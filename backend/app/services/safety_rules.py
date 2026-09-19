"""
Safety-Critical Invariant Engine for Industrial Plant Operations.

CORE INVARIANTS:
1. Human Report Always Wins:
   No AI model, classifier, or vision system may downgrade a human-reported severity,
   lower a computed risk score, or cancel/delay an emergency dispatch.
2. Escalate-Only Monotonicity:
   Incident severity and authority tiers can only transition monotonically UPWARD.
3. Irreversible Dispatch:
   Once an emergency or dispatch order is initiated, it can never be cancelled or delayed by AI.
"""

from __future__ import annotations
from typing import Any

TIER_RANKS = {
    "safety_team_queue": 1,
    "shift_supervisor": 2,
    "plant_safety_officer": 3,
    "emergency_authority": 4,
}

RANK_TO_TIER = {v: k for k, v in TIER_RANKS.items()}


def get_tier_rank(tier: str | None) -> int:
    if not tier:
        return 1
    return TIER_RANKS.get(tier.lower(), 1)


def resolve_highest_tier(current_tier: str | None, proposed_tier: str | None) -> str:
    """Returns the higher of two authority tiers (escalate-only)."""
    rank_curr = get_tier_rank(current_tier)
    rank_prop = get_tier_rank(proposed_tier)
    return RANK_TO_TIER[max(rank_curr, rank_prop)]


def apply_safety_invariants(
    human_report_type: str,
    current_tier: str | None,
    current_risk_score: float | None,
    proposed_tier: str | None,
    proposed_risk_score: float | None,
    has_dispatched: bool = False,
    is_acute_emergency: bool = False,
) -> dict[str, Any]:
    """
    Central authoritative safety invariant resolver.
    
    Guarantees:
    - If human selected 'emergency' or acute emergency is flagged, tier is locked to 'emergency_authority'.
    - Tier transitions are strictly monotonic (max(current, proposed)).
    - Risk scores are strictly non-decreasing (max(current, proposed)).
    - Dispatches once active can never be revoked or delayed.
    """
    is_human_emergency = (human_report_type or "").lower() == "emergency"
    
    # 1. Tier Resolution (Escalate-only)
    if is_human_emergency or is_acute_emergency:
        final_tier = "emergency_authority"
    else:
        final_tier = resolve_highest_tier(current_tier, proposed_tier)

    # 2. Risk Score Resolution (Non-decreasing floor)
    curr_score = current_risk_score if current_risk_score is not None else 0.0
    prop_score = proposed_risk_score if proposed_risk_score is not None else 0.0
    
    if is_human_emergency:
        # Human reported emergency guarantees at least high severity floor (0.75+)
        final_risk_score = round(max(0.75, curr_score, prop_score), 2)
    else:
        final_risk_score = round(max(curr_score, prop_score), 2)

    # 3. Dispatch Status (Irreversible once triggered)
    is_emergency_tier = final_tier == "emergency_authority"
    dispatch_active = has_dispatched or is_emergency_tier or (final_risk_score >= 0.70)

    # 4. Invariant audit log
    downgrade_prevented = (
        (proposed_tier and get_tier_rank(proposed_tier) < get_tier_rank(current_tier))
        or (proposed_risk_score is not None and proposed_risk_score < curr_score)
    )

    return {
        "routing_tier": final_tier,
        "risk_score": final_risk_score,
        "dispatch_active": dispatch_active,
        "is_emergency": is_emergency_tier,
        "downgrade_prevented": downgrade_prevented,
        "rule_audit": {
            "human_report_type": human_report_type,
            "tier_rank": get_tier_rank(final_tier),
            "monotonic_escalation_enforced": True,
        },
    }
