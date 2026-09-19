"""
Admin & Plant Onboarding Router for BSL AI Platform.
Enables dynamic onboarding of new steel plants, hazard zone definitions,
multi-format SOP ingestion (DOCX/PDF/MD/TXT), emergency team mapping,
and audit log verification without server restarts or code changes.
"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AuditLog
from app.schemas import AuditLogOut, EmergencyTeamDefinition, PlantZoneDefinition
from app.services import audit_logger, plant_manager, sop_parser
from app.services.rbac import AuthContext, UserRole, get_current_auth, require_role

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/plants")
def list_plants():
    """Lists all configured heavy industrial plant tenants."""
    return plant_manager.list_plants()


@router.get("/plants/{plant_id}")
def get_plant_details(plant_id: str):
    """Retrieves layout, zones, pipelines, transformers, and emergency teams for a plant."""
    return plant_manager.get_plant(plant_id)


@router.post("/plants")
def create_or_import_plant(
    plant_config: dict[str, Any],
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN)),
):
    """Imports or updates a complete plant configuration JSON."""
    plant_id = plant_config.get("plant_id")
    if not plant_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Configuration must contain 'plant_id'")

    registered = plant_manager.register_or_update_plant(plant_config)

    # Record action in immutable audit log
    audit_logger.log_event(
        db=db,
        action="PLANT_REGISTERED",
        plant_id=plant_id,
        actor_id=auth.user_id,
        actor_role=auth.role.value,
        details={"plant_name": registered.get("name"), "zone_count": len(registered.get("zones", []))},
    )

    return {"status": "success", "message": f"Plant '{plant_id}' successfully registered", "plant": registered}


@router.put("/plants/{plant_id}/zones")
def update_plant_zones(
    plant_id: str,
    zones: list[PlantZoneDefinition],
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN, UserRole.SAFETY_OFFICER)),
):
    """Updates hazard zones, phone-restricted flags, and safe kiosk alternatives for a plant."""
    plant = plant_manager.get_plant(plant_id)
    prev_zones = plant.get("zones", [])

    plant["zones"] = [z.model_dump() for z in zones]
    plant_manager.register_or_update_plant(plant)

    audit_logger.log_event(
        db=db,
        action="ZONES_UPDATED",
        plant_id=plant_id,
        actor_id=auth.user_id,
        actor_role=auth.role.value,
        previous_state={"zone_count": len(prev_zones)},
        new_state={"zone_count": len(zones)},
        details={"zones_updated": [z.zone_id for z in zones]},
    )

    return {"status": "success", "plant_id": plant_id, "zones": plant["zones"]}


@router.post("/plants/{plant_id}/sops/upload")
async def upload_plant_sop(
    plant_id: str,
    file: UploadFile = File(...),
    sop_id: str = Form(...),
    title: str = Form(...),
    version: str = Form("1.0"),
    incident_types: str = Form(""),  # Comma-separated categories
    reviewed_by_safety_officer: bool = Form(True),
    reviewer: str = Form("Safety Officer Command"),
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN, UserRole.SAFETY_OFFICER)),
):
    """
    Uploads and indexes an approved safety procedure in DOCX, PDF, Markdown, or TXT format.
    Automatically parses text, creates structured sections, and embeds into tenant RAG index.
    """
    file_bytes = await file.read()
    if not file_bytes:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Uploaded file is empty")

    types_list = [t.strip() for t in incident_types.split(",") if t.strip()]
    if not types_list:
        types_list = ["general_safety"]

    result = sop_parser.ingest_sop_document(
        plant_id=plant_id,
        filename=file.filename or "uploaded_sop.txt",
        file_bytes=file_bytes,
        sop_id=sop_id,
        title=title,
        version=version,
        incident_types=types_list,
        reviewer=reviewer,
        reviewed_by_safety_officer=reviewed_by_safety_officer,
    )

    audit_logger.log_event(
        db=db,
        action="SOP_UPLOADED",
        plant_id=plant_id,
        actor_id=auth.user_id,
        actor_role=auth.role.value,
        details={"sop_id": sop_id, "title": title, "version": version, "sections": result["section_count"]},
    )

    return {"status": "success", "sop": result}


@router.put("/plants/{plant_id}/emergency-teams")
def update_emergency_teams(
    plant_id: str,
    teams: list[EmergencyTeamDefinition],
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN, UserRole.CONTROL_ROOM)),
):
    """Configures emergency dispatch teams (Phone, SMS, WhatsApp, Radio) per plant."""
    plant = plant_manager.get_plant(plant_id)
    prev_teams = plant.get("emergency_teams", [])

    plant["emergency_teams"] = [t.model_dump() for t in teams]
    plant_manager.register_or_update_plant(plant)

    audit_logger.log_event(
        db=db,
        action="EMERGENCY_TEAMS_UPDATED",
        plant_id=plant_id,
        actor_id=auth.user_id,
        actor_role=auth.role.value,
        previous_state={"team_count": len(prev_teams)},
        new_state={"team_count": len(teams)},
        details={"teams": [t.team_id for t in teams]},
    )

    return {"status": "success", "plant_id": plant_id, "emergency_teams": plant["emergency_teams"]}


@router.get("/audit-logs", response_model=list[AuditLogOut])
def get_audit_logs(
    plant_id: str = "bsl_bokaro",
    limit: int = 50,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN, UserRole.SAFETY_OFFICER, UserRole.CONTROL_ROOM)),
):
    """Fetches immutable audit log entries for a plant with cryptographic entry hashes."""
    stmt = (
        select(AuditLog)
        .where(AuditLog.plant_id == plant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


@router.get("/audit-logs/verify")
def verify_audit_ledger(
    plant_id: str = "bsl_bokaro",
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(require_role(UserRole.ADMIN, UserRole.SAFETY_OFFICER)),
):
    """Cryptographically verifies the entire SHA-256 hash chain of the audit ledger."""
    is_valid, records_verified, err = audit_logger.verify_chain_integrity(db, plant_id)
    return {
        "plant_id": plant_id,
        "is_valid": is_valid,
        "records_verified": records_verified,
        "tampering_detected": not is_valid,
        "error_details": err,
    }
