import uuid

from sqlalchemy import String, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.mixins import TenantMixin, TimestampMixin


class Recommendation(Base, TenantMixin, TimestampMixin):
    """Structured recommendation + explainability payload (evidence, confidence,
    assumptions, alternatives) per Vision Doc section 4.3 / FR-601."""

    __tablename__ = "recommendations"

    recommendation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    simulation_run_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    title: Mapped[str] = mapped_column(String(500))
    action: Mapped[str] = mapped_column(String(2000))
    confidence: Mapped[float] = mapped_column(Float, default=0.0)  # 0-1
    evidence: Mapped[dict] = mapped_column(JSONB, default=dict)
    assumptions: Mapped[list] = mapped_column(JSONB, default=list)
    alternatives: Mapped[list] = mapped_column(JSONB, default=list)
    llm_explanation: Mapped[str | None] = mapped_column(String(4000), nullable=True)
