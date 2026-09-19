"""
Analytics, Safety Trends, and Culture Engagement Router.
Provides:
  1. Repeat hazard trends (zone, shift, equipment hotspots, and closure SLA).
  2. Positive-reinforcement culture metrics (zero worker surveillance).
  3. Closed-loop report lifecycle tracking by ticket ID or anonymous tracking code.
  4. Bilingual in-app 'What Happens to My Report' explainer content.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import CultureMetricsOut, IncidentTrackerOut, OperationalMetricsOut, SafetyTrendsOut
from app.services import operational_metrics, trend_analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/operational-metrics", response_model=OperationalMetricsOut)
def get_operational_metrics_endpoint(
    plant_id: str = "bsl_bokaro",
    window_days: int | None = None,
    db: Session = Depends(get_db),
):
    """
    Phase 8 — Seven key safety-operations KPIs:
    time_to_first_dispatch, time_to_acknowledge, reports_per_100_workers_per_month,
    near_miss_closure_time, transcription_confidence, pct_reports_completed_offline,
    false_dispatch_rate.

    window_days defaults to BSL_METRICS_WINDOW_DAYS env var (default 30).
    All None values indicate insufficient data; raw counts are included for transparency.
    """
    return operational_metrics.get_operational_metrics(plant_id, db, window_days)


@router.get("/trends", response_model=SafetyTrendsOut)
def get_safety_trends_endpoint(
    plant_id: str = "bsl_bokaro",
    db: Session = Depends(get_db),
):
    """Aggregates repeat hazard patterns and closure turnaround SLA."""
    return trend_analytics.get_safety_trends(plant_id, db)


@router.get("/culture", response_model=CultureMetricsOut)
def get_culture_metrics_endpoint(
    plant_id: str = "bsl_bokaro",
    db: Session = Depends(get_db),
):
    """Computes positive-reinforcement community safety metrics without surveillance."""
    return trend_analytics.get_culture_metrics(plant_id, db)


@router.get("/tracker/{identifier}", response_model=IncidentTrackerOut)
def track_report_status(
    identifier: str,
    db: Session = Depends(get_db),
):
    """
    Closes the loop for frontline workers:
    Tracks report lifecycle by ticket_id or anonymous tracking code.
    """
    tracker = trend_analytics.get_lifecycle_tracker(identifier, db)
    if not tracker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Report with code or ID '{identifier}' was not found.",
        )
    return tracker


@router.get("/explainer")
def get_report_explainer():
    """Returns bilingual step-by-step guidance on what happens after submitting a safety report."""
    return {
        "en": {
            "title": "What Happens to Your Safety Report?",
            "commitment": "Zero-Blame Guarantee: Reporting hazards protects your coworkers and is never penalized.",
            "steps": [
                {
                    "step": 1,
                    "title": "Received & Timestamped",
                    "description": "Your voice note or report is assigned an ID or anonymous code and securely logged.",
                    "status_badge": "RECEIVED",
                },
                {
                    "step": 2,
                    "title": "Safety Officer Review & SOP Citations",
                    "description": "AI correlates factory blueprints and quotes official plant safety procedures without human delay.",
                    "status_badge": "UNDER REVIEW",
                },
                {
                    "step": 3,
                    "title": "Corrective Action Assigned",
                    "description": "The appropriate maintenance squad or shift supervisor is dispatched to isolate the hazard.",
                    "status_badge": "ACTION ASSIGNED",
                },
                {
                    "step": 4,
                    "title": "Hazard Fixed & Verified",
                    "description": "Work is completed, closure evidence is verified, and the ticket is officially closed.",
                    "status_badge": "HAZARD RESOLVED",
                },
            ],
        },
        "hi": {
            "title": "आपकी सुरक्षा रिपोर्ट पर क्या कार्रवाई होती है?",
            "commitment": "सुरक्षा और गोपनीयता की गारंटी: खतरे की सूचना देना आपकी और साथियों की सुरक्षा करता है, कोई दंडात्मक कार्रवाई नहीं होती।",
            "steps": [
                {
                    "step": 1,
                    "title": "रिपोर्ट दर्ज और सुरक्षित",
                    "description": "आपकी आवाज या टेक्स्ट रिपोर्ट को एक गुप्त ट्रैकिंग कोड दिया जाता है और समय दर्ज किया जाता है।",
                    "status_badge": "प्राप्त हुई",
                },
                {
                    "step": 2,
                    "title": "सुरक्षा अधिकारी जांच और SOP मिलान",
                    "description": "सिस्टम तुरंत प्रासंगिक फैक्ट्री सुरक्षा नियमों (SOP) को निकालकर अधिकारियों को सूचित करता है।",
                    "status_badge": "जांच जारी",
                },
                {
                    "step": 3,
                    "title": "सुधार कार्य और टीम आवंटन",
                    "description": "खतरे को समाप्त करने के लिए संबंधित मेंटेनेंस टीम या शिफ्ट सुपरवाइजर को कार्य सौंपा जाता है।",
                    "status_badge": "कार्य आवंटित",
                },
                {
                    "step": 4,
                    "title": "खतरा समाप्त और पुष्टि",
                    "description": "मरम्मत कार्य पूर्ण होने के बाद प्रमाण की पुष्टि कर रिपोर्ट बंद की जाती है।",
                    "status_badge": "खतरा हल हुआ",
                },
            ],
        },
    }
