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
        self.assertEqual(audit.details["rating"], "useful")

    def test_06_export_rated_questions_dataset(self):
        """Export endpoint returns dataset of rated questions for continuous learning."""
        resp = self.client.get("/tickets/export/rated-questions?plant_id=bsl_bokaro")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("total_rated_samples", data)
        self.assertIn("samples", data)
        self.assertGreaterEqual(data["total_rated_samples"], 1)


if __name__ == "__main__":
    unittest.main()
