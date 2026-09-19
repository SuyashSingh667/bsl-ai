from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app.schemas import PrecautionaryMeasuresOut, TicketOut
from app.services import precautionary_measures, rag, translation, tts

router = APIRouter(prefix="/guidance", tags=["guidance"])


@router.get("/{ticket_id}/precautions", response_model=PrecautionaryMeasuresOut)
@router.post("/{ticket_id}/precautions", response_model=PrecautionaryMeasuresOut)
def get_or_generate_precautions(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "ticket not found")

    has_answers = bool(ticket.verification_answers or ticket.verification_answers_en)
    # If the ticket has verification interview answers, always regenerate fresh precautions
    # to guarantee they reflect the latest situation facts provided in the interview answers.
    if ticket.precautionary_measures and not has_answers:
        return ticket.precautionary_measures

    precautions = precautionary_measures.generate_precautionary_measures(ticket)
    ticket.precautionary_measures = precautions
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return precautions


@router.post("/{ticket_id}", response_model=TicketOut)
def generate(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "ticket not found")

    query = " ".join([ticket.incident_description_en, *ticket.verification_answers_en])
    guidance_text, sources = rag.generate_guidance(ticket.predicted_category, query)

    ticket.guidance_text = guidance_text
    ticket.guidance_sources = sources

    # Retrieval/generation only happens over the English document set, so
    # the English guidance_text is the ground truth here; translate it back
    # to the worker's language for playback, per the dynamic-content
    # translation rule in voice_pipeline.md (fixed question bank is
    # pre-approved-translation-only, but generated guidance is fine to
    # machine-translate since it's open-ended content either way).
    guidance_text_native = translation.from_english(guidance_text, ticket.language)
    ticket.guidance_text_native = guidance_text_native

    ticket.guidance_audio_path = tts.synthesize(guidance_text_native, ticket.language)

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    if ticket.photo_proof_path:
        ticket.photo_url = f"/photos/{Path(ticket.photo_proof_path).name}"
    return ticket
