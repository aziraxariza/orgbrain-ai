"""FR-102: Calculate Employee Workload.

Deterministic, rules-based (ADR-002: deterministic first). Workload ratio drives
both risk detection (capacity violations) and the dashboard's workload views.
"""
import uuid

from sqlalchemy.orm import Session

from app.models.employee import Employee
from app.models.task import Task, TaskStatus


def calculate_employee_workload(db: Session, tenant_id: uuid.UUID) -> list[dict]:
    employees = db.query(Employee).filter(
        Employee.tenant_id == tenant_id, Employee.is_active.is_(True)
    ).all()

    results = []
    for e in employees:
        active_tasks = db.query(Task).filter(
            Task.tenant_id == tenant_id,
            Task.assigned_person_id == e.employee_id,
            Task.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]),
        ).all()

        # Remaining work = estimate minus what's already logged, floored at 0.
        remaining_hours = sum(max(t.estimated_hours - t.actual_hours_completed, 0.0) for t in active_tasks)
        utilization = remaining_hours / e.available_hours_per_week if e.available_hours_per_week else 0.0

        if utilization >= 1.2:
            band = "overloaded"
        elif utilization >= 0.9:
            band = "at_capacity"
        elif utilization >= 0.5:
            band = "healthy"
        else:
            band = "underutilized"

        results.append({
            "employee_id": str(e.employee_id),
            "name": e.name,
            "available_hours_per_week": e.available_hours_per_week,
            "remaining_committed_hours": round(remaining_hours, 1),
            "utilization_ratio": round(utilization, 2),
            "band": band,
            "active_task_count": len(active_tasks),
        })

    return sorted(results, key=lambda r: r["utilization_ratio"], reverse=True)
