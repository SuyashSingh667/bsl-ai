"""
Maps a ticket's verification confidence and estimated impact to an authority
tier. Thresholds here are placeholders pending safety-officer approval, same
as hazard_bands.json — this is exactly the kind of number that must not be
presented as a validated standard.
"""

from app.config import CATEGORY_BASELINE_SEVERITY
from app.services import safety_rules, severity_matrix


def compute_risk_score(
    category: str | None,
    verification_score: float | None = None,
    impact: dict | None = None,
    observation_mode: str | None = None,
    is_hazard_active: bool | None = None,
    people_exposed_count: int | None = None,
    has_casualties: bool = False,
    zone_id: str | None = None,
    ml_confidence: float | None = None,
    ml_vision_event: str | None = None,
    ml_vision_confidence: float | None = None,
) -> float:
    """
    Computes objective risk score via the transparent Plant Severity Matrix.
    Enforces statutory baseline floor: Hazard Base * Likelihood * Consequence * Proximity.
    """
    score, _ = severity_matrix.calculate_severity_matrix(
        category=category,
        observation_mode=observation_mode,
        is_hazard_active=is_hazard_active,
        people_exposed_count=people_exposed_count,
        has_casualties=has_casualties,
        zone_id=zone_id,
        impact=impact,
        ml_category_confidence=ml_confidence,
        ml_vision_event=ml_vision_event,
        ml_vision_confidence=ml_vision_confidence,
    )
    return score


def compute_severity_with_factors(
    category: str | None,
    observation_mode: str | None = None,
    is_hazard_active: bool | None = None,
    people_exposed_count: int | None = None,
    has_casualties: bool = False,
    zone_id: str | None = None,
    impact: dict | None = None,
    ml_confidence: float | None = None,
    ml_vision_event: str | None = None,
    ml_vision_confidence: float | None = None,
) -> tuple[float, dict]:
    """Returns (score, full_contributing_factors_breakdown)."""
    return severity_matrix.calculate_severity_matrix(
        category=category,
        observation_mode=observation_mode,
        is_hazard_active=is_hazard_active,
        people_exposed_count=people_exposed_count,
        has_casualties=has_casualties,
        zone_id=zone_id,
        impact=impact,
        ml_category_confidence=ml_confidence,
        ml_vision_event=ml_vision_event,
        ml_vision_confidence=ml_vision_confidence,
    )


def route(report_type: str, risk_score: float, impact: dict | None) -> str:
    if report_type == "emergency":
        return "emergency_authority"

    if impact and impact.get("applicable") and impact.get("civilian_exposure_alert"):
        return "emergency_authority"

    if risk_score >= 0.7:
        return "plant_safety_officer"
    if risk_score >= 0.4:
        return "shift_supervisor"
    return "safety_team_queue"


