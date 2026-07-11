import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tenancy import get_current_user, CurrentUser
from app.services import simulation_service, prediction_service
from app.models.simulation import SimulationRun, SimulationType

router = APIRouter(prefix="/api/v1", tags=["simulation"])


@router.get("/projects/{project_id}/critical-path")
def critical_path(project_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return simulation_service.compute_critical_path(db, current_user.tenant_id, project_id)


@router.post("/tasks/{task_id}/simulate-delay")
def simulate_delay(task_id: uuid.UUID, delay_days: float, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """US-2.3: Identify Dependency Bottlenecks — propagate a hypothetical delay."""
    return simulation_service.simulate_delay_propagation(db, current_user.tenant_id, task_id, delay_days)


@router.post("/projects/{project_id}/monte-carlo")
def monte_carlo(project_id: uuid.UUID, iterations: int = 1000, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """FR-203. Persists the run per ADR-011 so repeated reads are cache-served rather than recomputed."""
    result = simulation_service.run_monte_carlo_simulation(db, current_user.tenant_id, project_id, iterations=iterations)
    run = SimulationRun(
        tenant_id=current_user.tenant_id,
        simulation_type=SimulationType.MONTE_CARLO,
        input_parameters={"project_id": str(project_id), "iterations": iterations},
        result_summary=result,
        success_probability=None,
        iterations=iterations,
    )
    db.add(run)
    db.commit()
    return {"simulation_run_id": str(run.simulation_run_id), **result}


@router.get("/capacity-violations")
def capacity_violations(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return simulation_service.detect_capacity_violations(db, current_user.tenant_id)


@router.get("/projects/{project_id}/prediction")
def project_prediction(project_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """US-2.2: Predict Project Delivery Success."""
    return prediction_service.predict_delivery_success(db, current_user.tenant_id, project_id)


@router.get("/projects/{project_id}/timeline-forecast")
def timeline_forecast(project_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return prediction_service.forecast_timeline_impacts(db, current_user.tenant_id, project_id)


@router.get("/workload-imbalances")
def workload_imbalances(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return prediction_service.predict_workload_imbalances(db, current_user.tenant_id)
