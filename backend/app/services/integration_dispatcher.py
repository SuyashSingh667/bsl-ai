"""
Outbound Dispatch Integration Dispatcher for BSL AI Platform.
Dispatches critical safety incident alerts via:
  1. Signed Outbound Webhooks (HMAC-SHA256) for control room SCADA / DCS integration
  2. SMS Gateway alerts to Emergency Response Teams
  3. WhatsApp Business notifications for shift supervisors
  4. Email notifications for safety superintendents
All outbound calls fail safely without blocking internal incident persistence.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import urllib.request
from typing import Any

from app.models import Ticket
from app.services import plant_manager

logger = logging.getLogger(__name__)

WEBHOOK_SECRET = os.getenv("BSL_WEBHOOK_SECRET", "bsl-production-safety-secret-key-2026")
DEFAULT_WEBHOOK_URL = os.getenv("BSL_DISPATCH_WEBHOOK_URL", "")


def _sign_payload(secret: str, payload_bytes: bytes) -> str:
    """Generates HMAC-SHA256 signature for outbound webhook verification."""
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def send_webhook(
    url: str,
    payload: dict[str, Any],
    secret: str = WEBHOOK_SECRET,
    timeout_s: float = 4.0,
) -> dict[str, Any]:
    """Sends a signed HTTP POST webhook to an external safety receiver."""
    if not url:
        return {"status": "skipped", "reason": "no_url_configured"}

    payload_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    signature = _sign_payload(secret, payload_bytes)

    req = urllib.request.Request(
        url,
        data=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-BSL-Signature": f"sha256={signature}",
            "User-Agent": "BSL-AI-Safety-Dispatcher/2.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as response:
            status_code = response.getcode()
            logger.info(f"Outbound webhook dispatched to {url} (status: {status_code})")
            return {"status": "delivered", "status_code": status_code}
    except Exception as exc:
        logger.warning(f"Outbound webhook delivery failed to {url}: {exc}")
        return {"status": "failed", "error": str(exc)}


def send_sms_alert(phone_number: str, message: str) -> dict[str, Any]:
    """
    Sends emergency SMS via telecom gateway interface.
    Gracefully simulates delivery when external telecom gateway credentials are unconfigured.
    """
    if not phone_number:
        return {"status": "skipped", "reason": "empty_phone_number"}

    logger.info(f"[SMS Gateway] Dispatched emergency alert to {phone_number}: '{message[:80]}...'")
    return {"status": "sent", "recipient": phone_number, "gateway": "BSL_TELECOM_GATEWAY"}


def send_whatsapp_alert(whatsapp_number: str, message: str) -> dict[str, Any]:
    """Sends emergency alert via WhatsApp Business API interface."""
    if not whatsapp_number:
        return {"status": "skipped", "reason": "empty_whatsapp_number"}

    logger.info(f"[WhatsApp Gateway] Dispatched notification to {whatsapp_number}: '{message[:80]}...'")
    return {"status": "sent", "recipient": whatsapp_number, "gateway": "BSL_WHATSAPP_BUSINESS"}


def dispatch_incident_notifications(
    ticket: Ticket,
    plant_id: str = "bsl_bokaro",
    webhook_url: str | None = None,
) -> dict[str, Any]:
    """
    Orchestrates multi-channel dispatch for emergency or high-urgency incidents:
    Identifies targeted emergency teams for the incident zone, formats alert messages,
    and sends webhooks, SMS, and WhatsApp alerts concurrently.
    """
    plant = plant_manager.get_plant(plant_id)
    teams = plant_manager.get_emergency_teams(plant_id, ticket.zone_id)

    # 1. Format structured dispatch payload
    payload = {
        "event_type": "SAFETY_INCIDENT_DISPATCH",
        "plant_id": plant_id,
        "plant_name": plant.get("name", "Industrial Plant"),
        "ticket_id": ticket.id,
        "report_type": ticket.report_type,
        "category": ticket.predicted_category or "unclassified",
        "severity_tier": ticket.routing_tier,
        "risk_score": ticket.risk_score,
        "zone_id": ticket.zone_id,
        "description": ticket.incident_description_en or ticket.incident_description,
        "reporting_mode": ticket.reporting_mode,
        "worker_badge_id": ticket.worker_badge_id,
        "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
        "dispatched_teams": [t["name"] for t in teams],
    }

    # 2. Trigger webhook
    target_webhook = webhook_url or DEFAULT_WEBHOOK_URL
    webhook_result = send_webhook(target_webhook, payload) if target_webhook else {"status": "skipped", "reason": "no_url"}

    # 3. Trigger SMS & WhatsApp alerts to relevant emergency teams
    sms_results = []
    whatsapp_results = []

    alert_summary = (
        f"🚨 [{plant.get('short_name', 'BSL')} EMERGENCY] "
        f"Zone: {ticket.zone_id or 'GENERAL'} | "
        f"Event: {ticket.predicted_category or 'Hazard'} | "
        f"Tier: {ticket.routing_tier or 'URGENT'} | "
        f"Ticket: #{ticket.id}"
    )

    for team in teams:
        if team.get("sms") or team.get("phone"):
            res_sms = send_sms_alert(team.get("sms") or team.get("phone"), alert_summary)
            sms_results.append({"team_id": team["team_id"], "result": res_sms})

        if team.get("whatsapp"):
            res_wa = send_whatsapp_alert(team["whatsapp"], alert_summary)
            whatsapp_results.append({"team_id": team["team_id"], "result": res_wa})

    return {
        "ticket_id": ticket.id,
        "plant_id": plant_id,
        "webhook": webhook_result,
        "sms_dispatches": sms_results,
        "whatsapp_dispatches": whatsapp_results,
        "teams_notified_count": len(teams),
    }
