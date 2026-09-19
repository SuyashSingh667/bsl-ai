import json
import math
from pathlib import Path

BASE_DIR = Path(__file__).parent


def load_json(name):
    with open(BASE_DIR / name) as f:
        return json.load(f)


def distance(a, b):
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def get_hazard_bands_config():
    return load_json("hazard_bands.json")


def save_hazard_bands_config(bands_dict: dict):
    cfg = load_json("hazard_bands.json")
    cfg["bands"].update(bands_dict)
    with open(BASE_DIR / "hazard_bands.json", "w") as f:
        json.dump(cfg, f, indent=2)
    return cfg


def estimate_impact(incident_zone_id, incident_type, occupancy_period="day", zones=None, hazard_config=None, plant_id=None):
    if zones is None:
        try:
            from app.services.plant_manager import get_plant_zones
            zones = get_plant_zones(plant_id or "bsl_bokaro")
        except Exception:
            zones = load_json("zones.json")["zones"]
    hazard_config = hazard_config or load_json("hazard_bands.json")

    if incident_type in hazard_config["not_applicable"]:
        return {
            "applicable": False,
            "footprint_type": "indicative_footprint_unvalidated",
            "reason": f"{incident_type} has no spatial impact model",
        }

    band = hazard_config["bands"].get(incident_type)
    if band is None:
        return {
            "applicable": False,
            "footprint_type": "indicative_footprint_unvalidated",
            "reason": f"no hazard band configured for '{incident_type}'",
        }

    zones_by_id = {z["zone_id"]: z for z in zones}
    origin = zones_by_id.get(incident_zone_id)
    if origin is None:
        raise ValueError(f"unknown zone_id: {incident_zone_id}")

    affected = []
    persons_low = 0.0
    persons_high = 0.0
    civilian_alert = False

    for zone in zones:
        if zone["zone_id"] == incident_zone_id:
            edge_distance = -zone["footprint_radius_m"]
        else:
            edge_distance = distance(origin["centroid"], zone["centroid"]) - zone["footprint_radius_m"]

        if edge_distance <= band["primary_m"]:
            zone_band = "primary"
            harm_prob = band["primary_harm_prob"]
        elif edge_distance <= band["secondary_m"]:
            zone_band = "secondary"
            harm_prob = band["secondary_harm_prob"]
        else:
            continue

        entry = {
            "zone_id": zone["zone_id"],
            "name": zone["name"],
            "band": zone_band,
            "distance_m": round(max(edge_distance, 0), 1),
        }

        occupancy = zone["occupancy"].get(occupancy_period) if zone["occupancy"] else None
        if occupancy is None:
            entry["occupancy_modeled"] = False
            if zone["category"] == "civilian":
                civilian_alert = True
        else:
            expected = occupancy * harm_prob
            entry["occupancy_modeled"] = True
            entry["estimated_persons_at_risk_range"] = [round(expected * 0.7, 1), round(expected * 1.3, 1)]
            persons_low += expected * 0.7
            persons_high += expected * 1.3

        affected.append(entry)

    return {
        "applicable": True,
        "footprint_type": "indicative_footprint_unvalidated",
        "footprint_label": "Indicative Footprint (Advisory / Unvalidated)",
        "model_version": hazard_config.get("model_version", "tier1-indicative-v1"),
        "incident_zone": incident_zone_id,
        "incident_type": incident_type,
        "primary_radius_m": band["primary_m"],
        "secondary_radius_m": band["secondary_m"],
        "occupancy_period": occupancy_period,
        "affected_zones": affected,
        "estimated_persons_at_risk_range": [round(persons_low), round(persons_high)],
        "civilian_exposure_alert": civilian_alert,
        "disclaimer": (
            "Indicative footprint for triage awareness only. Not a certified consequence analysis "
            "or blast-radius simulation. Requires safety-engineer physical verification before "
            "use in regulatory or emergency response zoning."
        ),
    }


if __name__ == "__main__":
    result = estimate_impact("GHS", "gas_leak")
    print(json.dumps(result, indent=2))
