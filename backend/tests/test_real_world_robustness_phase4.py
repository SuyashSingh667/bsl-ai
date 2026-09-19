"""
Unit Test Suite for Phase 4: Real-World Robustness (Plant Floor Reality).
Verifies:
  1. Pluggable TTS Provider & Pre-Cached SOP Audio offline lookup.
  2. Steel plant domain glossary post-corrections (LOTO, casthouse, tuyere, slag, BF gas).
  3. ASR segment confidence & low-confidence clarification trigger.
  4. Kiosk mode & supervisor proxy reporting persistence.
  5. Phone-restricted & intrinsically-safe zone metadata integrity.
"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from app.database import Base, SessionLocal, engine
from app.models import Ticket
from app.routers import incidents
from app.schemas import IncidentCreate
from app.services import tts_provider, transcription
from app.services.tts_provider import PreCachedSOPAudioProvider, get_tts_manager
from app.services.transcription import (
    check_critical_term_clarification,
    normalize_english_safety_terms,
    normalize_hindi_phonetics,
)


class TestRealWorldRobustnessPhase4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)

    def setUp(self):
        self.db = SessionLocal()
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        self.db.close()

    def test_01_pluggable_tts_precached_sop_audio(self):
        """Verify pre-cached SOP audio provider serves offline audio without network calls."""
        mgr = get_tts_manager()
        out_file = Path(self.temp_dir) / "test_sop_prompt.wav"

        # Standard SOP prompt that was pre-cached
        standard_text = "Move away from the hazard area immediately, alert your supervisor, and proceed to the designated assembly point."
        success = mgr.synthesize(standard_text, language="en", out_path=out_file)

        self.assertTrue(success, "Pre-cached SOP audio provider should successfully find pre-generated prompt")
        self.assertTrue(out_file.exists())
        self.assertGreater(out_file.stat().st_size, 0)

    def test_02_steel_plant_domain_glossary_corrections(self):
        """Verify post-correction dictionary corrects noisy Whisper steel plant terminology."""
        raw_noisy_text = "Worker reported low toe applied at breaker panel, but saw molten slow near cast house two year and b f gas leak."
        corrected = normalize_english_safety_terms(raw_noisy_text)

        self.assertIn("LOTO", corrected)
        self.assertIn("slag", corrected)
        self.assertIn("casthouse", corrected)
        self.assertIn("tuyere", corrected)
        self.assertIn("BF gas", corrected)
        self.assertNotIn("low toe", corrected)
        self.assertNotIn("two year", corrected)

    def test_03_hindi_steel_plant_lexicon_normalization(self):
        """Verify Hindi phonetic post-corrections for steel equipment and LOTO."""
        raw_hi = "ब्लास्ट फर्नेस कास्ट हाउस में टूयर के पास स्लेग का रिसाव है और लोटो लगाना होगा।"
        corrected_hi = normalize_hindi_phonetics(raw_hi)

        self.assertIn("कास्टहाउस", corrected_hi)
        self.assertIn("ट्यूयर", corrected_hi)
        self.assertIn("स्लैग", corrected_hi)
        self.assertIn("LOTO", corrected_hi)

    def test_04_asr_critical_term_clarification_trigger(self):
        """Verify low-confidence critical words trigger worker clarification prompt."""
        text = "Gas leak observed near tuyere in blast furnace."
        # High confidence on sentence, but low confidence on critical term
        segments = [
            {"text": "Gas leak observed near", "confidence": 0.95},
            {"text": "tuyere in blast furnace", "confidence": 0.52},
        ]

        needs_clarif, target, prompt = check_critical_term_clarification(text, segments)
        self.assertTrue(needs_clarif)
        self.assertEqual(target, "tuyere")
        self.assertIn("Low speech recognition confidence", prompt)
        self.assertIn("tuyere", prompt)

    def test_05_kiosk_mode_incident_reporting_persistence(self):
        """Verify incident reporting in shared kiosk mode persists station and badge IDs."""
        payload = IncidentCreate(
            report_type="suspected",
            incident_description="Abnormal gear vibration in secondary cooling pump motor.",
            reporting_mode="kiosk",
            worker_badge_id="SAIL-5524",
            kiosk_station_id="KSK-BF1-02",
            zone_id="BF1",
            language="en",
        )

        ticket = incidents.create_incident(payload, self.db)
        self.assertEqual(ticket.reporting_mode, "kiosk")
        self.assertEqual(ticket.worker_badge_id, "SAIL-5524")
        self.assertEqual(ticket.kiosk_station_id, "KSK-BF1-02")
        self.assertIsNone(ticket.reporter_supervisor_id)

    def test_06_supervisor_proxy_reporting_persistence(self):
        """Verify supervisor proxy reporting records both supervisor and worker credentials."""
        payload = IncidentCreate(
            report_type="emergency",
            incident_description="Molten steel breakout through taphole runner channel.",
            reporting_mode="supervisor_proxy",
            reporter_supervisor_id="SUP-8821",
            worker_badge_id="SAIL-4102",
            kiosk_station_id="KSK-BF1-01",
            zone_id="BF1",
            language="en",
        )

        ticket = incidents.create_incident(payload, self.db)
        self.assertEqual(ticket.reporting_mode, "supervisor_proxy")
        self.assertEqual(ticket.reporter_supervisor_id, "SUP-8821")
        self.assertEqual(ticket.worker_badge_id, "SAIL-4102")
        self.assertEqual(ticket.routing_tier, "emergency_authority")

    def test_07_zone_constraints_phone_restricted_flags(self):
        """Verify phone-restricted and intrinsically-safe flags in plant zones metadata."""
        from app.config import BACKEND_DIR
        zones_path = BACKEND_DIR / "spatial_impact" / "zones.json"
        if not zones_path.exists():
            zones_path = Path("spatial_impact/zones.json")
        self.assertTrue(zones_path.exists())

        with open(zones_path, "r") as fp:
            data = json.load(fp)

        zone_dict = {z["zone_id"]: z for z in data.get("zones", [])}

        # Blast Furnace 1 must be phone-restricted and intrinsically-safe
        self.assertIn("BF1", zone_dict)
        self.assertTrue(zone_dict["BF1"]["phone_restricted"])
        self.assertTrue(zone_dict["BF1"]["intrinsically_safe_only"])
        self.assertIsNotNone(zone_dict["BF1"]["safe_alternative"])
        self.assertIn("Kiosk", zone_dict["BF1"]["safe_alternative"])

        # Gas Holder Station must be phone-restricted
        self.assertIn("GHS", zone_dict)
        self.assertTrue(zone_dict["GHS"]["phone_restricted"])
        self.assertTrue(zone_dict["GHS"]["intrinsically_safe_only"])

        # Non-hazardous area (e.g. Raw Material Yard) is not phone-restricted
        self.assertIn("RMY", zone_dict)
        self.assertFalse(zone_dict["RMY"]["phone_restricted"])


if __name__ == "__main__":
    unittest.main()
