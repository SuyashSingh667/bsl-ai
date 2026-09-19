from spatial_impact.engine import estimate_impact

NOT_APPLICABLE_CATEGORIES = {"slip_fall", "ppe_violation"}


def assess(zone_id: str | None, category: str | None) -> dict | None:
    if not zone_id or not category or category in NOT_APPLICABLE_CATEGORIES:
        return None
    try:
        return estimate_impact(zone_id, category)
    except ValueError:
        return None
