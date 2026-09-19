"""
Similar Incident Intelligence and Recurring Hazard Detection.
Computes semantic similarity against historical incident tickets using
sentence-transformer embeddings and flags recurring hazard patterns.
"""

from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ticket
from app.services import embeddings


def find_similar(ticket_id: str, db: Session, top_k: int = 5) -> dict:
    target = db.get(Ticket, ticket_id)
    if not target:
        return {"similar_tickets": [], "recurring_hazard": False, "recurrence_note": None}

    query_text = target.incident_description_en or target.incident_description
    if not query_text or not query_text.strip():
        return {"similar_tickets": [], "recurring_hazard": False, "recurrence_note": None}

    # Fetch all other tickets
    stmt = select(Ticket).where(Ticket.id != ticket_id).order_by(Ticket.created_at.desc())
    candidates = db.execute(stmt).scalars().all()

    if not candidates:
        return {"similar_tickets": [], "recurring_hazard": False, "recurrence_note": None}

    candidate_texts = [c.incident_description_en or c.incident_description for c in candidates]
    target_vec = embeddings.encode([query_text])[0]
    candidate_vecs = embeddings.encode(candidate_texts)

    similarities = candidate_vecs @ target_vec  # cosine similarity

    ranked_results = []
    same_zone_similar_count = 0
    now = datetime.now(timezone.utc)

    for cand, sim in zip(candidates, similarities):
        sim_score = round(float(sim), 3)
        if sim_score >= 0.35:  # meaningful threshold
            entry = {
                "id": cand.id,
                "created_at": cand.created_at.isoformat(),
                "zone_id": cand.zone_id,
                "predicted_category": cand.predicted_category,
                "routing_tier": cand.routing_tier,
                "status": cand.status,
                "incident_description": cand.incident_description_en or cand.incident_description,
                "similarity": sim_score,
                "is_same_zone": bool(target.zone_id and cand.zone_id == target.zone_id),
            }
            ranked_results.append(entry)

            # Check recurring hazard condition: same zone, high similarity (>= 0.60) or same category
            if target.zone_id and cand.zone_id == target.zone_id and (sim_score >= 0.60 or cand.predicted_category == target.predicted_category):
                cand_dt = cand.created_at
                if cand_dt.tzinfo is not None:
                    cand_dt = cand_dt.astimezone(timezone.utc)
                else:
                    cand_dt = cand_dt.replace(tzinfo=timezone.utc)
                days_diff = abs((now - cand_dt).total_seconds()) / 86400
                if days_diff <= 30:
                    same_zone_similar_count += 1

    ranked_results.sort(key=lambda x: -x["similarity"])
    top_similar = ranked_results[:top_k]

    recurring_hazard = same_zone_similar_count >= 1
    recurrence_note = None
    if recurring_hazard:
        recurrence_note = (
            f"Recurring hazard detected: {same_zone_similar_count} related incident(s) "
            f"in zone '{target.zone_id}' within the last 30 days. Priority inspection recommended."
        )

    return {
        "ticket_id": ticket_id,
        "similar_tickets": top_similar,
        "recurring_hazard": recurring_hazard,
        "recurrence_note": recurrence_note,
        "same_zone_recent_matches": same_zone_similar_count,
    }
