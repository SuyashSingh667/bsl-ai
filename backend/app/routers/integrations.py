"""
Integration & Data Export Router for BSL AI Platform.
Provides standardized CSV and JSON export endpoints compatible with
enterprise safety management systems (SAP EHS, Enablon, Cority).
"""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Ticket
from app.services import audit_logger, integration_dispatcher, plant_manager
from app.services.rbac import AuthContext, UserRole, get_current_auth, require_role

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.get("/export/csv")
def export_tickets_csv(
    plant_id: str = "bsl_bokaro",
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN, UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM)),
):
    """
    Exports incident tickets to CSV format matching SAP EHS / Enablon schemas.
    """
    stmt = select(Ticket).where(Ticket.plant_id == plant_id).order_by(Ticket.created_at.desc())
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)

    tickets = db.execute(stmt).scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Standard enterprise EHS header columns
    headers = [
        "Incident ID",
        "Plant ID",
        "Created At (UTC)",
        "Updated At (UTC)",
        "Report Type",
        "Reporting Mode",
        "Worker Badge ID",
        "Supervisor Badge ID",
        "Zone ID",
        "Predicted Category",
        "Category Confidence",
        "Routing Tier",
        "Risk Score",
        "Status",
        "Description Native",
        "Description English",
        "Language",
        "SOP Sources",
        "Flagged For Human Review",
        "Resolution Notes",
    ]
    writer.writerow(headers)

    for t in tickets:
        sop_codes = []
        if t.guidance_sources:
            sop_codes = [s.get("sop_id", "") for s in t.guidance_sources if s.get("sop_id")]
        sop_str = "; ".join(filter(None, sop_codes))

        writer.writerow([
            t.id,
            t.plant_id,
            t.created_at.isoformat() if t.created_at else "",
            t.updated_at.isoformat() if t.updated_at else "",
            t.report_type,
            t.reporting_mode,
            t.worker_badge_id or "",
            t.reporter_supervisor_id or "",
            t.zone_id or "",
            t.predicted_category or "",
            round(t.category_confidence, 2) if t.category_confidence else "",
            t.routing_tier or "",
            round(t.risk_score, 2) if t.risk_score else "",
            t.status,
            t.incident_description or "",
            t.incident_description_en or "",
            t.language or "",
            sop_str,
            "YES" if t.flagged_for_human_review else "NO",
            t.resolution_notes or "",
        ])

    csv_data = output.getvalue()
    filename = f"safety_incidents_{plant_id}.csv"

    # Audit the data export
    audit_logger.log_event(
        db=db,
        action="DATA_EXPORTED_CSV",
        plant_id=plant_id,
        actor_id=auth.user_id,
        actor_role=auth.role.value,
        details={"record_count": len(tickets), "format": "CSV"},
    )

    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/export/json")
def export_tickets_json(
    plant_id: str = "bsl_bokaro",
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN, UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM)),
):
    """Exports structured incident data in JSON format for external BI or analytics."""
    stmt = select(Ticket).where(Ticket.plant_id == plant_id).order_by(Ticket.created_at.desc())
    if status_filter:
        stmt = stmt.where(Ticket.status == status_filter)

    tickets = db.execute(stmt).scalars().all()
    results = []
    for t in tickets:
        results.append({
            "ticket_id": t.id,
            "plant_id": t.plant_id,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "report_type": t.report_type,
            "reporting_mode": t.reporting_mode,
            "worker_badge_id": t.worker_badge_id,
            "zone_id": t.zone_id,
            "category": t.predicted_category,
            "routing_tier": t.routing_tier,
            "risk_score": t.risk_score,
            "status": t.status,
            "description": t.incident_description_en or t.incident_description,
            "extracted_entities": t.extracted_entities,
            "safety_report": t.safety_report,
            "visual_analysis": t.visual_analysis,
        })

    audit_logger.log_event(
        db=db,
        action="DATA_EXPORTED_JSON",
        plant_id=plant_id,
        actor_id=auth.user_id,
        actor_role=auth.role.value,
        details={"record_count": len(tickets), "format": "JSON"},
    )

    return {"plant_id": plant_id, "count": len(results), "incidents": results}


@router.post("/test-dispatch")
def test_dispatch_hook(
    plant_id: str = "bsl_bokaro",
    webhook_url: str | None = Query(default=None),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN)),
):
    """Triggers a test dispatch event to verify webhook, SMS, and WhatsApp configurations."""
    test_ticket = Ticket(
        id="TEST-DISPATCH-99",
        plant_id=plant_id,
        report_type="emergency",
        reporting_mode="kiosk",
        worker_badge_id="TEST-BADGE-01",
        zone_id="BF1",
        predicted_category="gas_leak",
        routing_tier="emergency_authority",
        risk_score=0.92,
        incident_description="Test automated emergency dispatch connectivity",
        incident_description_en="Test automated emergency dispatch connectivity",
    )

    result = integration_dispatcher.dispatch_incident_notifications(test_ticket, plant_id=plant_id, webhook_url=webhook_url)
    return {"status": "success", "dispatch_result": result}
