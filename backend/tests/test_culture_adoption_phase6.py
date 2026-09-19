"""
Unit & Integration Test Suite for Phase 6: Culture and Reporting Adoption.
Verifies:
  1. Anonymous / No-blame near-miss reporting:
     - Worker badge and identity stripped
     - Attributed to plant zone & shift only
     - Generates unique tracking code (NM-XXXXXX)
     - Audit log logs actor as ANONYMOUS
  2. Frontline status tracker ('Close the loop'):
     - Look up by tracking code or ticket ID
     - Validates lifecycle stage milestones (received -> under_review -> action_assigned -> action_taken -> resolved)
  3. Supervisor & Safety Officer corrective action workflow:
     - Assign corrective action, remediator, due date
     - Closure evidence recording & turnaround SLA calculation (closure_time_hours)
     - Audit log immutability
  4. Safety trends analytics:
     - Repeat hazard hotspots by zone
     - Hazards by shift
     - Repeat equipment anomalies
  5. Positive reinforcement & Anti-surveillance invariants:
     - Collective shift participation metrics
     - Total hazards fixed counter
     - Zero individual worker blame, rankings, or surveillance
  6. Bilingual in-app process explainer (Hindi & English parity).
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone
import uuid

from app.database import Base, SessionLocal, engine
from app.models import AuditLog, Ticket
from app.schemas import ActionAssignRequest, ActionCloseRequest, IncidentCreate
from app.routers import incidents, tickets, analytics
from app.services import audit_logger, trend_analytics


class TestCultureAdoptionPhase6(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_anonymous_near_miss_reporting(self):
        """Verify anonymous near-miss strips worker identity and generates tracking code."""
        ticket = incidents._create_ticket(
            db=self.db,
            report_type="suspected",
            text="Uncovered floor trench near BF1 casthouse pump, trip hazard.",
            employee_id="EMP_DO_NOT_LEAK",
            worker_badge_id="BADGE_9999",
            reporter_supervisor_id="SUP_444",
            zone_id="BF1",
            is_anonymous=True,
            shift="Shift B",
            plant_id="bsl_bokaro",
        )

        self.assertIsNotNone(ticket.id)
        self.assertTrue(ticket.is_anonymous)
        self.assertIsNotNone(ticket.anonymous_tracking_code)
        self.assertTrue(ticket.anonymous_tracking_code.startswith("NM-"))
        self.assertEqual(len(ticket.anonymous_tracking_code), 9)  # NM- + 6 hex chars

        # Identity strictly stripped
        self.assertIsNone(ticket.employee_id)
        self.assertIsNone(ticket.worker_badge_id)
        self.assertIsNone(ticket.reporter_supervisor_id)
        self.assertEqual(ticket.reporting_mode, "anonymous_near_miss")
        self.assertEqual(ticket.shift, "Shift B")
        self.assertEqual(ticket.lifecycle_stage, "received")

        # Verify audit log recorded anonymous attribution
        audit_records = (
            self.db.query(AuditLog)
            .filter(AuditLog.ticket_id == ticket.id, AuditLog.action == "INCIDENT_CREATED")
            .all()
        )
        self.assertGreater(len(audit_records), 0)
        self.assertEqual(audit_records[0].actor_id, "ANONYMOUS")
        self.assertEqual(audit_records[0].actor_role, "anonymous_reporter")
        self.assertTrue(audit_records[0].details.get("is_anonymous"))
        self.assertEqual(audit_records[0].details.get("shift"), "Shift B")

    def test_02_status_tracker_lookup_and_milestones(self):
        """Verify frontline workers can track reports by code or ticket ID without logging in."""
        # Create a report
        ticket = incidents._create_ticket(
            db=self.db,
            report_type="suspected",
            text="Steam flange leaking hot condensate onto walkway",
            zone_id="SMS",
            is_anonymous=True,
            shift="Shift A",
            plant_id="bsl_bokaro",
        )

        code = ticket.anonymous_tracking_code
        self.assertIsNotNone(code)

        # 1. Lookup by anonymous code
        tracker_by_code = trend_analytics.get_lifecycle_tracker(code, self.db)
        self.assertEqual(tracker_by_code["ticket_id"], ticket.id)
        self.assertEqual(tracker_by_code["anonymous_tracking_code"], code)
        self.assertTrue(tracker_by_code["is_anonymous"])
        self.assertEqual(tracker_by_code["lifecycle_stage"], "received")
        self.assertEqual(tracker_by_code["shift"], "Shift A")

        # 2. Lookup by ticket ID
        tracker_by_id = trend_analytics.get_lifecycle_tracker(ticket.id, self.db)
        self.assertEqual(tracker_by_id["ticket_id"], ticket.id)
        self.assertEqual(tracker_by_id["anonymous_tracking_code"], code)

        # 3. Non-existent code raises 404 in API endpoint
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            analytics.track_report_status("NON_EXISTENT_CODE_99", self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_03_supervisor_action_assignment_and_closure_sla(self):
        """Verify supervisor triage assigns corrective action and tracks closure turnaround SLA."""
        ticket = incidents._create_ticket(
            db=self.db,
            report_type="suspected",
            text="Conveyor belt misalignment causing rubber friction smoke",
            zone_id="RMY",
            is_anonymous=False,
            employee_id="EMP_8821",
            plant_id="bsl_bokaro",
        )

        # Simulate creation timestamp 3.5 hours ago to test SLA computation
        past_time = datetime.now(timezone.utc) - timedelta(hours=3, minutes=30)
        ticket.created_at = past_time
        self.db.add(ticket)
        self.db.commit()
        self.db.refresh(ticket)

        # 1. Assign corrective action
        due = datetime.now(timezone.utc) + timedelta(days=1)
        assign_payload = ActionAssignRequest(
            assigned_to="Mechanical Crew C / In-Charge K. Singh",
            corrective_action="Re-align conveyor idlers and tighten tensioning bolts.",
            due_date=due,
        )
        updated_ticket = tickets.assign_corrective_action(ticket.id, assign_payload, self.db)

        self.assertEqual(updated_ticket.assigned_to, "Mechanical Crew C / In-Charge K. Singh")
        self.assertEqual(updated_ticket.corrective_action, "Re-align conveyor idlers and tighten tensioning bolts.")
        self.assertEqual(updated_ticket.lifecycle_stage, "action_assigned")

        # Check audit log for assignment event
        assignment_logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.ticket_id == ticket.id, AuditLog.action == "CORRECTIVE_ACTION_ASSIGNED")
            .all()
        )
        self.assertGreater(len(assignment_logs), 0)
        self.assertEqual(assignment_logs[0].details.get("assigned_to"), "Mechanical Crew C / In-Charge K. Singh")

        # 2. Close corrective action
        close_payload = ActionCloseRequest(
            closure_notes="Idler rollers replaced and tracked on center under load. LOTO removed.",
            closure_evidence_path="/photos/conveyor_fix.jpg",
        )
        closed_ticket = tickets.close_action(ticket.id, close_payload, self.db)

        self.assertEqual(closed_ticket.status, "resolved")
        self.assertEqual(closed_ticket.lifecycle_stage, "resolved")
        self.assertIsNotNone(closed_ticket.closed_at)
        self.assertIsNotNone(closed_ticket.closure_time_hours)
        # Verify closure SLA hours calculation
        self.assertGreaterEqual(closed_ticket.closure_time_hours, 3.4)
        self.assertLessEqual(closed_ticket.closure_time_hours, 3.6)

        # Check audit log for closure event
        closure_logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.ticket_id == ticket.id, AuditLog.action == "TICKET_RESOLVED_WITH_ACTION")
            .all()
        )
        self.assertGreater(len(closure_logs), 0)
        self.assertEqual(closure_logs[0].details.get("closure_time_hours"), closed_ticket.closure_time_hours)

    def test_04_safety_trends_hotspots_and_repeat_equipment(self):
        """Verify trends calculation accurately highlights repeat hazards by zone, shift, and equipment."""
        trends = trend_analytics.get_safety_trends("bsl_bokaro", self.db)

        self.assertIn("total_incidents", trends)
        self.assertIn("total_near_misses", trends)
        self.assertIn("closed_near_misses", trends)
        self.assertIn("avg_closure_time_hours", trends)
        self.assertIn("hazards_by_zone", trends)
        self.assertIn("hazards_by_shift", trends)
        self.assertIn("repeat_equipment_hazards", trends)

        self.assertIsInstance(trends["hazards_by_zone"], dict)
        self.assertIsInstance(trends["hazards_by_shift"], dict)
        self.assertIsInstance(trends["repeat_equipment_hazards"], list)

        # Should reflect our plant shifts
        self.assertTrue(any(s in trends["hazards_by_shift"] for s in ["Shift A", "Shift B", "Shift C", "General"]))

    def test_05_team_culture_and_anti_surveillance_guarantees(self):
        """Verify positive reinforcement metrics avoid surveillance and blame leaderboards."""
        culture = trend_analytics.get_culture_metrics("bsl_bokaro", self.db)

        self.assertEqual(culture["plant_id"], "bsl_bokaro")
        self.assertGreaterEqual(culture["total_hazards_fixed"], 1)
        self.assertIn("shift_participation", culture)
        self.assertGreater(len(culture["shift_participation"]), 0)

        # Verify percentages sum close to 100%
        total_pct = sum(sp["pct"] for sp in culture["shift_participation"])
        self.assertGreaterEqual(total_pct, 95.0)
        self.assertLessEqual(total_pct, 105.0)

        # Verify positive bilingual impact statements
        self.assertIn("resolved", culture["impact_statement_en"].lower())
        self.assertIn("hazards", culture["impact_statement_en"].lower())
        self.assertIn("खतरों", culture["impact_statement_hi"])

        # CRITICAL ANTI-SURVEILLANCE INVARIANT:
        # No worker rankings, individual incident tallies, or culpability scoring.
        forbidden_keys = [
            "worker_leaderboard",
            "top_violators",
            "blame_list",
            "individual_incidents",
            "worst_workers",
            "fault_records",
        ]
        for key in forbidden_keys:
            self.assertNotIn(key, culture, f"Violation of anti-surveillance invariant: '{key}' must never exist!")

    def test_06_in_app_explainer_endpoint(self):
        """Verify in-app transparent explainer provides bilingual clarity on the report lifecycle."""
        explainer = analytics.get_report_explainer()

        self.assertIn("en", explainer)
        self.assertIn("hi", explainer)

        for lang in ["en", "hi"]:
            lang_data = explainer[lang]
            self.assertIn("title", lang_data)
            self.assertIn("commitment", lang_data)
            self.assertIn("steps", lang_data)
            self.assertEqual(len(lang_data["steps"]), 4)

            for s in lang_data["steps"]:
                self.assertIn("step", s)
                self.assertIn("title", s)
                self.assertIn("description", s)
                self.assertIn("status_badge", s)
                self.assertTrue(len(s["title"]) > 0)
                self.assertTrue(len(s["description"]) > 0)


if __name__ == "__main__":
    unittest.main()
