import uuid
import enum

from sqlalchemy import String, Float, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TenantMixin, TimestampMixin


class RiskType(str, enum.Enum):
    EXECUTION_DRIFT = "execution_drift"
    BOTTLENECK = "bottleneck"
    DEPENDENCY_CONCENTRATION = "dependency_concentration"
    CAPACITY_VIOLATION = "capacity_violation"


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RiskEvent(Base, TenantMixin, TimestampMixin):
    """Output of the deterministic Risk Detection Engine (FR-301..304)."""

    __tablename__ = "risk_events"

    risk_event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_type: Mapped[RiskType] = mapped_column(SAEnum(RiskType), nullable=False)
    severity: Mapped[RiskSeverity] = mapped_column(SAEnum(RiskSeverity), nullable=False)
    severity_score: Mapped[float] = mapped_column(Float, default=0.0)  # 0-100, drives ranking (FR-304)
    project_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    task_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    employee_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("employees.employee_id"), nullable=True)
    description: Mapped[str] = mapped_column(String(1000))
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)  # supporting numbers for explainability
    is_resolved: Mapped[bool] = mapped_column(default=False)
