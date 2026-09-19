from pathlib import Path
import shutil
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import PHOTO_UPLOAD_DIR
from app.database import get_db
from app.models import Ticket
from app.schemas import TicketOut, TicketUpdate
from app.services import routing, safety_rules, visual_analysis

router = APIRouter(prefix="/tickets", tags=["tickets"])

PHOTO_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _attach_photo_url(ticket: Ticket) -> Ticket:
    if ticket and ticket.photo_proof_path:
        filename = Path(ticket.photo_proof_path).name
        url = f"/photos/{filename}"
        ticket.photo_url = url
        ticket.media_url = url
        ext = Path(ticket.photo_proof_path).suffix.lower()
        ticket.media_type = "video" if ext in [".mp4", ".webm", ".mov", ".mkv", ".avi"] else "image"
    return ticket


@router.get("", response_model=list[TicketOut])
def list_tickets(
    plant_id: str | None = None,
    routing_tier: str | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    stmt = select(Ticket).order_by(Ticket.created_at.desc())
    if plant_id:
        stmt = stmt.where(Ticket.plant_id == plant_id)
    if routing_tier:
        stmt = stmt.where(Ticket.routing_tier == routing_tier)
    if status:
        stmt = stmt.where(Ticket.status == status)
    tickets = db.execute(stmt).scalars().all()
    for t in tickets:
        _attach_photo_url(t)
    return tickets


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "ticket not found")
    _attach_photo_url(ticket)
    return ticket


