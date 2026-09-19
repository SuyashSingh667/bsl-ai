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
    plant_id: Mapped[str] = mapped_column(String, default="bsl_bokaro", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    employee_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reporting_mode: Mapped[str] = mapped_column(String, default="personal")  # "personal" | "kiosk" | "supervisor_proxy"
    reporter_supervisor_id: Mapped[str | None] = mapped_column(String, nullable=True)
    worker_badge_id: Mapped[str | None] = mapped_column(String, nullable=True)
    kiosk_station_id: Mapped[str | None] = mapped_column(String, nullable=True)
    report_type: Mapped[str] = mapped_column(String)  # "suspected" | "emergency"

    # Phase 6: Anonymous no-blame reporting and closed-loop lifecycle tracking
    is_anonymous: Mapped[bool] = mapped_column(Boolean, default=False)
    shift: Mapped[str | None] = mapped_column(String, nullable=True)  # "Shift A", "Shift B", "Shift C", "General"
    anonymous_tracking_code: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    lifecycle_stage: Mapped[str] = mapped_column(String, default="received")  # "received" | "under_review" | "action_assigned" | "action_taken" | "resolved"
    corrective_action: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigned_to: Mapped[str | None] = mapped_column(String, nullable=True)
    due_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closure_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    closure_evidence_path: Mapped[str | None] = mapped_column(String, nullable=True)
    closure_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

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


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=_uuid)
    plant_id: Mapped[str] = mapped_column(String, default="bsl_bokaro", index=True)
    ticket_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    actor_id: Mapped[str] = mapped_column(String, default="SYSTEM")
    actor_role: Mapped[str] = mapped_column(String, default="system")  # "worker" | "supervisor" | "safety_officer" | "control_room" | "admin"
    action: Mapped[str] = mapped_column(String, index=True)
    previous_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_state: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, index=True)
    prev_entry_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    entry_hash: Mapped[str] = mapped_column(String, index=True)

