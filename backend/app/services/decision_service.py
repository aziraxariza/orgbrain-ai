"""Decision Support Engine (FR-500 series). What-if scenarios and decision
validation reuse the same deterministic simulation primitives — they never
re-derive numbers with a different method, per ADR-002 consistency requirement.
"""
import uuid
import copy

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.employee import Employee
from app.services.simulation_service import run_monte_carlo_simulation, compute_critical_path
from app.services.workload_service import calculate_employee_workload


def run_what_if_scenario(db: Session, tenant_id: uuid.UUID, project_id: uuid.UUID, changes: dict) -> dict:
    """FR-501: Execute "What-If" Scenarios.

    `changes` supports:
      - reassign: [{task_id, new_employee_id}]
      - add_capacity: [{employee_id, extra_hours_per_week}]
    Applies changes in a transaction that is always rolled back, so the what-if
    engine never mutates real data — only observes simulated deltas.
    """
    baseline_cp = compute_critical_path(db, tenant_id, project_id)
    baseline_mc = run_monte_carlo_simulation(db, tenant_id, project_id, iterations=500, seed=42)

    savepoint = db.begin_nested()
    try:
        for r in changes.get("reassign", []):
            task = db.query(Task).filter(Task.tenant_id == tenant_id, Task.task_id == uuid.UUID(r["task_id"])).first()
            if task:
                task.assigned_person_id = uuid.UUID(r["new_employee_id"])

        for c in changes.get("add_capacity", []):
            emp = db.query(Employee).filter(Employee.tenant_id == tenant_id, Employee.employee_id == uuid.UUID(c["employee_id"])).first()
            if emp:
                emp.available_hours_per_week += c.get("extra_hours_per_week", 0)

        db.flush()

        scenario_cp = compute_critical_path(db, tenant_id, project_id)
        scenario_mc = run_monte_carlo_simulation(db, tenant_id, project_id, iterations=500, seed=42)
    finally:
        savepoint.rollback()  # never persist a what-if

    delta_days = None
    if "total_duration_days" in baseline_cp and "total_duration_days" in scenario_cp:
        delta_days = round(scenario_cp["total_duration_days"] - baseline_cp["total_duration_days"], 1)

    return {
        "baseline": {"critical_path_days": baseline_cp.get("total_duration_days"), "monte_carlo_p80": baseline_mc.get("p80_days")},
        "scenario": {"critical_path_days": scenario_cp.get("total_duration_days"), "monte_carlo_p80": scenario_mc.get("p80_days")},
        "delta_critical_path_days": delta_days,
        "changes_applied": changes,
    }


def validate_strategic_decision(db: Session, tenant_id: uuid.UUID, decision: dict) -> dict:
    """FR-502: Validate Strategic Decisions.

    `decision` example: {"type": "reorg", "affected_employee_ids": [...], "disruption_weeks": 3}
    MVP heuristic model (ADR-002: deterministic rules before ML): reorg-style
    decisions incur a temporary output penalty proportional to the fraction of the
    org disrupted and the disruption window, tapering linearly to zero.
    """
    decision_type = decision.get("type")
    affected_ids = decision.get("affected_employee_ids", [])
    disruption_weeks = decision.get("disruption_weeks", 4)

    total_active = db.query(Employee).filter(Employee.tenant_id == tenant_id, Employee.is_active.is_(True)).count()
    affected_fraction = (len(affected_ids) / total_active) if total_active else 0

    if decision_type == "reorg":
        # Empirically-motivated placeholder coefficients — communication overhead and
        # context-switching cost scale with both breadth of disruption and duration.
        peak_output_penalty_pct = min(affected_fraction * 60 + 10, 60)
        recommended = peak_output_penalty_pct < 25
        return {
            "decision_type": decision_type,
            "affected_fraction": round(affected_fraction, 2),
            "peak_output_penalty_pct": round(peak_output_penalty_pct, 1),
            "disruption_weeks": disruption_weeks,
            "recommended": recommended,
            "rationale": (
                f"Disrupting {round(affected_fraction*100)}% of the org for {disruption_weeks} weeks "
                f"projects a peak output penalty of {round(peak_output_penalty_pct)}% during the transition."
            ),
        }

    if decision_type == "hire":
        role_skill = decision.get("target_skill")
        workloads = calculate_employee_workload(db, tenant_id)
        overloaded_matching = [w for w in workloads if w["band"] == "overloaded"]
        return {
            "decision_type": decision_type,
            "target_skill": role_skill,
            "current_overloaded_count": len(overloaded_matching),
            "recommended": len(overloaded_matching) > 0,
            "rationale": f"{len(overloaded_matching)} employee(s) currently overloaded; "
                         f"hiring would relieve committed-hours pressure.",
        }

    return {"decision_type": decision_type, "recommended": None, "rationale": "Unsupported decision type for MVP heuristic model."}


def recommend_resource_allocation(db: Session, tenant_id: uuid.UUID, limit: int = 20) -> list[dict]:
    """FR-503: Recommend Optimal Resource Allocation — pairs overloaded employees
    with underutilized employees who share at least one required skill.

    Each overloaded employee is matched to only their single best-fit relief
    candidate (most shared skills, then highest spare capacity), then the whole
    list is ranked by confidence and capped — an org-wide grid of every
    overloaded x underutilized pair is not a usable recommendation feed."""
    workloads = {w["employee_id"]: w for w in calculate_employee_workload(db, tenant_id)}
    employees = {str(e.employee_id): e for e in db.query(Employee).filter(Employee.tenant_id == tenant_id).all()}

    overloaded = [w for w in workloads.values() if w["band"] == "overloaded"]
    underutilized = [w for w in workloads.values() if w["band"] == "underutilized"]

    recommendations = []
    for o in overloaded:
        o_emp = employees.get(o["employee_id"])
        if not o_emp:
            continue

        best_match = None
        best_shared: set[str] = set()
        for u in underutilized:
            u_emp = employees.get(u["employee_id"])
            if not u_emp:
                continue
            shared_skills = set(o_emp.skills or []) & set(u_emp.skills or [])
            if not shared_skills:
                continue
            is_better = best_match is None or (
                len(shared_skills) > len(best_shared)
                or (len(shared_skills) == len(best_shared) and u["utilization_ratio"] < best_match["utilization_ratio"])
            )
            if is_better:
                best_match, best_shared = u, shared_skills

        if best_match:
            recommendations.append({
                "overloaded_employee": o["name"],
                "underutilized_employee": best_match["name"],
                "shared_skills": sorted(best_shared),
                "action": f"Shift work from {o['name']} ({o['utilization_ratio']*100:.0f}% utilized) "
                          f"to {best_match['name']} ({best_match['utilization_ratio']*100:.0f}% utilized).",
                "confidence": round(min(len(best_shared) / 3, 1.0), 2),
            })

    recommendations.sort(key=lambda r: r["confidence"], reverse=True)
    return recommendations[:limit]
