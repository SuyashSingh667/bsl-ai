from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IncidentCreate(BaseModel):
    plant_id: str = "bsl_bokaro"
    report_type: str = Field(pattern="^(suspected|emergency)$")
    incident_description: str
    employee_id: str | None = None
    reporting_mode: str = "personal"
    reporter_supervisor_id: str | None = None
    worker_badge_id: str | None = None
    kiosk_station_id: str | None = None
    zone_id: str | None = None
    language: str = "en"


class AnswerSubmit(BaseModel):
    answer_text: str
    answer_text_en: str | None = None
    question_text: str | None = None



class TicketUpdate(BaseModel):
    status: str | None = None
    resolution_notes: str | None = None
    routing_tier: str | None = None
    language: str | None = None


class TicketOut(BaseModel):
    id: str
    plant_id: str = "bsl_bokaro"
    created_at: datetime
    updated_at: datetime
    employee_id: str | None
    reporting_mode: str = "personal"
    reporter_supervisor_id: str | None = None
    worker_badge_id: str | None = None
    kiosk_station_id: str | None = None
    report_type: str
    incident_description: str
    incident_description_en: str
    language: str
    language_confidence: float | None
    audio_path: str | None
    photo_proof_path: str | None = None
    photo_url: str | None = None
    media_type: str | None = None
    media_url: str | None = None
    requires_photo_proof: bool = False
    zone_id: str | None
    predicted_category: str | None
    category_confidence: float | None
    extracted_entities: dict[str, Any] | None = Field(default_factory=dict)
    verification_questions: list[str] | None = Field(default_factory=list)
    verification_answers: list[str] | None = Field(default_factory=list)
    verification_answers_en: list[str] | None = Field(default_factory=list)
    verification_status: str = "pending"
    verification_score: float | None = None
    structured_findings: dict[str, Any] | None = Field(default_factory=dict)
    safety_report: dict[str, Any] | None = None
    risk_score: float | None = None
    routing_tier: str | None = None
    impact_assessment: dict[str, Any] | None = None
    guidance_text: str | None = None
    guidance_text_native: str | None = None
    guidance_sources: list[dict[str, Any]] | None = Field(default_factory=list)
    guidance_audio_path: str | None = None
    precautionary_measures: dict[str, Any] | None = None
    visual_analysis: dict[str, Any] | None = None
    status: str = "open"
    resolution_notes: str | None = None
    flagged_for_human_review: bool = False
    review_reason: str | None = None
    sop_gap_detected: bool = False
    ai_audit_trail: dict[str, Any] | None = None
    model_versions: dict[str, Any] | None = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class PrecautionaryMeasureItem(BaseModel):
    id: str
    icon: str
    title: str
    title_native: str
    text: str
    text_native: str
    checklist_label: str
    checklist_label_native: str


class PrecautionaryMeasuresOut(BaseModel):
    category: str
    sop_source: str
    sop_code: str
    prompt_question: str
    prompt_question_native: str
    spoken_summary_en: str
    spoken_summary_native: str
    audio_path: str | None = None
    measures: list[PrecautionaryMeasureItem]


class NextQuestionOut(BaseModel):
    done: bool
    question: str | None = None
    question_index: int | None = None
    total_questions: int | None = None
    question_audio_path: str | None = None
    options: list[str] = Field(default_factory=list)
    sop_source: str | None = None
    is_personalized: bool = False


class TTSRequest(BaseModel):
    text: str
    language: str = "en"


class TTSResponse(BaseModel):
    audio_path: str


class AuditLogOut(BaseModel):
    id: str
    plant_id: str
    ticket_id: str | None = None
    actor_id: str
    actor_role: str
    action: str
    previous_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    prev_entry_hash: str | None = None
    entry_hash: str

    model_config = {"from_attributes": True}


class PlantZoneDefinition(BaseModel):
    zone_id: str
    name: str
    category: str
    hazard_class: list[str] = Field(default_factory=list)
    footprint_radius_m: float = 80.0
    occupancy: dict[str, int] | None = None
    centroid: dict[str, float] = Field(default_factory=lambda: {"x": 0.0, "y": 0.0})
    phone_restricted: bool = False
    intrinsically_safe_only: bool = False
    safe_alternative: str | None = None


class EmergencyTeamDefinition(BaseModel):
    team_id: str
    name: str
    phone: str
    sms: str | None = None
    whatsapp: str | None = None
    radio_channel: str | None = None
    coverage_zones: list[str] = Field(default_factory=lambda: ["ALL"])

