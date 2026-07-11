from app.models.project import Project
from app.services.simulation_service import compute_critical_path, run_monte_carlo_simulation


def test_critical_path_is_computed_for_a_project(db, seeded_org):
    project = db.query(Project).filter(Project.tenant_id == seeded_org.organization_id).first()
    result = compute_critical_path(db, seeded_org.organization_id, project.project_id)
    assert "error" not in result
    assert result["total_duration_days"] >= 0
    assert isinstance(result["critical_path"], list)


def test_monte_carlo_percentiles_are_ordered(db, seeded_org):
    project = db.query(Project).filter(Project.tenant_id == seeded_org.organization_id).first()
    result = run_monte_carlo_simulation(db, seeded_org.organization_id, project.project_id, iterations=200, seed=1)
    assert "error" not in result
    assert result["min_days"] <= result["p50_days"] <= result["p80_days"] <= result["p95_days"] <= result["max_days"]


def test_monte_carlo_is_reproducible_with_same_seed(db, seeded_org):
    project = db.query(Project).filter(Project.tenant_id == seeded_org.organization_id).first()
    r1 = run_monte_carlo_simulation(db, seeded_org.organization_id, project.project_id, iterations=100, seed=7)
    r2 = run_monte_carlo_simulation(db, seeded_org.organization_id, project.project_id, iterations=100, seed=7)
    assert r1 == r2
