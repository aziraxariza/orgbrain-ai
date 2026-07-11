import uuid

from sqlalchemy import String, Float, Boolean, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.mixins import TenantMixin, TimestampMixin


class Employee(Base, TenantMixin, TimestampMixin):
    """Matches SRS Appendix B Employees Table exactly."""

    __tablename__ = "employees"

    employee_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(255), nullable=False)
    manager_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=True
    )
    skills: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    available_hours_per_week: Mapped[float] = mapped_column(Float, default=40.0)
    current_workload_hours: Mapped[float] = mapped_column(Float, default=0.0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hire_date: Mapped[Date] = mapped_column(Date, nullable=True)

    organization = relationship("Organization", back_populates="employees")
    manager = relationship("Employee", remote_side=[employee_id], backref="direct_reports")
    tasks = relationship("Task", back_populates="assignee")
