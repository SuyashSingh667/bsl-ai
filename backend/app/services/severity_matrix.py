"""
Transparent Rule-Based Industrial Severity Matrix for Bokaro Steel Limited (BSL).
Formula: Risk Score = min(1.0, max(Baseline, Hazard Base * Likelihood * Consequence * Proximity))

All ML and AI predictions are strictly tagged as 'Advisory'.
The final operational score is deterministic, auditable, and configurable per plant.
"""

from __future__ import annotations
from typing import Any

# Statutory Hazard Base Severities (Bokaro Steel Limited Master Safety Matrix 2024.1)
PLANT_HAZARD_BASE: dict[str, float] = {
    "molten_metal_spill": 0.85,
    "confined_space_emergency": 0.85,
    "gas_leak": 0.80,
    "fire": 0.70,
    "crane_lifting_failure": 0.65,
    "chemical_spill": 0.60,
    "electrical_hazard": 0.55,
    "vehicle_traffic_incident": 0.50,
    "mechanical_failure": 0.40,
    "slip_fall": 0.20,
    "ppe_violation": 0.15,
}

# Critical plant infrastructure zones requiring proximity multipliers
HIGH_RISK_ASSET_ZONES: dict[str, dict[str, Any]] = {
    "BF1": {"multiplier": 1.25, "reason": "Blast Furnace 1 (CO Gas & Molten Metal Reservoir)"},
    "BF2": {"multiplier": 1.25, "reason": "Blast Furnace 2 (High CO Gas Network)"},
    "COB": {"multiplier": 1.25, "reason": "Coke Oven Battery (Toxic & Explosive Gas By-Products)"},
    "SMS": {"multiplier": 1.20, "reason": "Steel Melting Shop (Converter & Liquid Steel Ladles)"},
    "GHS": {"multiplier": 1.25, "reason": "Central Gas Holder Station (Volatile Gas Storage)"},
    "OXY": {"multiplier": 1.20, "reason": "Tonnage Oxygen Plant (High-Pressure Flammability Booster)"},
}


def calculate_severity_matrix(
    category: str | None,
    observation_mode: str | None = None,
    is_hazard_active: bool | None = None,
    people_exposed_count: int | None = None,
    has_casualties: bool = False,
    zone_id: str | None = None,
    impact: dict[str, Any] | None = None,
    ml_category_confidence: float | None = None,
    ml_vision_event: str | None = None,
    ml_vision_confidence: float | None = None,
) -> tuple[float, dict[str, Any]]:
    """
    Computes a transparent, auditable industrial safety score from explicit physical factors.
    Returns: (score, contributing_factors_breakdown)
    """
    cat_clean = (category or "mechanical_failure").lower()
    base_severity = PLANT_HAZARD_BASE.get(cat_clean, 0.40)

    # 1. Likelihood Factor (1.00 - 1.25)
    if is_hazard_active is True or observation_mode in ["visual_confirmed", "both_seen_and_smelled"]:
        likelihood_multiplier = 1.25
        likelihood_reason = "Active ongoing release or direct verified physical observation"
    elif observation_mode == "odor_only":
        likelihood_multiplier = 1.10
        likelihood_reason = "Vapor/odor detected without visible breach"
    elif is_hazard_active is False:
        likelihood_multiplier = 1.00
        likelihood_reason = "Hazard stopped or contained"
    else:
        likelihood_multiplier = 1.05
        likelihood_reason = "Status pending physical inspection"

    # 2. Consequence Factor (1.00 - 1.40)
    count = people_exposed_count or 0
    if impact and impact.get("applicable"):
        _, hi = impact.get("estimated_persons_at_risk_range", (0, 0))
        count = max(count, hi)

    if has_casualties:
        consequence_multiplier = 1.40
        consequence_reason = "Personnel casualty, unconsciousness, or acute trauma reported"
    elif count >= 10:
        consequence_multiplier = 1.30
        consequence_reason = f"High workforce exposure: {count} workers in danger zone"
    elif count >= 3:
        consequence_multiplier = 1.15
        consequence_reason = f"Moderate workforce exposure: {count} workers present"
    else:
        consequence_multiplier = 1.00
        consequence_reason = "Unmanned sector or zero immediate personnel in blast radius"

    # 3. Proximity to Critical Plant Assets (1.00 - 1.25)
    zid = (zone_id or "").upper().strip()
    if zid in HIGH_RISK_ASSET_ZONES:
        asset_multiplier = HIGH_RISK_ASSET_ZONES[zid]["multiplier"]
        asset_reason = HIGH_RISK_ASSET_ZONES[zid]["reason"]
    elif impact and impact.get("applicable") and impact.get("civilian_exposure_alert"):
        asset_multiplier = 1.25
        asset_reason = "Perimeter breach threatening civilian/perimeter plant boundary"
    else:
        asset_multiplier = 1.00
        asset_reason = f"Standard operating perimeter (Zone {zone_id or 'General'})"

    # 4. Deterministic Multiplicative Product
    raw_computed = base_severity * likelihood_multiplier * consequence_multiplier * asset_multiplier
    
    # Invariant: Score can never be lower than the statutory baseline severity floor
    final_score = round(min(1.0, max(base_severity, raw_computed)), 2)

    # 5. ML Advisory Container (Explicitly labeled advisory)
    ml_advisory = {
        "role": "ADVISORY ONLY",
        "notice": "ML predictions assist category identification; statutory score is governed by plant matrix rules.",
        "predicted_category": category,
        "category_confidence": round(ml_category_confidence, 2) if ml_category_confidence else None,
        "vision_event_detected": ml_vision_event,
        "vision_confidence": round(ml_vision_confidence, 2) if ml_vision_confidence else None,
    }

    contributing_factors = {
        "matrix_version": "BSL-SEV-MATRIX-2024.1",
        "hazard_category": cat_clean,
        "hazard_base_severity": base_severity,
        "likelihood": {
            "multiplier": likelihood_multiplier,
            "reason": likelihood_reason,
        },
        "consequence": {
            "multiplier": consequence_multiplier,
            "reason": consequence_reason,
            "exposed_count": count,
        },
        "asset_proximity": {
            "multiplier": asset_multiplier,
            "reason": asset_reason,
            "zone_id": zone_id,
        },
        "formula": "min(1.0, max(Base, Base * Likelihood * Consequence * Proximity))",
        "raw_product": round(raw_computed, 3),
        "calculated_risk_score": final_score,
        "ml_advisory": ml_advisory,
    }

    return final_score, contributing_factors
