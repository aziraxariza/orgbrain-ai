import uuid
import enum

from sqlalchemy import String, Float, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TenantMixin, TimestampMixin


class SimulationType(str, enum.Enum):
    MONTE_CARLO = "monte_carlo"
    WHAT_IF = "what_if"
    DECISION_VALIDATION = "decision_validation"


class SimulationRun(Base, TenantMixin, TimestampMixin):
    """Every simulation invocation is persisted so recommendations/explainability can
    reference exactly which run produced them (ADR-011: cache deterministic results)."""

    __tablename__ = "simulation_runs"

    simulation_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_type: Mapped[SimulationType] = mapped_column(SAEnum(SimulationType), nullable=False)
    input_parameters: Mapped[dict] = mapped_column(JSONB, default=dict)
    result_summary: Mapped[dict] = mapped_column(JSONB, default=dict)
    success_probability: Mapped[float | None] = mapped_column(Float, nullable=True)
    iterations: Mapped[int] = mapped_column(default=1000)
