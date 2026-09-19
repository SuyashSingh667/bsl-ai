from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app.services import similar_incidents

router = APIRouter(prefix="/tickets", tags=["intelligence"])


@router.get("/{ticket_id}/similar")
def get_similar_incidents(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.get(Ticket, ticket_id)
    if not ticket:
        raise HTTPException(404, "ticket not found")
    return similar_incidents.find_similar(ticket_id, db)
