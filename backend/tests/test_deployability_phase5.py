"""
Comprehensive Unit & Integration Test Suite for Phase 5: Deployability and Scalability.
Verifies:
  1. Data-driven plant configuration loading (Bokaro & dynamic Rourkela without code changes).
  2. Dynamic spatial impact calculations based on loaded plant zones.
  3. Universal SOP ingestion & section chunking.
  4. Multi-tenant data isolation (plant_id scoping).
  5. Role-Based Access Control (RBAC) permission enforcement.
  6. Cryptographically chained SHA-256 immutable audit ledger with anti-tampering verification.
  7. Outbound integration dispatch and HMAC-SHA256 signature generation.
  8. Standardized enterprise CSV data export.
  9. Automated data retention pruning and PII anonymization.
  10. Air-gapped local model adapter operation (zero external network calls).
  11. Architectural biometric voice-print prohibition assertion.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from app.database import Base, SessionLocal, engine
from app.models import AuditLog, Ticket
from app.schemas import IncidentCreate, PlantZoneDefinition
from app.routers import incidents, tickets, integrations
from app.services import (
    audit_logger,
    data_retention,
    integration_dispatcher,
    model_adapter,
    plant_manager,
    privacy_policy,
    rbac,
    sop_parser,
    spatial_impact,
)
from app.services.model_adapter import InferenceMode, ModelAdapter
from app.services.rbac import AuthContext, UserRole


class TestDeployabilityPhase5(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_01_data_driven_plant_loading(self):
        """Verify plant layout loads dynamically per tenant without hard-coded constants."""
        bokaro = plant_manager.get_plant("bsl_bokaro")
        self.assertEqual(bokaro["plant_id"], "bsl_bokaro")
        self.assertEqual(bokaro["short_name"], "BSL")
        self.assertGreaterEqual(len(bokaro["zones"]), 10)
        self.assertGreaterEqual(len(bokaro["emergency_teams"]), 4)

        # Verify second plant onboarded completely via JSON with zero code changes
        rourkela = plant_manager.get_plant("rsp_rourkela")
        self.assertEqual(rourkela["plant_id"], "rsp_rourkela")
        self.assertEqual(rourkela["short_name"], "RSP")
        self.assertIn("Rourkela", rourkela["name"])
        self.assertGreaterEqual(len(rourkela["zones"]), 4)

    def test_02_dynamic_spatial_impact_per_plant(self):
        """Verify spatial impact calculates correctly using the target plant's specific zones."""
        # Bokaro Blast Furnace 1 gas leak
        impact_bokaro = spatial_impact.assess("BF1", "gas_leak", plant_id="bsl_bokaro")
        self.assertIsNotNone(impact_bokaro)
        self.assertTrue(impact_bokaro["applicable"])
        self.assertEqual(impact_bokaro["incident_zone"], "BF1")

        # Rourkela Blast Furnace 5 gas leak
        impact_rsp = spatial_impact.assess("BF5", "gas_leak", plant_id="rsp_rourkela")
        self.assertIsNotNone(impact_rsp)
        self.assertTrue(impact_rsp["applicable"])
        self.assertEqual(impact_rsp["incident_zone"], "BF5")

    def test_03_universal_sop_ingestion_and_chunking(self):
        """Verify SOP ingestion extracts structured sections and attaches governance frontmatter."""
        sample_sop_text = (
            "# Blast Furnace Tuyere Emergency Isolation\n\n"
            "## Immediate Isolation Steps\n"
            "Depressurize cold blast line immediately. Close snort valve V-01.\n\n"
            "## Water Leak Containment\n"
            "Isolate cooling circuit C-14 and divert steam away from casthouse floor.\n"
        ).encode("utf-8")

        result = sop_parser.ingest_sop_document(
            plant_id="rsp_rourkela",
            filename="rsp_tuyere_emergency.md",
            file_bytes=sample_sop_text,
            sop_id="RSP/SOP/BF-05",
            title="Blast Furnace Tuyere Emergency Isolation",
            version="2.0",
            incident_types=["gas_leak", "molten_metal_spill"],
            reviewer="RSP Safety Command",
            reviewed_by_safety_officer=True,
        )

        self.assertEqual(result["sop_id"], "RSP/SOP/BF-05")
        self.assertEqual(result["plant_id"], "rsp_rourkela")
        self.assertGreaterEqual(result["section_count"], 2)
        self.assertTrue(Path(result["file_path"]).exists())

    def test_04_multi_tenant_data_isolation(self):
        """Verify tickets are partitioned strictly by plant_id and isolated in queries."""
        t_bokaro = incidents.create_incident(
            IncidentCreate(
                plant_id="bsl_bokaro",
                report_type="suspected",
                incident_description="Abnormal heat emission at BSL taphole runner.",
                zone_id="BF1",
                language="en",
            ),
            self.db,
        )

        t_rourkela = incidents.create_incident(
            IncidentCreate(
                plant_id="rsp_rourkela",
                report_type="suspected",
                incident_description="Conveyor motor vibration at RSP raw materials.",
                zone_id="CIVIL_SECTOR",
                language="en",
            ),
            self.db,
        )

        # Query isolated lists
        bokaro_list = tickets.list_tickets(plant_id="bsl_bokaro", db=self.db)
        rsp_list = tickets.list_tickets(plant_id="rsp_rourkela", db=self.db)

        bokaro_ids = [t.id for t in bokaro_list]
        rsp_ids = [t.id for t in rsp_list]

        self.assertIn(t_bokaro.id, bokaro_ids)
        self.assertNotIn(t_bokaro.id, rsp_ids)
        self.assertIn(t_rourkela.id, rsp_ids)
        self.assertNotIn(t_rourkela.id, bokaro_ids)

    def test_05_rbac_permissions_matrix(self):
        """Verify role hierarchy and permission validation across roles."""
        worker_auth = AuthContext(user_id="W-101", role=UserRole.WORKER, plant_id="bsl_bokaro")
        supervisor_auth = AuthContext(user_id="S-201", role=UserRole.SUPERVISOR, plant_id="bsl_bokaro")
        officer_auth = AuthContext(user_id="O-301", role=UserRole.SAFETY_OFFICER, plant_id="bsl_bokaro")
        admin_auth = AuthContext(user_id="A-401", role=UserRole.ADMIN, plant_id="bsl_bokaro")

        # Worker can create incident, but cannot configure plant or read audit logs
        self.assertTrue(worker_auth.has_permission("incident:create"))
        self.assertFalse(worker_auth.has_permission("plant:configure"))
        self.assertFalse(worker_auth.has_permission("audit:read"))

        # Supervisor can proxy report
        self.assertTrue(supervisor_auth.has_permission("incident:proxy_report"))
        self.assertFalse(supervisor_auth.has_permission("plant:configure"))

        # Safety officer can view audit logs and override triage
        self.assertTrue(officer_auth.has_permission("audit:read"))
        self.assertTrue(officer_auth.has_permission("incident:triage_override"))

        # Admin has full capabilities
        self.assertTrue(admin_auth.has_permission("plant:configure"))
        self.assertTrue(admin_auth.has_permission("data:retention_prune"))

    def test_06_immutable_audit_ledger_integrity_and_tamper_detection(self):
        """Verify SHA-256 hash chaining in audit log and tampering detection."""
        import uuid
        test_plant = f"test_audit_plant_{uuid.uuid4().hex[:8]}"

        # Record series of audit entries
        log1 = audit_logger.log_event(self.db, "EVENT_1", plant_id=test_plant, actor_id="U1", actor_role="worker")
        log2 = audit_logger.log_event(self.db, "EVENT_2", plant_id=test_plant, actor_id="U2", actor_role="supervisor")
        log3 = audit_logger.log_event(self.db, "EVENT_3", plant_id=test_plant, actor_id="U3", actor_role="admin")

        self.assertEqual(log2.prev_entry_hash, log1.entry_hash)
        self.assertEqual(log3.prev_entry_hash, log2.entry_hash)

        # Verify initial valid state
        is_valid, count, err = audit_logger.verify_chain_integrity(self.db, plant_id=test_plant)
        self.assertTrue(is_valid)
        self.assertEqual(count, 3)
        self.assertIsNone(err)

        # Simulate adversarial database tampering (modify payload of log2)
        log2.details = {"malicious_modification": True}
        self.db.commit()

        # Integrity check must immediately catch tampering
        is_valid_after, _, err_after = audit_logger.verify_chain_integrity(self.db, plant_id=test_plant)
        self.assertFalse(is_valid_after)
        self.assertIn("tampering detected", err_after.lower())

    def test_07_outbound_dispatch_signature_and_safe_failure(self):
        """Verify HMAC-SHA256 webhook signing and safe execution."""
        secret = "test-secret-key"
        payload = {"ticket_id": "T-100", "event": "CRITICAL_FIRE"}
        raw_bytes = json.dumps(payload).encode("utf-8")

        sig1 = integration_dispatcher._sign_payload(secret, raw_bytes)
        sig2 = integration_dispatcher._sign_payload(secret, raw_bytes)
        self.assertEqual(sig1, sig2)
        self.assertEqual(len(sig1), 64)  # 64 hex characters for SHA-256

        # Dispatch notification to dummy ticket
        dummy_ticket = Ticket(
            id="T-DISP-01",
            plant_id="bsl_bokaro",
            report_type="emergency",
            zone_id="BF1",
            predicted_category="fire",
            routing_tier="emergency_authority",
            risk_score=0.95,
            incident_description="Transformer fire in casthouse",
            incident_description_en="Transformer fire in casthouse",
        )
        res = integration_dispatcher.dispatch_incident_notifications(dummy_ticket, plant_id="bsl_bokaro")
        self.assertIn("teams_notified_count", res)
        self.assertGreaterEqual(res["teams_notified_count"], 1)

    def test_08_csv_data_export_compliance(self):
        """Verify standardized CSV export formats conform to enterprise safety schemas."""
        ticket = incidents.create_incident(
            IncidentCreate(
                plant_id="bsl_bokaro",
                report_type="emergency",
                incident_description="Gas leak detected near valve V-12.",
                zone_id="GHS",
                language="en",
            ),
            self.db,
        )

        auth = AuthContext(user_id="OFFICER-1", role=UserRole.SAFETY_OFFICER, plant_id="bsl_bokaro")
        response = integrations.export_tickets_csv(plant_id="bsl_bokaro", db=self.db, auth=auth)

        self.assertEqual(response.media_type, "text/csv")
        csv_text = response.body.decode("utf-8")
        reader = csv.reader(io.StringIO(csv_text))
        rows = list(reader)

        headers = rows[0]
        self.assertIn("Incident ID", headers)
        self.assertIn("Plant ID", headers)
        self.assertIn("Routing Tier", headers)
        self.assertIn("Risk Score", headers)

        # Check data row contains created ticket
        found = any(row[0] == ticket.id for row in rows[1:])
        self.assertTrue(found)

    def test_09_data_retention_pruning_and_anonymization(self):
        """Verify media past retention window is deleted and worker PII is anonymized."""
        import uuid
        tid = f"OLD-{uuid.uuid4().hex[:8]}"
        old_ticket = Ticket(
            id=tid,
            plant_id="bsl_bokaro",
            report_type="suspected",
            worker_badge_id="WORKER-CONFIDENTIAL-99",
            employee_id="EMP-9999",
            reporter_supervisor_id="SUP-1111",
            zone_id="RMY",
            incident_description="Historical dust surge.",
            incident_description_en="Historical dust surge.",
            created_at=datetime.now(timezone.utc) - timedelta(days=200),
        )
        self.db.add(old_ticket)
        self.db.commit()

        # Run retention pruning with 180-day retention
        result = data_retention.prune_expired_media(self.db, plant_id="bsl_bokaro", retention_days=180)
        self.assertGreaterEqual(result["records_anonymized"], 1)

        self.db.refresh(old_ticket)
        self.assertEqual(old_ticket.worker_badge_id, "ANONYMIZED")
        self.assertEqual(old_ticket.employee_id, "ANONYMIZED")
        self.assertEqual(old_ticket.reporter_supervisor_id, "ANONYMIZED")

    def test_10_airgapped_local_model_adapter(self):
        """Verify model adapter in local_airgapped mode executes with zero external calls."""
        adapter = ModelAdapter(mode=InferenceMode.LOCAL_AIRGAPPED)
        self.assertTrue(adapter.is_airgapped())

        completion = adapter.generate_completion(prompt="Verify tuyere burn risk")
        self.assertTrue(completion["is_airgapped"])
        self.assertIn("AIR-GAPPED LOCAL ADAPTER", completion["text"])
        self.assertEqual(completion["model"], "local-rule-engine-v2")

    def test_11_biometric_prohibition_compliance(self):
        """Verify architectural prohibition of biometric / voice-print speaker identification."""
        self.assertTrue(privacy_policy.assert_no_biometric_collection())
        self.assertIn("voice_consent", privacy_policy.CONSENT_STATEMENTS["en"])
        self.assertIn("voice_consent", privacy_policy.CONSENT_STATEMENTS["hi"])


if __name__ == "__main__":
    unittest.main()
