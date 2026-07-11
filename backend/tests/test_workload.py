from app.services.workload_service import calculate_employee_workload
from app.models.employee import Employee
from app.models.task import Task, TaskStatus, TaskPriority
from datetime import date, timedelta


def test_workload_bands_are_computed(db, seeded_org):
    results = calculate_employee_workload(db, seeded_org.organization_id)
    assert len(results) == 25
    for r in results:
        assert r["band"] in {"overloaded", "at_capacity", "healthy", "underutilized"}
        assert r["utilization_ratio"] >= 0


def test_overloaded_employee_ranks_above_underutilized(db, seeded_org):
    emp = db.query(Employee).filter(Employee.tenant_id == seeded_org.organization_id).first()
    proj = emp.tasks[0].project_id if emp.tasks else None

    # Force a controlled scenario: give one employee 10x their available hours in open tasks.
    emp.available_hours_per_week = 10
    other_tasks = db.query(Task).filter(Task.tenant_id == seeded_org.organization_id).limit(3).all()
    for t in other_tasks:
        t.assigned_person_id = emp.employee_id
        t.estimated_hours = 100
        t.actual_hours_completed = 0
        t.status = TaskStatus.IN_PROGRESS
    db.flush()

    results = calculate_employee_workload(db, seeded_org.organization_id)
    top = results[0]
    assert top["employee_id"] == str(emp.employee_id)
    assert top["band"] == "overloaded"
