from spatial_impact.engine import estimate_impact

NOT_APPLICABLE_CATEGORIES = {"slip_fall", "ppe_violation"}


def assess(zone_id: str | None, category: str | None, plant_id: str | None = None) -> dict | None:
    if not zone_id or not category or category in NOT_APPLICABLE_CATEGORIES:
        return None
    try:
        return estimate_impact(zone_id, category, plant_id=plant_id)
    except ValueError:
        return None
