"""Execution Simulation Engine (FR-200 series).

ADR-002: deterministic algorithms first, Monte Carlo second, LLM never touches
these numbers — it only explains them (see explainability_service.py).
"""
import uuid
import random
from datetime import date, timedelta

import networkx as nx
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.employee import Employee


def _task_subgraph(db: Session, tenant_id: uuid.UUID, project_id: uuid.UUID | None = None) -> nx.DiGraph:
    q = db.query(Task).filter(Task.tenant_id == tenant_id)
    if project_id:
        q = q.filter(Task.project_id == project_id)
    tasks = q.all()

    g = nx.DiGraph()
    for t in tasks:
        duration_days = max((t.estimated_hours - t.actual_hours_completed) / 8.0, 0.0)
        g.add_node(str(t.task_id), duration=duration_days, name=t.name, status=t.status.value)
    for t in tasks:
        for dep in t.depends_on:
            if str(dep.task_id) in g.nodes:
                g.add_edge(str(dep.task_id), str(t.task_id))
    return g


def compute_critical_path(db: Session, tenant_id: uuid.UUID, project_id: uuid.UUID) -> dict:
    """FR-201: Compute Critical Path. Longest-duration path through the dependency
    DAG determines the earliest possible project completion."""
    g = _task_subgraph(db, tenant_id, project_id)

    if not nx.is_directed_acyclic_graph(g):
        cycle = next(iter(nx.simple_cycles(g)), [])
        return {"error": "dependency_cycle_detected", "cycle": cycle}

    if g.number_of_nodes() == 0:
        return {"critical_path": [], "total_duration_days": 0.0}

    # Longest path by duration using DAG longest-path algorithm on a weighted graph.
    for u, v in g.edges():
        g[u][v]["weight"] = g.nodes[u]["duration"]

    longest_path = nx.dag_longest_path(g, weight="weight")
    total_duration = sum(g.nodes[n]["duration"] for n in longest_path)

    return {
        "critical_path": [{"task_id": n, "name": g.nodes[n]["name"], "duration_days": round(g.nodes[n]["duration"], 1)} for n in longest_path],
        "total_duration_days": round(total_duration, 1),
    }


def simulate_delay_propagation(db: Session, tenant_id: uuid.UUID, task_id: uuid.UUID, delay_days: float) -> dict:
    """FR-202: Simulate Task Delay Propagation. Pushes a delay downstream through
    depends_on edges and reports every task/project whose timeline shifts."""
    g = _task_subgraph(db, tenant_id)
    task_key = str(task_id)
    if task_key not in g.nodes:
        return {"error": "task_not_found"}

    affected = nx.descendants(g, task_key)
    affected_tasks = db.query(Task).filter(Task.tenant_id == tenant_id, Task.task_id.in_([uuid.UUID(a) for a in affected])).all()

    impact = []
    for t in affected_tasks:
        new_deadline = (t.deadline + timedelta(days=delay_days)) if t.deadline else None
        impact.append({
            "task_id": str(t.task_id),
            "name": t.name,
            "original_deadline": t.deadline.isoformat() if t.deadline else None,
            "projected_deadline": new_deadline.isoformat() if new_deadline else None,
        })

    return {
        "source_task_id": task_key,
        "delay_days": delay_days,
        "downstream_tasks_affected": len(impact),
        "impact": impact,
    }


def detect_capacity_violations(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    """FR-204: Detect Capacity Constraint Violations — employees whose committed
    remaining work exceeds available hours for the current period."""
    from app.services.workload_service import calculate_employee_workload

    workloads = calculate_employee_workload(db, tenant_id)
    return [w for w in workloads if w["utilization_ratio"] >= 1.0]


def run_monte_carlo_simulation(
    db: Session, tenant_id: uuid.UUID, project_id: uuid.UUID, iterations: int = 1000,
    variance_pct: float = 0.25, seed: int | None = None,
) -> dict:
    """FR-203: Run Monte Carlo Simulation. Each task duration is resampled from a
    triangular distribution (min = -variance, mode = estimate, max = +variance) per
    iteration; the critical path is recomputed each time to build a distribution of
    project completion times. This is the statistical layer referenced in ADR-002 —
    used only when deterministic critical path alone can't express uncertainty.
    """
    rng = random.Random(seed)
    base_g = _task_subgraph(db, tenant_id, project_id)

    if base_g.number_of_nodes() == 0 or not nx.is_directed_acyclic_graph(base_g):
        return {"error": "no_valid_task_graph"}

    completion_days = []
    for _ in range(iterations):
        sim_g = base_g.copy()
        for n in sim_g.nodes:
            base_duration = sim_g.nodes[n]["duration"]
            low = max(base_duration * (1 - variance_pct), 0.0)
            high = base_duration * (1 + variance_pct)
            mode = base_duration
            sim_g.nodes[n]["duration"] = rng.triangular(low, high, mode) if high > low else base_duration
        for u, v in sim_g.edges():
            sim_g[u][v]["weight"] = sim_g.nodes[u]["duration"]

        if sim_g.number_of_edges() > 0:
            path = nx.dag_longest_path(sim_g, weight="weight")
        else:
            path = list(sim_g.nodes)
        completion_days.append(sum(sim_g.nodes[n]["duration"] for n in path))

    completion_days.sort()
    n = len(completion_days)
    p50 = completion_days[int(n * 0.5)]
    p80 = completion_days[min(int(n * 0.8), n - 1)]
    p95 = completion_days[min(int(n * 0.95), n - 1)]
    mean = sum(completion_days) / n

    return {
        "iterations": iterations,
        "mean_days": round(mean, 1),
        "p50_days": round(p50, 1),
        "p80_days": round(p80, 1),
        "p95_days": round(p95, 1),
        "min_days": round(completion_days[0], 1),
        "max_days": round(completion_days[-1], 1),
    }
