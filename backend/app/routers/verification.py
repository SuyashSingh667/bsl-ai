from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app.schemas import AnswerSubmit, NextQuestionOut, TicketOut
from app.services import (
    answer_classifier,
    precautionary_measures,
    report_generator,
    routing,
    spatial_impact,
    translation,
    tts,
    verification_engine,
)

router = APIRouter(prefix="/verification", tags=["verification"])


def _get_ticket(ticket_id: str, db: Session) -> Ticket:
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "ticket not found")
    if not ticket.predicted_category:
        raise HTTPException(400, "incident category could not be determined; no verification questions available")
    return ticket


@router.get("/{ticket_id}/next-question", response_model=NextQuestionOut)
def next_question(ticket_id: str, lang: str | None = None, db: Session = Depends(get_db)):
    ticket = _get_ticket(ticket_id, db)
    if lang:
        ticket.language = lang
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
    interview_lang = ticket.language or "en"
    answered = len(ticket.verification_answers)
    description_en = ticket.incident_description_en or ticket.incident_description or ""

    question, idx, options, sop_source, is_personalized = verification_engine.next_question(
        category=ticket.predicted_category,
        answered_count=answered,
        language=interview_lang,
        incident_description_en=description_en,
        prior_questions=ticket.verification_questions or [],
        prior_answers_en=ticket.verification_answers_en or [],
        zone_id=ticket.zone_id,
        raw_description=ticket.incident_description or "",
    )

    audio_path = None
    if question:
        full_p = tts.synthesize(question, interview_lang)
        if full_p:
            audio_path = f"/audio/{Path(full_p).name}"

    static_questions = verification_engine.get_questions(ticket.predicted_category, language=interview_lang)
    total_q = 4 if is_personalized else len(static_questions)

    return NextQuestionOut(
        done=question is None,
        question=question,
        question_index=idx if question else None,
        total_questions=total_q,
        question_audio_path=audio_path,
        options=options,
        sop_source=sop_source,
        is_personalized=is_personalized,
    )


@router.post("/{ticket_id}/answer", response_model=TicketOut)
def submit_answer(ticket_id: str, payload: AnswerSubmit, db: Session = Depends(get_db)):
    ticket = _get_ticket(ticket_id, db)
    lang = ticket.language or "en"
    answered = len(ticket.verification_answers)
    description_en = ticket.incident_description_en or ticket.incident_description or ""

    # 1. Determine what question was asked
    question = payload.question_text
    if not question:
        q_tuple = verification_engine.next_question(
            category=ticket.predicted_category,
            answered_count=answered,
            language=lang,
            incident_description_en=description_en,
            prior_questions=ticket.verification_questions or [],
            prior_answers_en=ticket.verification_answers_en or [],
            zone_id=ticket.zone_id,
            raw_description=ticket.incident_description or "",
        )
        question = q_tuple[0]

    if question is None:
        raise HTTPException(400, "all verification questions already answered")

    # 2. Use explicit answer_text_en, or map from quick option chip, or neural translation
    matched_option_en = verification_engine.find_english_option(
        category=ticket.predicted_category,
        question_idx=answered,
        answer_text=payload.answer_text,
        incident_description_en=description_en,
        prior_questions=ticket.verification_questions or [],
        prior_answers_en=ticket.verification_answers_en or [],
        zone_id=ticket.zone_id,
        language=lang,
        raw_description=ticket.incident_description or "",
    )
    answer_en = payload.answer_text_en or matched_option_en or translation.to_english(payload.answer_text, ticket.language)

    ticket.verification_questions = [*ticket.verification_questions, question]
    ticket.verification_answers = [*ticket.verification_answers, payload.answer_text]
    ticket.verification_answers_en = [*ticket.verification_answers_en, answer_en]

    remaining_question, _, _, _, _ = verification_engine.next_question(
        category=ticket.predicted_category,
        answered_count=answered + 1,
        language=lang,
        incident_description_en=description_en,
        prior_questions=ticket.verification_questions,
        prior_answers_en=ticket.verification_answers_en,
        zone_id=ticket.zone_id,
        raw_description=ticket.incident_description or "",
    )
    if remaining_question is None:
        _finalize(ticket)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.post("/{ticket_id}/finalize", response_model=TicketOut)
def finalize(ticket_id: str, db: Session = Depends(get_db)):
    ticket = _get_ticket(ticket_id, db)
    _finalize(ticket)
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def _finalize(ticket: Ticket) -> None:
    # 1. Run Answer Identification Model across all turns
    findings = answer_classifier.aggregate_interview_findings(
        ticket.verification_questions,
        ticket.verification_answers_en or ticket.verification_answers,
    )
    ticket.structured_findings = findings

    # 2. Evidence & Consistency Assessment
    score = findings.get("total_evidence_score", 0.5)
    obs_mode = findings.get("observation_mode", "unspecified")
    if obs_mode in ["visual_confirmed", "both_seen_and_smelled"]:
        status = "strongly_supported"
        score = max(score, 0.75)
    elif obs_mode == "odor_only":
        status = "needs_verification"
        score = min(max(score, 0.4), 0.65)
    elif score >= 0.7:
        status = "strongly_supported"
    elif score >= 0.4:
        status = "needs_verification"
    else:
        status = "inconsistent_insufficient"

    ticket.verification_score = round(score, 2)
    ticket.verification_status = status

    # 3. Spatial Consequence Assessment
    impact = spatial_impact.assess(ticket.zone_id, ticket.predicted_category)
    if impact:
        ticket.impact_assessment = impact

    # 4. Transparent Risk Scoring & Escalation Routing
    risk_score = routing.compute_risk_score(ticket.predicted_category, score, impact)
    ticket.risk_score = risk_score
    ticket.routing_tier = routing.route(ticket.report_type, risk_score, impact)
    ticket.status = "in_progress"

    photo_url = None
    if ticket.photo_proof_path:
        photo_filename = Path(ticket.photo_proof_path).name
        photo_url = f"/photos/{photo_filename}"

    # 5. Generate Structured Safety Incident Report
    report = report_generator.generate_incident_report(
        ticket_id=ticket.id,
        category=ticket.predicted_category,
        category_confidence=ticket.category_confidence,
        zone_id=ticket.zone_id,
        initial_statement=ticket.incident_description,
        initial_statement_en=ticket.incident_description_en,
        findings=findings,
        impact=impact,
        routing_tier=ticket.routing_tier,
        risk_score=risk_score,
        photo_url=photo_url,
        report_type=ticket.report_type or "suspected",
        verification_questions=ticket.verification_questions,
        verification_answers=ticket.verification_answers,
        verification_answers_en=ticket.verification_answers_en,
    )
    ticket.safety_report = report
    ticket.guidance_text = report["report_markdown"]
    ticket.guidance_sources = report["sources"]

    # 6. Concise Audio Briefing
    summary_for_voice = (
        f"Verification completed. Category: {report['category_title']}. "
        f"Threat level: {report['threat_level']}. Immediate safety actions are on your screen."
    )
    native_voice_text = translation.from_english(summary_for_voice, ticket.language) if ticket.language and ticket.language != "en" else summary_for_voice
    ticket.guidance_text_native = native_voice_text
    full_audio = tts.synthesize(native_voice_text, ticket.language or "en")
    ticket.guidance_audio_path = f"/audio/{Path(full_audio).name}" if full_audio else None

    # 7. Generate Personalized Precautionary Measures Grounded in BSL SOPs
    try:
        ticket.precautionary_measures = precautionary_measures.generate_precautionary_measures(ticket)
    except Exception as exc:
        pass
