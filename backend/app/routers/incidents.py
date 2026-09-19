import re
import shutil
import uuid

from pathlib import Path
from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.config import AUDIO_UPLOAD_DIR, CATEGORIES_REQUIRING_PHOTO, PHOTO_UPLOAD_DIR
from app.database import get_db
from app.models import Ticket
from app.schemas import IncidentCreate, TicketOut
from app.services import (
    classifier,
    entity_extraction,
    precautionary_measures,
    report_generator,
    routing,
    spatial_impact,
    transcription,
    translation,
)

router = APIRouter(prefix="/incidents", tags=["incidents"])

AUDIO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
PHOTO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

SUPPORTED_LANGUAGES = {"hi", "bn", "ta", "te", "mr", "gu", "kn", "ml", "pa", "or", "en"}

_HINGLISH_REGEX = re.compile(
    r"\b(ho|raha|rahi|rahe|hai|hain|kare|karna|hoga|hua|aag|laga|lagi|korei|hori|pani|dhua|bijli|kripya|jaldi|dekho|aaya|gaya|kuch|bahut|thoda|andar|bahar|band|chalu|bolo|bol|madad|chahiye|phat|nikal|admi|gir|pada|ahe|nahi|lag gayi|aag lagi)\b",
    re.IGNORECASE,
)


def detect_language_from_text(text: str) -> str:
    script_counts = {
        "bn": sum(1 for c in text if "\u0980" <= c <= "\u09ff"),  # Bengali / Assamese
        "ta": sum(1 for c in text if "\u0b80" <= c <= "\u0bff"),  # Tamil
        "te": sum(1 for c in text if "\u0c00" <= c <= "\u0c7f"),  # Telugu
        "hi": sum(1 for c in text if "\u0900" <= c <= "\u097f"),  # Devanagari (Hindi / Marathi)
        "gu": sum(1 for c in text if "\u0a80" <= c <= "\u0aff"),  # Gujarati
        "kn": sum(1 for c in text if "\u0c80" <= c <= "\u0cff"),  # Kannada
        "ml": sum(1 for c in text if "\u0d00" <= c <= "\u0d7f"),  # Malayalam
        "pa": sum(1 for c in text if "\u0a00" <= c <= "\u0a7f"),  # Punjabi (Gurmukhi)
        "or": sum(1 for c in text if "\u0b00" <= c <= "\u0b7f"),  # Odia
    }
    max_lang, count = max(script_counts.items(), key=lambda x: x[1])
    if count > 0:
        # Differentiate Marathi vs Hindi in Devanagari
        if max_lang == "hi":
            marathi_markers = ["आहे", "नाही", "झाले", "झाला", "गळती", "येथे", "पाहिले", "होते", "केले", "आहेत", "ळ"]
            if any(m in text for m in marathi_markers):
                return "mr"
        return max_lang

    # Check for Latin-script Hindi / Hinglish phonetics
    if _HINGLISH_REGEX.search(text):
        return "hi"

    return "en"