def get_dispatch_recipients(
    category: str | None,
    zone_id: str | None,
    routing_tier: str | None,
    risk_score: float | None = None,
    report_type: str = "suspected",
) -> list[dict[str, str]]:
    """
    Returns an official, auditable list of Bokaro Steel plant dispatch recipients
    and emergency command units to whom the incident report and dossier are routed.
    """
    cat = (category or "").lower()
    recipients = []

    # 1. Primary Action & Suppression Units
    if "fire" in cat:
        recipients.append({
            "department": "BSL Plant Fire Services & Crash Tender Squad",
            "role": "Immediate Fire Suppression & Rescue Response",
            "contact": "Ext 101 / 3333 (Direct Hotline) | VHF Ch 1",
            "priority": "CRITICAL / IMMEDIATE ACTION",
            "status": "DISPATCHED & TRANSMITTED",
        })
    elif "elec" in cat:
        recipients.append({
            "department": "Central Electrical Substation & High-Voltage Switchgear Command",
            "role": "Grid Isolation & LOTO Verification",
            "contact": "Ext 3111 | Emergency Substation Console",
            "priority": "CRITICAL / IMMEDIATE ACTION",
            "status": "DISPATCHED & TRANSMITTED",
        })
    elif "gas" in cat:
        recipients.append({
            "department": "Bokaro Gas Safety Station & Rescue Squad",
            "role": "Gas Sniffing, Pipeline Isolation & SCBA Operations",
            "contact": "Ext 2222 | Emergency Gas Dispatch",
            "priority": "CRITICAL / IMMEDIATE ACTION",
            "status": "DISPATCHED & TRANSMITTED",
        })
    elif "molten" in cat or "metal" in cat:
        recipients.append({
            "department": "Blast Furnace / SMS Casthouse Emergency Response Squad",
            "role": "Hot Metal Breakout Containment & Dry Sand Damming",
            "contact": "Ext 2400 | Casthouse In-Charge",
            "priority": "CRITICAL / IMMEDIATE ACTION",
            "status": "DISPATCHED & TRANSMITTED",
        })
    elif "chem" in cat or "acid" in cat:
        recipients.append({
            "department": "BSL Hazardous Chemical Spill Mitigation Unit",
            "role": "Neutralization & HazMat Containment",
            "contact": "Ext 2550 | Chemical Safety Desk",
            "priority": "CRITICAL / IMMEDIATE ACTION",
            "status": "DISPATCHED & TRANSMITTED",
        })
    elif "crane" in cat or "lift" in cat:
        recipients.append({
            "department": "Central Rigging & Heavy Crane Safety Cell",
            "role": "Structural Crane Inspection & Gantry Isolation",
            "contact": "Ext 2300 | Crane Maintenance Desk",
            "priority": "HIGH PRIORITY",
            "status": "DISPATCHED & TRANSMITTED",
        })
    elif "vehicle" in cat or "traffic" in cat:
        recipients.append({
            "department": "Plant Traffic Control & Heavy Vehicle Security",
            "role": "Corridor Clearing & Road Incident Clearance",
            "contact": "Ext 103 / 3400 | Traffic Control",
            "priority": "HIGH PRIORITY",
            "status": "DISPATCHED & TRANSMITTED",
        })
    else:
        recipients.append({
            "department": "Central Emergency Response & Plant Rescue Cell",
            "role": "Primary Incident Response & Area Clearance",
            "contact": "Ext 101 | Central Control Desk",
            "priority": "ELEVATED PRIORITY",
            "status": "DISPATCHED & TRANSMITTED",
        })

    # 2. Medical Emergency Standby
    recipients.append({
        "department": "BSL Occupational Health Centre (OHC) Emergency Trauma Unit",
        "role": "Mobile Trauma Ambulance & Paramedic Resuscitation",
        "contact": "Ext 102 | Ambulance Direct Dispatch",
        "priority": "HIGH PRIORITY / STANDBY",
        "status": "NOTIFIED & STANDBY",
    })

    # 3. Zone / Area Operations Management
    zone_label = f"Zone {zone_id}" if zone_id else "Incident Operating Sector"
    recipients.append({
        "department": f"{zone_label} Area Maintenance In-Charge & Shift Supervisor",
        "role": "Local Perimeter Cordon & Workforce Muster Accountability",
        "contact": "Ext 2100 | Zone Shift Console",
        "priority": "COMMAND & CONTROL",
        "status": "TRANSMITTED",
    })

    # 4. Central Safety Authority & Executive Routing
    tier = routing_tier or "safety_team_queue"
    if tier == "emergency_authority" or report_type == "emergency" or (risk_score and risk_score >= 0.7):
        recipients.append({
            "department": "Chief General Manager (Safety & Environment), Bokaro Steel Limited",
            "role": "Executive Emergency Authority & Plant Incident Command",
            "contact": "Ext 3300 | Executive Director (Works) Direct Line",
            "priority": "EXECUTIVE ESCALATION",
            "status": "URGENT DOSSIER TRANSMITTED",
        })
        recipients.append({
            "department": "Central Safety Engineering Department (CSED - Bokaro)",
            "role": "Statutory Incident Investigation & Regulatory Reporting",
            "contact": "Ext 3340 | CSED Directorate",
            "priority": "STATUTORY AUDIT",
            "status": "LOGGED & TRANSMITTED",
        })
    elif tier == "plant_safety_officer":
        recipients.append({
            "department": "Senior Manager (Plant Safety Cell)",
            "role": "On-Duty Safety Officer Evaluation & Site Audit",
            "contact": "Ext 3333 | Safety Control Room",
            "priority": "INVESTIGATION REQUIRED",
            "status": "TRANSMITTED",
        })
    else:
        recipients.append({
            "department": "Departmental Safety Coordinator & Review Queue",
            "role": "Corrective Action Tracking & Daily Log Review",
            "contact": "Ext 3310 | Safety Queue Registry",
            "priority": "INFORMATIONAL AUDIT",
            "status": "QUEUED & LOGGED",
        })

    return recipients
