"""Prediction & Forecasting Engine (FR-400 series). Combines the deterministic
critical path with the Monte Carlo distribution and current risk load into a
single success-probability figure. Still no ML/LLM — pure arithmetic over
already-computed deterministic + probabilistic outputs (ADR-002)."""
import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.models.project import Project
from app.services.simulation_service import run_monte_carlo_simulation, compute_critical_path
from app.services.risk_service import rank_risks


def predict_delivery_success(db: Session, tenant_id: uuid.UUID, project_id: uuid.UUID) -> dict:
    """FR-401: Predict Project Delivery Success Probability."""
    project = db.query(Project).filter(Project.tenant_id == tenant_id, Project.project_id == project_id).first()
    if not project:
        return {"error": "project_not_found"}

    mc = run_monte_carlo_simulation(db, tenant_id, project_id, iterations=1000)
    if "error" in mc:
        return mc

    if project.target_end_date and project.start_date:
        days_available = (project.target_end_date - date.today()).days
    else:
        days_available = None

    if days_available is None:
        # No target date set — report the distribution without a probability figure.
        return {"project_id": str(project_id), "monte_carlo": mc, "success_probability": None,
                "note": "Set project.target_end_date to compute a success probability."}

    # Fraction of simulated completion times that land within the remaining runway.
    # Re-derive from percentiles as a cheap approximation rather than re-running raw samples.
    if days_available >= mc["p95_days"]:
        probability = 0.95
    elif days_available >= mc["p80_days"]:
        probability = 0.80
    elif days_available >= mc["p50_days"]:
        probability = 0.50
    elif days_available >= mc["min_days"]:
        probability = 0.20
    else:
        probability = 0.05

    project_risks = [r for r in rank_risks(db, tenant_id) if r.get("project_id") == project_id]
    risk_penalty = min(len(project_risks) * 0.03, 0.25)
    probability = max(probability - risk_penalty, 0.02)

    return {
        "project_id": str(project_id),
        "days_available": days_available,
        "monte_carlo": mc,
        "active_project_risks": len(project_risks),
        "success_probability": round(probability, 2),
    }


def forecast_timeline_impacts(db: Session, tenant_id: uuid.UUID, project_id: uuid.UUID) -> dict:
    """FR-402: Forecast Timeline Impacts — critical path plus buffer analysis."""
    cp = compute_critical_path(db, tenant_id, project_id)
    if "error" in cp:
        return cp

    project = db.query(Project).filter(Project.tenant_id == tenant_id, Project.project_id == project_id).first()
    forecast_end = None
    if project and project.start_date:
        from datetime import timedelta
        forecast_end = project.start_date + timedelta(days=cp["total_duration_days"])

    buffer_days = None
    if project and project.target_end_date and forecast_end:
        buffer_days = (project.target_end_date - forecast_end).days

    return {
        "critical_path": cp["critical_path"],
        "forecast_duration_days": cp["total_duration_days"],
        "forecast_end_date": forecast_end.isoformat() if forecast_end else None,
        "target_end_date": project.target_end_date.isoformat() if project and project.target_end_date else None,
        "buffer_days": buffer_days,
        "at_risk": buffer_days is not None and buffer_days < 0,
    }


def predict_workload_imbalances(db: Session, tenant_id: uuid.UUID) -> dict:
    """FR-403: Predict Workload Imbalances — near-term view of who trends toward
    overload vs underutilization based on current committed work."""
    from app.services.workload_service import calculate_employee_workload

    workloads = calculate_employee_workload(db, tenant_id)
    overloaded = [w for w in workloads if w["band"] == "overloaded"]
    underutilized = [w for w in workloads if w["band"] == "underutilized"]

    return {
        "overloaded_count": len(overloaded),
        "underutilized_count": len(underutilized),
        "overloaded": overloaded[:10],
        "underutilized": underutilized[:10],
        "org_avg_utilization": round(sum(w["utilization_ratio"] for w in workloads) / len(workloads), 2) if workloads else 0,
    }
