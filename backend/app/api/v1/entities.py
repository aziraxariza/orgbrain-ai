import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.tenancy import get_current_user, CurrentUser
from app.models.employee import Employee
from app.models.project import Project
from app.models.task import Task
from app.schemas.entities import EmployeeOut, ProjectOut, TaskOut
from app.services.workload_service import calculate_employee_workload

router = APIRouter(prefix="/api/v1", tags=["entities"])


@router.get("/employees", response_model=list[EmployeeOut])
def list_employees(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return db.query(Employee).filter(Employee.tenant_id == current_user.tenant_id).all()


@router.get("/employees/workload")
def get_workload(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """US-1.2: View Team Composition & Workload."""
    return calculate_employee_workload(db, current_user.tenant_id)


@router.get("/employees/{employee_id}", response_model=EmployeeOut)
def get_employee(employee_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    emp = db.query(Employee).filter(Employee.tenant_id == current_user.tenant_id, Employee.employee_id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return db.query(Project).filter(Project.tenant_id == current_user.tenant_id).all()


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(project_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    proj = db.query(Project).filter(Project.tenant_id == current_user.tenant_id, Project.project_id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return proj


@router.get("/projects/{project_id}/tasks", response_model=list[TaskOut])
def list_project_tasks(project_id: uuid.UUID, db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    """US-1.3: View Project Timeline & Dependencies."""
    return db.query(Task).filter(Task.tenant_id == current_user.tenant_id, Task.project_id == project_id).all()


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db), current_user: CurrentUser = Depends(get_current_user)):
    return db.query(Task).filter(Task.tenant_id == current_user.tenant_id).all()
