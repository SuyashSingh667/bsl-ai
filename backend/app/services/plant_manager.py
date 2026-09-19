"""
Data-Driven Plant Layout and Configuration Manager.
Loads plant map, zones, critical assets, gas pipelines, transformers,
and emergency teams dynamically per tenant from JSON or admin API.
Replaces all hardcoded plant names across the platform.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.config import BACKEND_DIR, PROJECT_ROOT

logger = logging.getLogger(__name__)

# Primary storage for tenant plant configurations
PLANTS_DIR = BACKEND_DIR / "plants"
if not PLANTS_DIR.exists():
    PLANTS_DIR = PROJECT_ROOT / "plants"
PLANTS_DIR.mkdir(parents=True, exist_ok=True)

_PLANTS_CACHE: dict[str, dict[str, Any]] = {}
DEFAULT_PLANT_ID = "bsl_bokaro"


def _load_plant_from_disk(plant_id: str) -> dict[str, Any] | None:
    path = PLANTS_DIR / f"{plant_id}.json"
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as fp:
            data = json.load(fp)
            return data
    except Exception as exc:
        logger.error(f"Failed to parse plant config {path}: {exc}")
        return None


def get_plant(plant_id: str = DEFAULT_PLANT_ID) -> dict[str, Any]:
    """Retrieves plant configuration by plant_id with memory caching."""
    if plant_id in _PLANTS_CACHE:
        return _PLANTS_CACHE[plant_id]

    data = _load_plant_from_disk(plant_id)
    if data is None:
        if plant_id != DEFAULT_PLANT_ID:
            logger.warning(f"Plant {plant_id} not found, falling back to {DEFAULT_PLANT_ID}")
            return get_plant(DEFAULT_PLANT_ID)
        # Fallback minimal schema if even bsl_bokaro is missing
        data = {
            "plant_id": DEFAULT_PLANT_ID,
            "name": "Heavy Industry Manufacturing Plant",
            "short_name": "PLANT",
            "location": "Industrial Complex",
            "emergency_hotline": "+910000000000",
            "zones": [],
            "emergency_teams": [],
            "gas_pipelines": [],
            "transformers": [],
            "critical_assets": [],
        }

    _PLANTS_CACHE[plant_id] = data
    return data


def list_plants() -> list[dict[str, Any]]:
    """Lists summary of all configured plants available on the node."""
    results = []
    for file_path in sorted(PLANTS_DIR.glob("*.json")):
        plant_id = file_path.stem
        cfg = get_plant(plant_id)
        results.append({
            "plant_id": cfg.get("plant_id", plant_id),
            "name": cfg.get("name", plant_id),
            "short_name": cfg.get("short_name", plant_id.upper()),
            "location": cfg.get("location", ""),
            "emergency_hotline": cfg.get("emergency_hotline", ""),
            "zone_count": len(cfg.get("zones", [])),
            "emergency_team_count": len(cfg.get("emergency_teams", [])),
            "data_retention_days": cfg.get("data_retention_days", 180),
        })
    return results


def register_or_update_plant(config_dict: dict[str, Any]) -> dict[str, Any]:
    """Registers or updates a plant configuration on disk and updates cache."""
    plant_id = config_dict.get("plant_id")
    if not plant_id:
        raise ValueError("Missing 'plant_id' in plant configuration")

    # Sanitize plant_id
    plant_id = "".join(c for c in plant_id.lower() if c.isalnum() or c in ("_", "-"))
    config_dict["plant_id"] = plant_id

    out_file = PLANTS_DIR / f"{plant_id}.json"
    with open(out_file, "w", encoding="utf-8") as fp:
        json.dump(config_dict, fp, indent=2, ensure_ascii=False)

    _PLANTS_CACHE[plant_id] = config_dict
    logger.info(f"Successfully registered data-driven plant layout for {plant_id}")
    return config_dict


def get_plant_zones(plant_id: str = DEFAULT_PLANT_ID) -> list[dict[str, Any]]:
    """Returns zones for specified plant."""
    plant = get_plant(plant_id)
    return plant.get("zones", [])


def get_emergency_teams(plant_id: str = DEFAULT_PLANT_ID, zone_id: str | None = None) -> list[dict[str, Any]]:
    """Returns relevant emergency teams for plant and optional zone."""
    plant = get_plant(plant_id)
    teams = plant.get("emergency_teams", [])
    if not zone_id:
        return teams
    # Filter teams covering ALL or this specific zone
    filtered = []
    for team in teams:
        cov = team.get("coverage_zones", ["ALL"])
        if "ALL" in cov or zone_id in cov:
            filtered.append(team)
    return filtered or teams


def get_critical_assets(plant_id: str = DEFAULT_PLANT_ID, zone_id: str | None = None) -> list[dict[str, Any]]:
    plant = get_plant(plant_id)
    assets = plant.get("critical_assets", [])
    if not zone_id:
        return assets
    return [a for a in assets if a.get("zone_id") == zone_id]


def format_plant_prompt(template_str: str, plant_id: str = DEFAULT_PLANT_ID) -> str:
    """Interpolates plant-specific terminology and names into templates."""
    plant = get_plant(plant_id)
    return template_str.format(
        plant_name=plant.get("name", "Industrial Plant"),
        plant_short=plant.get("short_name", "PLANT"),
        hotline=plant.get("emergency_hotline", "Control Room"),
        location=plant.get("location", ""),
    )