def _create_ticket(
    db: Session,
    report_type: str,
    text: str,
    language: str | None = None,
    employee_id: str | None = None,
    zone_id: str | None = None,
    audio_path: str | None = None,
    language_confidence: float | None = None,
    text_en: str | None = None,
    photo_proof_path: str | None = None,
) -> Ticket:
    detected_from_text = detect_language_from_text(text)
    effective_lang = language or detected_from_text
    if effective_lang not in SUPPORTED_LANGUAGES:
        effective_lang = detected_from_text if detected_from_text in SUPPORTED_LANGUAGES else "hi"
    if (not language or language in ["auto", "en"]) and detected_from_text != "en":
        effective_lang = detected_from_text
        if language_confidence is None:
            language_confidence = 0.99

    if not text_en:
        text_en = translation.to_english(text, effective_lang)

    category, confidence = classifier.classify(text_en, "en", raw_text=text)
    entities = entity_extraction.extract(text_en, stated_zone_id=zone_id)
    effective_zone = zone_id or entities.get("mentioned_zone")

    # Photo or video upload is compulsory in necessary cases (critical physical hazards or emergencies)
    requires_photo = (category in CATEGORIES_REQUIRING_PHOTO) or (report_type == "emergency")

    media_type = None
    if photo_proof_path:
        ext = Path(photo_proof_path).suffix.lower()
        media_type = "video" if ext in [".mp4", ".webm", ".mov", ".mkv", ".avi"] else "image"

    ticket = Ticket(
        employee_id=employee_id,
        report_type=report_type,
        incident_description=text,
        incident_description_en=text_en,
        language=effective_lang,
        language_confidence=language_confidence,
        audio_path=audio_path,
        photo_proof_path=photo_proof_path,
        media_type=media_type,
        requires_photo_proof=requires_photo,
        zone_id=effective_zone,
        predicted_category=category,
        category_confidence=confidence,
        extracted_entities=entities,
        model_versions={
            "classifier": "semantic-hybrid-v1",
            "entity_extraction": "regex+semantic-zone-v1",
            "translation": "whisper-direct-translate+opus-mt",
        },
    )

    impact = spatial_impact.assess(effective_zone, category)
    if impact:
        ticket.impact_assessment = impact

    if report_type == "emergency":
        ticket.verification_status = "emergency_bypass"
        ticket.risk_score = routing.compute_risk_score(category, verification_score=1.0, impact=impact)
        ticket.routing_tier = "emergency_authority"
        ticket.status = "escalated"
        try:
            ticket.precautionary_measures = precautionary_measures.generate_precautionary_measures(ticket)
        except Exception:
            pass
        # Synthesize initial emergency incident report with dispatch recipients
        try:
            findings = {
                "observation_mode": "visual_confirmed",
                "is_hazard_active": True,
                "confirmed_equipment": [entities.get("equipment")] if entities.get("equipment") else [],
                "reported_symptoms": [],
                "people_exposed_count": None,
                "total_evidence_score": 1.0,
            }
            photo_url = f"/photos/{Path(ticket.photo_proof_path).name}" if ticket.photo_proof_path else None
            rep = report_generator.generate_incident_report(
                ticket_id=ticket.id,
                category=category or "fire",
                category_confidence=confidence,
                zone_id=effective_zone,
                initial_statement=text,
                initial_statement_en=text_en,
                findings=findings,
                impact=impact,
                routing_tier="emergency_authority",
                risk_score=ticket.risk_score,
                photo_url=photo_url,
                report_type="emergency",
            )
            ticket.safety_report = rep
            ticket.guidance_text = rep["report_markdown"]
            ticket.guidance_sources = rep["sources"]
        except Exception:
            pass

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    if ticket.photo_proof_path:
        url = f"/photos/{Path(ticket.photo_proof_path).name}"
        ticket.photo_url = url
        ticket.media_url = url
    return ticket


@router.post("", response_model=TicketOut)
def create_incident(payload: IncidentCreate, db: Session = Depends(get_db)):
    return _create_ticket(
        db,
        report_type=payload.report_type,
        text=payload.incident_description,
        language=payload.language,
        employee_id=payload.employee_id,
        zone_id=payload.zone_id,
    )


@router.post("/audio", response_model=TicketOut)
def create_incident_from_audio(
    report_type: str = Form(pattern="^(suspected|emergency)$"),
    file: UploadFile = None,
    photo: UploadFile | None = File(None),
    employee_id: str | None = Form(None),
    zone_id: str | None = Form(None),
    language: str | None = Form(None),
    db: Session = Depends(get_db),
):
    dest = AUDIO_UPLOAD_DIR / f"{uuid.uuid4().hex[:12]}_{file.filename}"
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    photo_path = None
    if photo and photo.filename:
        photo_dest = PHOTO_UPLOAD_DIR / f"{uuid.uuid4().hex[:12]}_{photo.filename}"
        with open(photo_dest, "wb") as out:
            shutil.copyfileobj(photo.file, out)
        photo_path = str(photo_dest)

    # Universal transcription + automatic language detection + English translation
    lang_hint = language if (language and language not in ["auto", "null", "undefined"]) else None
    native_text, text_en, detected_lang, language_confidence = transcription.transcribe_and_translate(
        str(dest), language=lang_hint
    )
    effective_lang = lang_hint or detected_lang

    script_lang = detect_language_from_text(native_text)
    if script_lang != "en":
        effective_lang = script_lang
    elif effective_lang not in SUPPORTED_LANGUAGES:
        effective_lang = "hi"

    return _create_ticket(
        db,
        report_type=report_type,
        text=native_text,
        text_en=text_en,
        language=effective_lang,
        employee_id=employee_id,
        zone_id=zone_id,
        audio_path=str(dest),
        photo_proof_path=photo_path,
        language_confidence=language_confidence,
    )

