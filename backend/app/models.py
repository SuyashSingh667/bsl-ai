import uuid
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return uuid.uuid4().hex[:12]


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    employee_id: Mapped[str | None] = mapped_column(String, nullable=True)
    report_type: Mapped[str] = mapped_column(String)  # "suspected" | "emergency"

    incident_description: Mapped[str] = mapped_column(Text)
    incident_description_en: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String, default="en")
    language_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    photo_proof_path: Mapped[str | None] = mapped_column(String, nullable=True)
    media_type: Mapped[str | None] = mapped_column(String, nullable=True)  # "image" | "video"
    requires_photo_proof: Mapped[bool] = mapped_column(Boolean, default=False)
    zone_id: Mapped[str | None] = mapped_column(String, nullable=True)

    predicted_category: Mapped[str | None] = mapped_column(String, nullable=True)
    category_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    extracted_entities: Mapped[dict] = mapped_column(JSON, default=dict)

    verification_questions: Mapped[list] = mapped_column(JSON, default=list)
    verification_answers: Mapped[list] = mapped_column(JSON, default=list)
    verification_answers_en: Mapped[list] = mapped_column(JSON, default=list)
    verification_status: Mapped[str] = mapped_column(String, default="pending")
    verification_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    structured_findings: Mapped[dict] = mapped_column(JSON, default=dict)
    safety_report: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    routing_tier: Mapped[str | None] = mapped_column(String, nullable=True)

    impact_assessment: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    guidance_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    guidance_text_native: Mapped[str | None] = mapped_column(Text, nullable=True)
    guidance_sources: Mapped[list] = mapped_column(JSON, default=list)
    guidance_audio_path: Mapped[str | None] = mapped_column(String, nullable=True)
    precautionary_measures: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    visual_analysis: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String, default="open")
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    flagged_for_human_review: Mapped[bool] = mapped_column(Boolean, default=False)
    review_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    sop_gap_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    ai_audit_trail: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    model_versions: Mapped[dict] = mapped_column(JSON, default=dict)
