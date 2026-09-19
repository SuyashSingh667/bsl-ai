"""
Phase 8.3 — Demo / Simulation Mode.

Creates synthetic plant data and scripted incidents so the product can be
demonstrated to plant safety officers without real incident data.

Activated by setting env var:  BSL_DEMO_MODE=1
The demo seed is idempotent — running it multiple times does not add duplicates
if tickets with the demo seed prefix already exist.

Demo tickets are prefixed with "DEMO_" in their employee_id field so they can be
filtered out of production reporting queries.

Usage (from backend/):
    ./venv/bin/python -m app.services.demo_mode

Or via the admin API:
    POST /admin/demo/seed
    DELETE /admin/demo/clear
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models import Ticket

logger = logging.getLogger(__name__)

DEMO_ENABLED: bool = os.getenv("BSL_DEMO_MODE", "0").strip() == "1"
DEMO_EMPLOYEE_PREFIX = "DEMO_WORKER"


# ── Scripted incident scenarios ───────────────────────────────────────────────
# Each entry is a realistic heavy-industry safety incident:
# - Mix of emergency and suspected types
# - Spread across shifts, zones, and categories
# - Some resolved, some open
# - Some offline, some false-alarm for metric demos

DEMO_INCIDENTS: list[dict[str, Any]] = [
    {
        "report_type": "emergency",
        "incident_description": "BF gas leak detected near stove area, strong smell, workers evacuating",
        "incident_description_en": "BF gas leak detected near stove area, strong smell, workers evacuating",
        "zone_id": "BF1",
        "shift": "A",
        "predicted_category": "gas_leak",
        "category_confidence": 0.91,
        "language": "hi",
        "language_confidence": 0.88,
        "risk_score": 9.2,
        "routing_tier": "critical",
        "dispatch_status": "acknowledged",
        "dispatched_offset_min": -45,
        "acknowledged_offset_min": -43,  # 2 min ACK time
        "lifecycle_stage": "action_assigned",
        "corrective_action": "Isolate BF gas pipeline valve V-17, evacuate 200m radius, deploy gas detection team",
        "assigned_to": "Shift Safety Officer Ravi Kumar",
        "completed_offline": False,
        "false_alarm": False,
    },
    {
        "report_type": "emergency",
        "incident_description": "Worker fell from scaffold near coke oven battery 3, unconscious",
        "incident_description_en": "Worker fell from scaffold near coke oven battery 3, unconscious",
        "zone_id": "COB",
        "shift": "B",
        "predicted_category": "fall_from_height",
        "category_confidence": 0.95,
        "language": "en",
        "language_confidence": 0.97,
        "risk_score": 10.0,
        "routing_tier": "critical",
        "dispatch_status": "on_site",
        "dispatched_offset_min": -120,
        "acknowledged_offset_min": -118,
        "on_site_offset_min": -115,
        "lifecycle_stage": "action_taken",
        "corrective_action": "Medical team dispatched. Area cordoned. Scaffold inspection ordered.",
        "assigned_to": "ERT Lead Suresh Pandey",
        "completed_offline": False,
        "false_alarm": False,
    },
    {
        "report_type": "suspected",
        "incident_description": "Sparks and smoke from electrical panel in rolling mill control room",
        "incident_description_en": "Sparks and smoke from electrical panel in rolling mill control room",
        "zone_id": "HRM",
        "shift": "C",
        "predicted_category": "electrical_hazard",
        "category_confidence": 0.83,
        "language": "hi",
        "language_confidence": 0.79,
        "risk_score": 6.1,
        "routing_tier": "high",
        "dispatch_status": "dispatched",
        "dispatched_offset_min": -8,
        "lifecycle_stage": "under_review",
        "completed_offline": False,
        "false_alarm": False,
    },
    {
        "report_type": "suspected",
        "incident_description": "Overhead crane cable looks frayed near SMS bay crane #4, needs inspection",
        "incident_description_en": "Overhead crane cable looks frayed near SMS bay crane #4, needs inspection",
        "zone_id": "SMS",
        "shift": "A",
        "predicted_category": "equipment_hazard",
        "category_confidence": 0.75,
        "language": "en",
        "language_confidence": 0.92,
        "risk_score": 5.4,
        "routing_tier": "medium",
        "dispatch_status": "closed",
        "dispatched_offset_min": -1440,
        "acknowledged_offset_min": -1438,
        "lifecycle_stage": "resolved",
        "corrective_action": "Crane #4 taken offline. Cable replaced. Re-certified.",
        "assigned_to": "Mechanical Maintenance Team Lead",
        "closed_offset_min": -1380,
        "closure_time_hours": 1.0,
        "closure_notes": "Cable replaced with spec SWL-16T cable. Load test passed.",
        "completed_offline": False,
        "false_alarm": False,
    },
    {
        "report_type": "suspected",
        "incident_description": "Tuyere leaking water near blast furnace 2 tuyere stock, steam visible",
        "incident_description_en": "Tuyere leaking water near blast furnace 2 tuyere stock, steam visible",
        "zone_id": "BF2",
        "shift": "B",
        "predicted_category": "equipment_hazard",
        "category_confidence": 0.80,
        "language": "hi",
        "language_confidence": 0.85,
        "risk_score": 7.8,
        "routing_tier": "high",
        "dispatch_status": "acknowledged",
        "dispatched_offset_min": -90,
        "acknowledged_offset_min": -85,
        "lifecycle_stage": "action_assigned",
        "corrective_action": "Reduce BF throughput. Tuyere team to replace suspect tuyere stock.",
        "assigned_to": "Blast Furnace Maintenance Crew",
        "completed_offline": True,  # Demo: reported via offline queue
        "false_alarm": False,
    },
    {
        "report_type": "emergency",
        "incident_description": "False alarm — smoke detector triggered by welding fumes, no actual fire",
        "incident_description_en": "False alarm — smoke detector triggered by welding fumes, no actual fire",
        "zone_id": "PWR",
        "shift": "C",
        "predicted_category": "fire",
        "category_confidence": 0.62,
        "language": "en",
        "language_confidence": 0.96,
        "risk_score": 4.0,
        "routing_tier": "medium",
        "dispatch_status": "closed",
        "dispatched_offset_min": -3000,
        "acknowledged_offset_min": -2999,
        "lifecycle_stage": "resolved",
        "closed_offset_min": -2970,
        "closure_time_hours": 0.5,
        "closure_notes": "Confirmed welding work permit active. No fire. Detector sensitivity adjusted.",
        "false_alarm": True,  # Demo: false dispatch example
        "completed_offline": False,
    },
    {
        "report_type": "suspected",
        "incident_description": "PPE violation observed: worker without hard hat near raw material yard",
        "incident_description_en": "PPE violation observed: worker without hard hat near raw material yard",
        "zone_id": "RMY",
        "shift": "A",
        "predicted_category": "ppe_violation",
        "category_confidence": 0.88,
        "language": "hi",
        "language_confidence": 0.82,
        "risk_score": 3.5,
        "routing_tier": "low",
        "dispatch_status": "pending",
        "lifecycle_stage": "received",
        "is_anonymous": True,
        "completed_offline": True,  # Demo: offline near-miss
        "false_alarm": False,
    },
    {
        "report_type": "suspected",
        "incident_description": "LOTO violation: equipment being maintained without proper lockout tag",
        "incident_description_en": "LOTO violation: equipment being maintained without proper lockout tag",
        "zone_id": "SMS2",
        "shift": "B",
        "predicted_category": "loto_violation",
        "category_confidence": 0.78,
        "language": "en",
        "language_confidence": 0.94,
        "risk_score": 8.1,
        "routing_tier": "high",
        "dispatch_status": "acknowledged",
        "dispatched_offset_min": -200,
        "acknowledged_offset_min": -198,
        "lifecycle_stage": "under_review",
        "completed_offline": False,
        "false_alarm": False,
    },
]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _offset(minutes: int) -> datetime:
    return _now() + timedelta(minutes=minutes)


def _demo_id(n: int) -> str:
    return f"demo{n:04d}"


def seed_demo_data(db: Session, plant_id: str = "bsl_bokaro") -> list[str]:
    """
    Creates synthetic incident tickets for demo mode.
    Idempotent: skips creation if tickets with the same demo IDs already exist.
    Returns list of created ticket IDs.
    """
    created_ids: list[str] = []

    for i, scenario in enumerate(DEMO_INCIDENTS):
        ticket_id = _demo_id(i + 1)
        existing = db.get(Ticket, ticket_id)
        if existing:
            logger.info(f"Demo ticket {ticket_id} already exists — skipping.")
            continue

        now = _now()
        dispatched_at = (
            _offset(scenario["dispatched_offset_min"])
            if "dispatched_offset_min" in scenario
            else None
        )
        acknowledged_at = (
            _offset(scenario["acknowledged_offset_min"])
            if "acknowledged_offset_min" in scenario
            else None
        )
        on_site_at = (
            _offset(scenario["on_site_offset_min"])
            if "on_site_offset_min" in scenario
            else None
        )
        closed_at = (
            _offset(scenario["closed_offset_min"])
            if "closed_offset_min" in scenario
            else None
        )

        # Time from creation to dispatch (realistic offset)
        created_at = (
            _offset(scenario.get("dispatched_offset_min", 0) - 2)
            if "dispatched_offset_min" in scenario
            else now
        )

        ticket = Ticket(
            id=ticket_id,
            plant_id=plant_id,
            created_at=created_at,
            updated_at=now,
            employee_id=f"{DEMO_EMPLOYEE_PREFIX}_{i + 1:02d}",
            reporting_mode="personal",
            report_type=scenario["report_type"],
            incident_description=scenario["incident_description"],
            incident_description_en=scenario["incident_description_en"],
            zone_id=scenario.get("zone_id"),
            shift=scenario.get("shift", "A"),
            predicted_category=scenario.get("predicted_category"),
            category_confidence=scenario.get("category_confidence"),
            language=scenario.get("language", "en"),
            language_confidence=scenario.get("language_confidence"),
            risk_score=scenario.get("risk_score"),
            routing_tier=scenario.get("routing_tier"),
            dispatch_status=scenario.get("dispatch_status", "pending"),
            dispatched_at=dispatched_at,
            acknowledged_at=acknowledged_at,
            acknowledged_by="ERT Control Room" if acknowledged_at else None,
            on_site_at=on_site_at,
            on_site_by="ERT Lead" if on_site_at else None,
            lifecycle_stage=scenario.get("lifecycle_stage", "received"),
            corrective_action=scenario.get("corrective_action"),
            assigned_to=scenario.get("assigned_to"),
            closed_at=closed_at,
            closure_time_hours=scenario.get("closure_time_hours"),
            closure_notes=scenario.get("closure_notes"),
            status="closed" if closed_at else "open",
            is_anonymous=scenario.get("is_anonymous", False),
            completed_offline=scenario.get("completed_offline", False),
            false_alarm=scenario.get("false_alarm", False),
            verification_status="pending",
            flagged_for_human_review=False,
            sop_gap_detected=False,
            guidance_sources=[],
            model_versions={"demo": "1.0"},
        )
        db.add(ticket)
        db.commit()
        db.refresh(ticket)
        created_ids.append(ticket_id)
        logger.info(f"Seeded demo ticket {ticket_id}: {scenario['predicted_category']}")

    return created_ids


def clear_demo_data(db: Session, plant_id: str = "bsl_bokaro") -> int:
    """Removes all demo tickets (those with employee_id starting with DEMO_WORKER)."""
    from sqlalchemy import delete, select

    stmt = select(Ticket).where(
        Ticket.plant_id == plant_id,
        Ticket.employee_id.like(f"{DEMO_EMPLOYEE_PREFIX}%"),
    )
    demo_tickets = list(db.scalars(stmt).all())
    count = 0
    for t in demo_tickets:
        db.delete(t)
        count += 1
    db.commit()
    logger.info(f"Cleared {count} demo tickets from plant {plant_id}.")
    return count


if __name__ == "__main__":
    # Allow running directly: ./venv/bin/python -m app.services.demo_mode
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent.parent))
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        ids = seed_demo_data(db)
        print(f"Seeded {len(ids)} demo incidents: {ids}")
    finally:
        db.close()