@router.post("/{ticket_id}/photo", response_model=TicketOut)
def upload_photo(
    ticket_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "ticket not found")

    dest = PHOTO_UPLOAD_DIR / f"{ticket_id}_{uuid.uuid4().hex[:8]}_{file.filename}"
    with open(dest, "wb") as out:
        shutil.copyfileobj(file.file, out)

    ext = dest.suffix.lower()
    is_video = ext in [".mp4", ".webm", ".mov", ".mkv", ".avi"]
    media_type = "video" if is_video else "image"

    ticket.photo_proof_path = str(dest)
    ticket.media_type = media_type
    photo_url = f"/photos/{dest.name}"
    ticket.photo_url = photo_url
    ticket.media_url = photo_url

    # 2. Run AI Visual Hazard Analysis on the uploaded evidence
    v_analysis = visual_analysis.analyze_visual_evidence(str(dest), ticket.predicted_category or "fire")
    ticket.visual_analysis = v_analysis

    if v_analysis.get("flagged_for_human_review"):
        ticket.flagged_for_human_review = True
        ticket.review_reason = v_analysis.get("human_review_reason")

    # Invariant: Evidence-only vision may elevate urgency, but never lowers score or dismisses
    proposed_risk = ticket.risk_score
    if v_analysis.get("is_valid_evidence"):
        proposed_risk = min(1.0, round((ticket.risk_score or 0.5) + 0.10, 2))

    has_active_dispatch = bool(ticket.safety_report and ticket.safety_report.get("recipients"))
    safety_check = safety_rules.apply_safety_invariants(
        human_report_type=ticket.report_type,
        current_tier=ticket.routing_tier,
        current_risk_score=ticket.risk_score,
        proposed_tier=ticket.routing_tier,
        proposed_risk_score=proposed_risk,
        has_dispatched=has_active_dispatch,
    )
    ticket.risk_score = safety_check["risk_score"]
    ticket.routing_tier = safety_check["routing_tier"]

    # If safety report was already synthesized, update report with photo and AI analysis
    if ticket.safety_report:
        rep = dict(ticket.safety_report)
        rep["photo_url"] = photo_url
        rep["media_url"] = photo_url
        rep["media_type"] = media_type
        rep["visual_analysis"] = v_analysis
        rep["risk_score"] = ticket.risk_score

        # Check if visual evidence confirmed hazard or is uncorroborated
        if "verified_summary" in rep:
            v_sum = dict(rep["verified_summary"])
            if v_analysis.get("is_valid_evidence"):
                v_sum["observation_mode"] = f"Confirmed by AI Vision ({v_analysis['detected_event'].replace('_', ' ').title()} - {int(v_analysis['confidence']*100)}%)"
            else:
                v_sum["observation_mode"] = f"No Visual Corroboration ({v_analysis['detected_event'].replace('_', ' ').title()} - Flagged for Safety Officer Review)"
            rep["verified_summary"] = v_sum

        md = rep.get("report_markdown", "")
        if "Field Evidence" not in md and "Photographic Field Evidence" not in md:
            media_sec = (
                f"\n\n## Photographic & Video Field Evidence\n"
                f'<video controls width="100%" style="max-height: 400px; border-radius: 8px;" src="{photo_url}"></video>\n'
                f"*Verified video recording captured on site for Zone {ticket.zone_id or 'Plant Facility'}.*\n"
                if is_video else
                f"\n\n## Photographic Field Evidence\n"
                f"![Incident Scene Photographic Proof]({photo_url})\n"
                f"*Photographic evidence captured on site for Zone {ticket.zone_id or 'Plant Facility'}.*\n"
            )
            tags_str = ", ".join(f"`{t}`" for t in v_analysis.get("tags", []))
            ai_sec = (
                f"\n## 🤖 AI Visual Hazard Analysis (Advisory Evidence)\n"
                f"- **Detected Visual Event:** `{v_analysis['detected_event'].replace('_', ' ').title()}`\n"
                f"- **Model Confidence:** `{int(v_analysis['confidence'] * 100)}%`\n"
                f"- **Visual Status:** `{'PHYSICALLY CORROBORATED' if v_analysis['is_valid_evidence'] else 'NO VISUAL CORROBORATION'}`\n"
                f"- **Evidence Tags:** {tags_str}\n"
                f"- **Human Review Flag:** `{'FLAGGED FOR SAFETY OFFICER REVIEW' if v_analysis.get('flagged_for_human_review') else 'CORROBORATED'}`\n"
                f"- **Calculated Risk Score Impact:** `{'Elevated by visual proof' if v_analysis['is_valid_evidence'] else 'Held strictly neutral (never lowered)'}`\n"
                f"- **Detailed Assessment:** *{v_analysis['visual_summary']}*\n"
            )
            rep["report_markdown"] = f"{md}\n{media_sec}\n{ai_sec}"
        ticket.safety_report = rep
        ticket.guidance_text = rep.get("report_markdown")

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    _attach_photo_url(ticket)

    try:
        from app.services import audit_logger
        audit_logger.log_event(
            db=db,
            action="VISUAL_EVIDENCE_ATTACHED",
            plant_id=ticket.plant_id,
            ticket_id=ticket.id,
            actor_id="SAFETY_OPERATOR",
            actor_role="safety_officer",
            details={
                "media_type": media_type,
                "is_valid_evidence": v_analysis.get("is_valid_evidence"),
                "detected_event": v_analysis.get("detected_event"),
            },
        )
    except Exception:
        pass

    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: str, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "ticket not found")

    prev_status = ticket.status
    if payload.status is not None:
        ticket.status = payload.status
    if payload.resolution_notes is not None:
        ticket.resolution_notes = payload.resolution_notes
    if payload.routing_tier is not None:
        ticket.routing_tier = payload.routing_tier
    if payload.language is not None:
        ticket.language = payload.language

    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    _attach_photo_url(ticket)

    try:
        from app.services import audit_logger
        audit_logger.log_event(
            db=db,
            action="TICKET_UPDATED",
            plant_id=ticket.plant_id,
            ticket_id=ticket.id,
            actor_id="SAFETY_OFFICER",
            actor_role="safety_officer",
            previous_state={"status": prev_status},
            new_state={"status": ticket.status, "routing_tier": ticket.routing_tier},
            details={"resolution_notes": payload.resolution_notes},
        )
    except Exception:
        pass

    return ticket
