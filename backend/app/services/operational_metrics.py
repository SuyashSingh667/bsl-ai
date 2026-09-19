"""
Phase 8 — Operational Metrics Service.

Aggregates the seven safety-operations KPIs requested:
  1. time_to_first_dispatch   — seconds from ticket.created_at → ticket.dispatched_at
  2. time_to_acknowledge       — seconds from ticket.dispatched_at → ticket.acknowledged_at
  3. reports_per_100_workers_per_month — requires plant_headcount in plant config
  4. near_miss_closure_time    — hours (ticket.closure_time_hours, already set on closure)
  5. transcription_confidence  — ticket.language_confidence
  6. pct_reports_completed_offline — ticket.completed_offline flag (new, Phase 8)
  7. false_dispatch_rate        — ticket.false_alarm flag (new, Phase 8)

All raw counts are returned alongside averages so callers can verify correctness.
No invented statistics — if there is insufficient data, the metric is None and a
data_note explains why.

Config flags (all via environment variables):
  BSL_DISPATCH_ACK_TIMEOUT_SECONDS  (default 60) — shown in output for transparency
  BSL_METRICS_WINDOW_DAYS           (default 30)  — rolling window for aggregation
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Ticket
from app.services import plant_manager

ACK_SLA_SECONDS: int = int(os.getenv("BSL_DISPATCH_ACK_TIMEOUT_SECONDS", "60"))
METRICS_WINDOW_DAYS: int = int(os.getenv("BSL_METRICS_WINDOW_DAYS", "30"))
_DATA_NOTE = (
    "Metrics computed from real tickets in the configured time window. "
    "None values indicate insufficient data (< 1 observation). "
    "reports_per_100_workers_per_month requires plant_headcount in plant config."
)


def _safe_avg(values: list[float]) -> float | None:
    return sum(values) / len(values) if values else None


def get_operational_metrics(
    plant_id: str,
    db: Session,
    window_days: int | None = None,
) -> dict[str, Any]:
    """
    Returns a dict matching OperationalMetricsOut.
    window_days defaults to BSL_METRICS_WINDOW_DAYS env var.
    """
    window = window_days if window_days is not None else METRICS_WINDOW_DAYS
    since = datetime.now(timezone.utc) - timedelta(days=window)

    # ── fetch all tickets in window for this plant ───────────────────────────
    stmt = select(Ticket).where(
        Ticket.plant_id == plant_id,
        Ticket.created_at >= since,
    )
    tickets: list[Ticket] = list(db.scalars(stmt).all())

    total_tickets = len(tickets)
    emergency_tickets = sum(1 for t in tickets if t.report_type == "emergency")

    # ── 1. time_to_first_dispatch ────────────────────────────────────────────
    dispatch_deltas: list[float] = []
    dispatched_count = 0
    for t in tickets:
        if t.dispatched_at and t.created_at:
            created = t.created_at
            dispatched = t.dispatched_at
            # Ensure both are timezone-aware
            if created.tzinfo is None:
                created = created.replace(tzinfo=timezone.utc)
            if dispatched.tzinfo is None:
                dispatched = dispatched.replace(tzinfo=timezone.utc)
            delta = (dispatched - created).total_seconds()
            if delta >= 0:
                dispatch_deltas.append(delta)
                dispatched_count += 1

    # ── 2. time_to_acknowledge ───────────────────────────────────────────────
    ack_deltas: list[float] = []
    acknowledged_count = 0
    for t in tickets:
        if t.acknowledged_at and t.dispatched_at:
            dispatched = t.dispatched_at
            acked = t.acknowledged_at
            if dispatched.tzinfo is None:
                dispatched = dispatched.replace(tzinfo=timezone.utc)
            if acked.tzinfo is None:
                acked = acked.replace(tzinfo=timezone.utc)
            delta = (acked - dispatched).total_seconds()
            if delta >= 0:
                ack_deltas.append(delta)
                acknowledged_count += 1

    # ── 3. reports_per_100_workers_per_month ─────────────────────────────────
    plant_cfg = plant_manager.get_plant(plant_id)
    plant_headcount: int | None = plant_cfg.get("plant_headcount")
    reports_per_100: float | None = None
    if plant_headcount and plant_headcount > 0 and window > 0:
        months_in_window = window / 30.0
        reports_per_100 = round(
            (total_tickets / plant_headcount) * 100 / months_in_window, 2
        )

    # ── 4. near_miss_closure_time ────────────────────────────────────────────
    closure_times: list[float] = []
    for t in tickets:
        if t.closure_time_hours is not None and t.closure_time_hours >= 0:
            closure_times.append(t.closure_time_hours)

    # ── 5. transcription_confidence ──────────────────────────────────────────
    confidences: list[float] = []
    for t in tickets:
        if t.language_confidence is not None:
            confidences.append(t.language_confidence)

    # ── 6. pct_reports_completed_offline ─────────────────────────────────────
    offline_count = sum(1 for t in tickets if t.completed_offline)
    pct_offline: float | None = None
    if total_tickets > 0:
        pct_offline = round(100.0 * offline_count / total_tickets, 1)

    # ── 7. false_dispatch_rate ────────────────────────────────────────────────
    false_alarm_count = sum(1 for t in tickets if t.false_alarm)
    false_dispatch_rate: float | None = None
    if dispatched_count > 0:
        false_dispatch_rate = round(100.0 * false_alarm_count / dispatched_count, 1)

    return {
        "plant_id": plant_id,
        "window_days": window,
        "total_tickets": total_tickets,
        "emergency_tickets": emergency_tickets,
        "avg_time_to_first_dispatch_s": _safe_avg(dispatch_deltas),
        "avg_time_to_acknowledge_s": _safe_avg(ack_deltas),
        "avg_near_miss_closure_time_h": _safe_avg(closure_times),
        "avg_transcription_confidence": _safe_avg(confidences),
        "pct_reports_completed_offline": pct_offline,
        "false_dispatch_rate": false_dispatch_rate,
        "reports_per_100_workers_per_month": reports_per_100,
        "dispatched_count": dispatched_count,
        "acknowledged_count": acknowledged_count,
        "offline_count": offline_count,
        "false_alarm_count": false_alarm_count,
        "ack_sla_seconds": ACK_SLA_SECONDS,
        "data_note": _DATA_NOTE,
    }
