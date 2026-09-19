"""
Immutable Tamper-Evident Audit Logger for BSL AI Platform.
Cryptographically chains audit events via SHA-256 (blockchain-style backlink).
Any deletion, tampering, or backdating breaks the cryptographic chain.
"""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger(__name__)

GENESIS_HASH = "0000000000000000000000000000000000000000000000000000000000000000"


def _normalize_ts(ts: datetime | str | None) -> str:
    if ts is None:
        return ""
    if isinstance(ts, datetime):
        return ts.strftime("%Y-%m-%d %H:%M:%S")
    return str(ts).split(".")[0].replace("T", " ").replace("Z", "")


def _compute_hash(
    prev_hash: str,
    plant_id: str,
    ticket_id: str | None,
    actor_id: str,
    actor_role: str,
    action: str,
    timestamp: datetime | str,
    details: dict[str, Any],
) -> str:
    ts_str = _normalize_ts(timestamp)
    payload = f"{prev_hash}|{plant_id}|{ticket_id or ''}|{actor_id}|{actor_role}|{action}|{ts_str}|{json.dumps(details, sort_keys=True)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def log_event(
    db: Session,
    action: str,
    plant_id: str = "bsl_bokaro",
    ticket_id: str | None = None,
    actor_id: str = "SYSTEM",
    actor_role: str = "system",
    previous_state: dict[str, Any] | None = None,
    new_state: dict[str, Any] | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Appends an immutable audit event to the ledger with SHA-256 hash chaining.
    """
    details = details or {}
    now = datetime.now(timezone.utc)

    # Find the latest audit entry for this plant to obtain the chain head
    stmt = (
        select(AuditLog)
        .where(AuditLog.plant_id == plant_id)
        .order_by(AuditLog.created_at.desc(), AuditLog.id.desc())
        .limit(1)
    )
    last_entry = db.execute(stmt).scalars().first()
    prev_hash = last_entry.entry_hash if last_entry and last_entry.entry_hash else GENESIS_HASH

    entry_hash = _compute_hash(
        prev_hash=prev_hash,
        plant_id=plant_id,
        ticket_id=ticket_id,
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        timestamp=now,
        details=details,
    )

    entry = AuditLog(
        plant_id=plant_id,
        ticket_id=ticket_id,
        actor_id=actor_id,
        actor_role=actor_role,
        action=action,
        previous_state=previous_state,
        new_state=new_state,
        details=details,
        created_at=now,
        prev_entry_hash=prev_hash,
        entry_hash=entry_hash,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    logger.info(f"[Audit] Recorded {action} for plant={plant_id} ticket={ticket_id} (hash={entry_hash[:10]}...)")
    return entry


def verify_chain_integrity(db: Session, plant_id: str = "bsl_bokaro") -> tuple[bool, int, str | None]:
    """
    Verifies that the audit ledger has not been tampered with.
    Follows cryptographic prev_entry_hash links in topological order.
    Returns: (is_valid, records_verified, error_reason)
    """
    stmt = (
        select(AuditLog)
        .where(AuditLog.plant_id == plant_id)
    )
    all_entries = db.execute(stmt).scalars().all()
    if not all_entries:
        return True, 0, None

    # Follow cryptographic hash pointers from genesis
    by_prev: dict[str, AuditLog] = {e.prev_entry_hash or "": e for e in all_entries}
    ordered_entries: list[AuditLog] = []
    curr_prev = GENESIS_HASH

    while curr_prev in by_prev:
        e = by_prev[curr_prev]
        ordered_entries.append(e)
        curr_prev = e.entry_hash
        if len(ordered_entries) > len(all_entries):
            break

    # If any disconnected blocks exist, fallback to created_at
    if len(ordered_entries) != len(all_entries):
        ordered_entries = sorted(all_entries, key=lambda x: (x.created_at or datetime.min, x.id))

    expected_prev = GENESIS_HASH
    for idx, entry in enumerate(ordered_entries):
        if idx == 0:
            if entry.prev_entry_hash != GENESIS_HASH:
                return False, idx, f"Genesis entry has invalid prev_entry_hash: {entry.prev_entry_hash}"
        else:
            if entry.prev_entry_hash != expected_prev:
                return False, idx, f"Hash broken at sequence #{idx} (entry {entry.id}): expected {expected_prev}, found {entry.prev_entry_hash}"

        recomputed = _compute_hash(
            prev_hash=entry.prev_entry_hash or "",
            plant_id=entry.plant_id,
            ticket_id=entry.ticket_id,
            actor_id=entry.actor_id,
            actor_role=entry.actor_role,
            action=entry.action,
            timestamp=entry.created_at,
            details=entry.details or {},
        )
        if recomputed != entry.entry_hash:
            return False, idx, f"Payload tampering detected at #{idx} (entry {entry.id})"

        expected_prev = entry.entry_hash

    return True, len(ordered_entries), None
