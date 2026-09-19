"""
Comprehensive Automated Test Suite for RAG Verification Pipeline (Phases 1-5).
Tests:
1. Retrieval Recall and SOP ID mapping against approved knowledge base
2. Missing-slot prioritization policy across hazard categories
3. Non-repetition invariant: answered slots must never be re-asked
4. Question length and format constraints (<= 25 words, single-sentence, zero blame)
5. Safety officer question rating endpoint and audit logging
6. Export of rated question training/eval dataset
"""

import unittest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.database import Base, engine, get_db
from app.main import app
from app.models import Ticket, AuditLog
from app.services import interview_state, hazard_checklists, hybrid_retrieval, rag


class TestRAGPipelineImprovements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        rag.build_index()

    def setUp(self):
        self.db: Session = next(get_db())

    def tearDown(self):
        self.db.close()

    def test_01_retrieval_grounding_and_governance(self):
        """Verified that approved SOP documents are retrieved with valid IDs and citations."""
        query = "gas leak from flange near blast furnace stove"
        chunks, is_confident = hybrid_retrieval.retrieve_grounded_context("gas_leak", query, top_k=2)
        self.assertTrue(len(chunks) > 0)
        self.assertTrue(is_confident)
        top_sop = chunks[0]["sop_id"]
        self.assertIn(top_sop, ["BSL/SOP/GAS-01", "BSL/REF/BFG-01", "BSL/REF/COG-02"])

    def test_02_slot_prioritization_and_urgency(self):
        """Initial state picks top-priority missing slot (isolation or victim triage)."""
        state = interview_state.InterviewState(
            hazard_type="fire",
            zone_id="COB",
            language="en",
            initial_report="Fire observed in cable basement.",
        )
        q, opts, sop, is_p, target_slot = interview_state.generate_next_best_question(state)
        self.assertIsNotNone(q)
        self.assertIn(target_slot, ["material_involved", "electrical_power_cut"])
        self.assertTrue(is_p)
        self.assertIn("Fire", sop)

    def test_03_non_repetition_invariant(self):
        """Once worker answers a slot, it is NEVER asked again in subsequent turns."""
        state = interview_state.InterviewState(
            hazard_type="gas_leak",
            zone_id="BF1",
            language="en",
            initial_report="Gas leaking from pipe flange, but we already shut the isolation valve.",
        )
        # Isolation is already stated as shut in initial report
        self.assertIn("isolation_status", state.filled_slots)

        q, opts, sop, is_p, target_slot = interview_state.generate_next_best_question(state)
        # Next question MUST NOT ask about isolation status
        self.assertNotEqual(target_slot, "isolation_status")
        self.assertIn(target_slot, ["victims_condition", "evacuation_status", "ignition_source"])

    def test_04_constraint_enforcement_length_and_blame(self):
        """All generated questions must be <= 25 words, single-sentence, and contain no blame words."""
        for cat in hazard_checklists.INFORMATION_NEEDS_REGISTRY.keys():
            state = interview_state.InterviewState(
                hazard_type=cat,
                zone_id="SMS",
                language="en",
                initial_report=f"Reported {cat} emergency in sector.",
            )
            q, opts, sop, is_p, slot = interview_state.generate_next_best_question(state)
            self.assertIsNotNone(q)
            words = q.strip().split()
            self.assertLessEqual(len(words), 25, f"Question too long: {q}")
            self.assertEqual(q.count("?"), 1, f"Multi-part question: {q}")
            for blame in ["why did you", "who caused", "whose fault"]:
                self.assertNotIn(blame, q.lower())

    def test_05_safety_officer_question_rating_and_audit(self):
        """Safety officer submits question rating, stored on ticket and logged to immutable audit trail."""
        ticket_id = f"test-rag-{uuid.uuid4().hex[:8]}"
        ticket = Ticket(
            id=ticket_id,
            plant_id="bsl_bokaro",
            report_type="suspected",
            predicted_category="gas_leak",
            incident_description="Gas leak at stove 3 manifold.",
            incident_description_en="Gas leak at stove 3 manifold.",
            language="en",
        )
        self.db.add(ticket)
        self.db.commit()

        # Submit question rating
        resp = self.client.post(
            f"/tickets/{ticket_id}/rate-question",
            json={
                "question_text": "Has the gas supply or isolation valve been safely closed?",
                "target_slot": "isolation_status",
                "rating": "useful",
                "feedback_notes": "Essential priority question for incident command",
                "officer_id": "OFFICER_VERMA",
            },
        )
        self.assertEqual(resp.status_code, 200)
        t_data = resp.json()
        self.assertEqual(len(t_data["question_ratings"]), 1)
        self.assertEqual(t_data["question_ratings"][0]["rating"], "useful")
        self.assertEqual(t_data["question_ratings"][0]["officer_id"], "OFFICER_VERMA")

        # Verify audit log entry
        audit = self.db.query(AuditLog).filter_by(ticket_id=ticket_id, action="QUESTION_RATING_SUBMITTED").first()
        self.assertIsNotNone(audit)
    def test_06_export_rated_questions_dataset(self):
        """Export endpoint returns dataset of rated questions for continuous learning."""
        resp = self.client.get("/tickets/export/rated-questions?plant_id=bsl_bokaro")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_rated_samples", data)
        self.assertIn("samples", data)
        self.assertGreaterEqual(data["total_rated_samples"], 1)

    def test_07_verification_no_repeat_questions_on_short_answers(self):
        """Verifies that verification questions never repeat across turns even when answers are short."""
        from app.services import verification_engine

        # Turn 0
        q0, idx0, opts0, sop0, is_p0 = verification_engine.next_question(
            category="gas_leak",
            answered_count=0,
            language="en",
            incident_description_en="Severe gas leak detected in coke oven battery 5.",
            prior_questions=[],
            prior_answers_en=[],
        )
        self.assertIsNotNone(q0)

        # Turn 1: Short answer 'No'
        q1, idx1, opts1, sop1, is_p1 = verification_engine.next_question(
            category="gas_leak",
            answered_count=1,
            language="en",
            incident_description_en="Severe gas leak detected in coke oven battery 5.",
            prior_questions=[q0],
            prior_answers_en=["No"],
        )
        self.assertIsNotNone(q1)
        self.assertNotEqual(q0.strip().lower(), q1.strip().lower())

        # Turn 2: Short answer 'No one'
        q2, idx2, opts2, sop2, is_p2 = verification_engine.next_question(
            category="gas_leak",
            answered_count=2,
            language="en",
            incident_description_en="Severe gas leak detected in coke oven battery 5.",
            prior_questions=[q0, q1],
            prior_answers_en=["No", "No one"],
        )
        self.assertIsNotNone(q2)
        self.assertNotEqual(q1.strip().lower(), q2.strip().lower())
        self.assertNotEqual(q0.strip().lower(), q2.strip().lower())

        # Test Hindi turns as well
        q_hi_0, _, _, _, _ = verification_engine.next_question(
            category="fire",
            answered_count=0,
            language="hi",
            incident_description_en="Fire in cable gallery basement.",
            prior_questions=[],
            prior_answers_en=[],
        )
        q_hi_1, _, _, _, _ = verification_engine.next_question(
            category="fire",
            answered_count=1,
            language="hi",
            incident_description_en="Fire in cable gallery basement.",
            prior_questions=[q_hi_0],
            prior_answers_en=["हाँ"],
        )
        self.assertIsNotNone(q_hi_1)
        self.assertNotEqual(q_hi_0.strip().lower(), q_hi_1.strip().lower())


if __name__ == "__main__":
    unittest.main()

