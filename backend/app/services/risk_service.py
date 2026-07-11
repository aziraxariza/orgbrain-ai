"""Risk Detection Engine (FR-300 series). Heuristic rules per PRD Feature Matrix
(ML anomaly detection is explicitly Post-MVP). Every risk carries evidence so the
explainability layer never has to invent a justification.
"""
import uuid
from datetime import date

import networkx as nx
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.risk import RiskEvent, RiskType, RiskSeverity
from app.services.graph_service import build_org_graph
from app.services.workload_service import calculate_employee_workload


def _severity_from_score(score: float) -> RiskSeverity:
    if score >= 85:
        return RiskSeverity.CRITICAL
    if score >= 65:
        return RiskSeverity.HIGH
    if score >= 35:
        return RiskSeverity.MEDIUM
    return RiskSeverity.LOW


def detect_execution_drift(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    """FR-301: Detect Execution Drift — tasks whose progress is materially behind
    what elapsed time against the deadline implies."""
    today = date.today()
    tasks = db.query(Task).filter(
        Task.tenant_id == tenant_id,
        Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS]),
        Task.deadline.isnot(None),
        Task.start_date.isnot(None),
    ).all()

    findings = []
    for t in tasks:
        total_span = (t.deadline - t.start_date).days
        if total_span <= 0:
            continue
        elapsed = (today - t.start_date).days
        expected_progress = min(max(elapsed / total_span, 0.0), 1.0) * 100
        drift = expected_progress - t.progress_percent

        if drift > 15:
            score = min(drift * 1.2, 100)
            findings.append({
                "risk_type": RiskType.EXECUTION_DRIFT,
                "severity": _severity_from_score(score),
                "severity_score": round(score, 1),
                "task_id": t.task_id,
                "project_id": t.project_id,
                "employee_id": t.assigned_person_id,
                "description": f"'{t.name}' is {round(drift)}pts behind expected progress "
                                f"({round(t.progress_percent)}% actual vs {round(expected_progress)}% expected).",
                "evidence": {
                    "expected_progress_pct": round(expected_progress, 1),
                    "actual_progress_pct": t.progress_percent,
                    "days_elapsed": elapsed,
                    "total_span_days": total_span,
                },
            })
    return findings


def identify_bottlenecks(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    """FR-302: Identify Bottleneck Tasks and People — nodes with unusually high
    betweenness centrality in the task/employee graph, i.e. a lot of execution
    routes through them."""
    g = build_org_graph(db, tenant_id)
    if g.number_of_nodes() < 3:
        return []

    centrality = nx.betweenness_centrality(g)
    if not centrality:
        return []

    max_c = max(centrality.values()) or 1.0
    findings = []
    for node, c in centrality.items():
        norm = c / max_c
        if norm < 0.6:
            continue
        node_type, node_id = node.split(":", 1)
        score = round(norm * 100, 1)
        findings.append({
            "risk_type": RiskType.BOTTLENECK,
            "severity": _severity_from_score(score),
            "severity_score": score,
            "task_id": uuid.UUID(node_id) if node_type == "task" else None,
            "employee_id": uuid.UUID(node_id) if node_type == "employee" else None,
            "project_id": None,
            "description": f"{g.nodes[node].get('name', node_id)} ({node_type}) sits on an unusually "
                            f"high share of execution paths — a single point of failure.",
            "evidence": {"betweenness_centrality": round(c, 4), "normalized_score": round(norm, 3)},
        })
    return findings


def flag_dependency_concentration(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    """FR-303: Flag Dependency Concentration Risk — a single employee assigned to
    an outsized share of tasks that many other tasks depend on."""
    tasks = db.query(Task).filter(Task.tenant_id == tenant_id).all()
    blocking_counts: dict[uuid.UUID, int] = {}

    for t in tasks:
        if t.assigned_person_id is None:
            continue
        blocking_counts[t.assigned_person_id] = blocking_counts.get(t.assigned_person_id, 0) + len(t.blocks)

    if not blocking_counts:
        return []

    max_count = max(blocking_counts.values()) or 1
    findings = []
    for employee_id, count in blocking_counts.items():
        if count == 0:
            continue
        norm = count / max_count
        if norm < 0.5:
            continue
        score = round(norm * 100, 1)
        findings.append({
            "risk_type": RiskType.DEPENDENCY_CONCENTRATION,
            "severity": _severity_from_score(score),
            "severity_score": score,
            "employee_id": employee_id,
            "task_id": None,
            "project_id": None,
            "description": f"Employee is assigned to tasks that block {count} downstream task(s) — "
                            f"their absence would cascade widely.",
            "evidence": {"downstream_blocked_task_count": count},
        })
    return findings


def rank_risks(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    """FR-304: Rank Risks by Severity and Immediacy. Runs all detectors and returns
    a single sorted feed — this is what the dashboard's Risks page and the
    /risks endpoint serve."""
    all_findings = (
        detect_execution_drift(db, tenant_id)
        + identify_bottlenecks(db, tenant_id)
        + flag_dependency_concentration(db, tenant_id)
    )

    capacity_violations = _capacity_violation_findings(db, tenant_id)
    all_findings.extend(capacity_violations)

    return sorted(all_findings, key=lambda f: f["severity_score"], reverse=True)


def _capacity_violation_findings(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    overloaded = [w for w in calculate_employee_workload(db, tenant_id) if w["utilization_ratio"] >= 1.0]
    findings = []
    for w in overloaded:
        score = min((w["utilization_ratio"] - 1.0) * 200 + 50, 100)
        findings.append({
            "risk_type": RiskType.CAPACITY_VIOLATION,
            "severity": _severity_from_score(score),
            "severity_score": round(score, 1),
            "employee_id": uuid.UUID(w["employee_id"]),
            "task_id": None,
            "project_id": None,
            "description": f"{w['name']} is committed to {w['utilization_ratio']*100:.0f}% of available "
                            f"capacity ({w['remaining_committed_hours']}h remaining vs "
                            f"{w['available_hours_per_week']}h/week available).",
            "evidence": w,
        })
    return findings


def persist_risk_findings(db: Session, tenant_id: uuid.UUID, findings: list[dict]) -> list[RiskEvent]:
    events = []
    for f in findings:
        event = RiskEvent(tenant_id=tenant_id, **f)
        db.add(event)
        events.append(event)
    db.commit()
    return events
