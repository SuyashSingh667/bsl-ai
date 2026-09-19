"""
Data Retention and Privacy Pruning Service.
Enforces configurable data-retention schedules (e.g. 90/180/365 days):
  1. Deletes physical raw audio recordings and photo/video proofs past retention limit.
  2. Anonymizes frontline worker PII (badge IDs, employee numbers).
  3. Preserves statutory industrial incident metrics (zone, category, severity, resolution)
     for factory inspectorate and OSHA compliance.
  4. Records every pruning event into the immutable tamper-evident audit log.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Ticket
from app.services import audit_logger, plant_manager

logger = logging.getLogger(__name__)


def prune_expired_media(
    db: Session,
    plant_id: str = "bsl_bokaro",
    retention_days: int | None = None,
    actor_id: str = "RETENTION_CRON",
) -> dict[str, Any]:
    """
    Scans tickets older than retention_days, purges audio/photo media from disk,
    and anonymizes worker identifiers while maintaining safety logs.
    """
    if retention_days is None:
        plant = plant_manager.get_plant(plant_id)
        retention_days = plant.get("data_retention_days", 180)

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)

    stmt = (
        select(Ticket)
        .where(Ticket.plant_id == plant_id)
        .where(Ticket.created_at < cutoff_date)
        .where(Ticket.audio_path.isnot(None) | Ticket.photo_proof_path.isnot(None) | (Ticket.worker_badge_id != "ANONYMIZED"))
    )

    tickets_to_prune = db.execute(stmt).scalars().all()

    audio_files_deleted = 0
    photos_deleted = 0
    records_anonymized = 0

    for ticket in tickets_to_prune:
        # 1. Delete physical audio file
        if ticket.audio_path:
            audio_p = Path(ticket.audio_path)
            if audio_p.exists():
                try:
                    os.remove(audio_p)
                    audio_files_deleted += 1
                except Exception as exc:
                    logger.warning(f"Failed to remove expired audio {audio_p}: {exc}")
            ticket.audio_path = None

        # 2. Delete physical photo/video file
        if ticket.photo_proof_path:
            photo_p = Path(ticket.photo_proof_path)
            if photo_p.exists():
                try:
                    os.remove(photo_p)
                    photos_deleted += 1
                except Exception as exc:
                    logger.warning(f"Failed to remove expired photo {photo_p}: {exc}")
            ticket.photo_proof_path = None

        # 3. Anonymize worker PII
        if ticket.worker_badge_id or ticket.employee_id or ticket.reporter_supervisor_id:
            ticket.worker_badge_id = "ANONYMIZED"
            ticket.employee_id = "ANONYMIZED"
            ticket.reporter_supervisor_id = "ANONYMIZED" if ticket.reporter_supervisor_id else None
            records_anonymized += 1

    db.commit()

    details = {
        "retention_days": retention_days,
        "cutoff_date": cutoff_date.isoformat(),
        "audio_files_deleted": audio_files_deleted,
        "photos_deleted": photos_deleted,
        "records_anonymized": records_anonymized,
    }

    if records_anonymized > 0 or audio_files_deleted > 0:
        audit_logger.log_event(
            db=db,
            action="DATA_RETENTION_PRUNED",
            plant_id=plant_id,
            actor_id=actor_id,
            actor_role="admin",
            details=details,
        )

    logger.info(f"[Data Retention] Plant {plant_id}: Pruned {audio_files_deleted} audio, {photos_deleted} photos, anonymized {records_anonymized} tickets")
    return details
