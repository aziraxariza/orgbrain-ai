import uuid
import enum

from sqlalchemy import String, Float, Date, ForeignKey, Enum as SAEnum, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TenantMixin, TimestampMixin


class TaskPriority(str, enum.Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    BLOCKED = "blocked"
    DONE = "done"


# Self-referential many-to-many: task.depends_on -> other tasks (FR-101/FR-201/FR-202)
task_dependencies = Table(
    "task_dependencies",
    Base.metadata,
    Column("task_id", UUID(as_uuid=True), ForeignKey("tasks.task_id"), primary_key=True),
    Column("depends_on_task_id", UUID(as_uuid=True), ForeignKey("tasks.task_id"), primary_key=True),
)


class Task(Base, TenantMixin, TimestampMixin):
    __tablename__ = "tasks"

    task_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    assigned_person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=True
    )
    estimated_hours: Mapped[float] = mapped_column(Float, default=0.0)
    actual_hours_completed: Mapped[float] = mapped_column(Float, default=0.0)
    progress_percent: Mapped[float] = mapped_column(Float, default=0.0)
    start_date: Mapped[Date] = mapped_column(Date, nullable=True)
    deadline: Mapped[Date] = mapped_column(Date, nullable=True)
    priority: Mapped[TaskPriority] = mapped_column(SAEnum(TaskPriority), default=TaskPriority.P2)
    status: Mapped[TaskStatus] = mapped_column(SAEnum(TaskStatus), default=TaskStatus.TODO)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("Employee", back_populates="tasks")

    depends_on = relationship(
        "Task",
        secondary=task_dependencies,
        primaryjoin=task_id == task_dependencies.c.task_id,
        secondaryjoin=task_id == task_dependencies.c.depends_on_task_id,
        backref="blocks",
    )
