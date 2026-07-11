import uuid
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    employee_id: uuid.UUID
    name: str
    role: str
    manager_id: Optional[uuid.UUID] = None
    skills: list[str] = []
    available_hours_per_week: float
    current_workload_hours: float
    is_active: bool
    hire_date: Optional[date] = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: uuid.UUID
    project_id: uuid.UUID
    name: str
    assigned_person_id: Optional[uuid.UUID] = None
    estimated_hours: float
    actual_hours_completed: float
    progress_percent: float
    start_date: Optional[date] = None
    deadline: Optional[date] = None
    priority: str
    status: str


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: uuid.UUID
    name: str
    description: str
    start_date: Optional[date] = None
    target_end_date: Optional[date] = None
    status: str


class WhatIfRequest(BaseModel):
    project_id: uuid.UUID
    reassign: list[dict] = []
    add_capacity: list[dict] = []


class DecisionValidationRequest(BaseModel):
    type: str
    affected_employee_ids: list[str] = []
    disruption_weeks: int = 4
    target_skill: Optional[str] = None


class ChatRequest(BaseModel):
    question: str
    context: dict = {}
