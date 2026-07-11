from app.services.risk_service import rank_risks, detect_execution_drift, _capacity_violation_findings
from app.models.employee import Employee
from app.models.task import Task, TaskStatus


def test_rank_risks_returns_sorted_by_severity(db, seeded_org):
    findings = rank_risks(db, seeded_org.organization_id)
    scores = [f["severity_score"] for f in findings]
    assert scores == sorted(scores, reverse=True)


def test_capacity_violation_detected_for_overloaded_employee(db, seeded_org):
    emp = db.query(Employee).filter(Employee.tenant_id == seeded_org.organization_id).first()
    emp.available_hours_per_week = 5
    tasks = db.query(Task).filter(Task.tenant_id == seeded_org.organization_id).limit(2).all()
    for t in tasks:
        t.assigned_person_id = emp.employee_id
        t.estimated_hours = 200
        t.actual_hours_completed = 0
        t.status = TaskStatus.IN_PROGRESS
    db.flush()

    findings = _capacity_violation_findings(db, seeded_org.organization_id)
    assert any(f["employee_id"] == emp.employee_id for f in findings)


def test_execution_drift_returns_valid_severity(db, seeded_org):
    findings = detect_execution_drift(db, seeded_org.organization_id)
    for f in findings:
        assert 0 <= f["severity_score"] <= 100
