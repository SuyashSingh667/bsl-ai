import unittest
import uuid
from app.models import Ticket
from app.services import safety_rules, severity_matrix, rag, precautionary_measures, visual_analysis


class TestSafetyRules(unittest.TestCase):
    def test_human_report_emergency_primacy(self):
        """Human report always wins: emergency report cannot be downgraded by AI."""
        inv = safety_rules.apply_safety_invariants(
            human_report_type="emergency",
            current_tier="emergency_authority",
            current_risk_score=0.85,
            proposed_tier="safety_team_queue",
            proposed_risk_score=0.20,
            has_dispatched=True,
            is_acute_emergency=True,
        )
        self.assertGreaterEqual(inv["risk_score"], 0.75, "Emergency human report floor must be at least 0.75")
        self.assertEqual(inv["routing_tier"], "emergency_authority", "Emergency report must never be demoted from emergency_authority")
        self.assertTrue(inv["downgrade_prevented"], "Must record downgrade prevented in audit trail")
        self.assertTrue(inv["dispatch_active"], "Emergency dispatch must remain active")

    def test_monotonic_severity_floor_downgrade_rejection(self):
        """No AI component may downgrade an existing severity floor."""
        inv = safety_rules.apply_safety_invariants(
            human_report_type="suspected",
            current_tier="shift_supervisor",
            current_risk_score=0.65,
            proposed_tier="safety_team_queue",
            proposed_risk_score=0.30,
            has_dispatched=False,
            is_acute_emergency=False,
        )
        self.assertEqual(inv["risk_score"], 0.65, "Score must remain at 0.65")
        self.assertEqual(inv["routing_tier"], "shift_supervisor", "Routing tier must remain at shift_supervisor")
        self.assertTrue(inv["downgrade_prevented"])

    def test_escalation_promotion_allowed(self):
        """Escalation is allowed and promoted when new evidence increases hazard."""
        inv = safety_rules.apply_safety_invariants(
            human_report_type="suspected",
            current_tier="shift_supervisor",
            current_risk_score=0.50,
            proposed_tier="emergency_authority",
            proposed_risk_score=0.88,
            has_dispatched=False,
            is_acute_emergency=False,
        )
        self.assertEqual(inv["risk_score"], 0.88, "Score must be elevated to 0.88")
        self.assertEqual(inv["routing_tier"], "emergency_authority", "Routing tier must escalate to emergency_authority")
        self.assertFalse(inv["downgrade_prevented"])

    def test_irreversible_dispatch_invariant(self):
        """Once dispatch is triggered, it cannot be delayed or revoked by AI."""
        inv = safety_rules.apply_safety_invariants(
            human_report_type="suspected",
            current_tier="shift_supervisor",
            current_risk_score=0.70,
            proposed_tier="safety_team_queue",
            proposed_risk_score=0.25,
            has_dispatched=True,
            is_acute_emergency=False,
        )
        self.assertEqual(inv["routing_tier"], "shift_supervisor")
        self.assertTrue(inv["dispatch_active"], "Dispatched incident must remain active")
        self.assertNotEqual(inv["routing_tier"], "safety_team_queue")

    def test_transparent_severity_matrix(self):
        """Rule-based severity matrix calculates score and shows factors + advisory label."""
        score, matrix_data = severity_matrix.calculate_severity_matrix(
            category="fire",
            observation_mode="visual_confirmed",
            is_hazard_active=True,
            people_exposed_count=5,
            zone_id="BF1",
            impact={"consequence_multiplier": 1.25},
        )
        self.assertTrue(0.0 <= score <= 1.0)
        self.assertIn("hazard_base_severity", matrix_data)
        self.assertIn("likelihood", matrix_data)
        self.assertIn("consequence", matrix_data)
        self.assertIn("asset_proximity", matrix_data)
        self.assertIn("ml_advisory", matrix_data)
        self.assertEqual(matrix_data["ml_advisory"]["role"], "ADVISORY ONLY")
        self.assertIn("multiplier", matrix_data["likelihood"])
        self.assertIn("multiplier", matrix_data["consequence"])
        self.assertIn("multiplier", matrix_data["asset_proximity"])

    def test_evidence_only_vision_unrelated_photo(self):
        """Vision cannot lower score on unrelated images, flags for human review, never auto-dismisses."""
        res = visual_analysis.analyze_visual_evidence("non_existent_unrelated_photo.jpg", "fire")
        self.assertEqual(res["risk_score_impact"], "neutral_unchanged")
        self.assertEqual(res["visual_status"], "no_visual_corroboration")
        self.assertTrue(res["flagged_for_human_review"])
        self.assertIn("human_review_reason", res)
        self.assertIn("evidence-only", res["advisory_notice"])

    def test_sop_governance_unreviewed_blocked_from_rag(self):
        """Unreviewed SOPs are strictly blocked from the RAG index."""
        rag.build_index()
        unreviewed_chunks = [c for c in rag._chunks if c.sop_id == "BSL/SOP/TEST-99"]
        self.assertEqual(len(unreviewed_chunks), 0, "Unreviewed procedure must not exist in index")

    def test_sop_retrieve_and_quote_citations_and_gap_fallback(self):
        """Instructions must cite [SOP_ID: Section X] and unreviewed gaps trigger fallback."""
        t_fire = Ticket(
            id=str(uuid.uuid4()),
            report_type="suspected",
            predicted_category="fire",
            incident_description="Conveyor motor smoking with small flames",
            incident_description_en="Conveyor motor smoking with small flames",
            language="en",
        )
        res_fire = precautionary_measures.generate_precautionary_measures(t_fire)
        self.assertEqual(res_fire["sop_code"], "BSL/SOP/FIRE-02")
        self.assertFalse(res_fire["sop_gap_detected"])
        self.assertEqual(len(res_fire["measures"]), 4)
        for m in res_fire["measures"]:
            self.assertTrue(m["citation"].startswith("[BSL/SOP/FIRE-02: Section "), f"Invalid citation {m['citation']}")
            self.assertTrue(m["checklist_label"].startswith("[BSL/SOP/FIRE-02]"), f"Invalid checklist label {m['checklist_label']}")

        t_gap = Ticket(
            id=str(uuid.uuid4()),
            report_type="suspected",
            predicted_category="unreviewed_experimental_test",
            incident_description="Experimental laser test failure",
            incident_description_en="Experimental laser test failure",
            language="en",
        )
        res_gap = precautionary_measures.generate_precautionary_measures(t_gap)
        self.assertTrue(res_gap["sop_gap_detected"])
        self.assertTrue(t_gap.sop_gap_detected)
        self.assertTrue(t_gap.flagged_for_human_review)
        for m in res_gap["measures"]:
            self.assertIn("[BSL/SOP/GEN-00: Section ", m["citation"])


if __name__ == "__main__":
    unittest.main()
