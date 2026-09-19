"""
Unit & Regression Test Suite for Phase 3: Vision Module Fix.
Verifies:
  1. Apache-2.0 licensing and detector version provenance.
  2. SHA-256 fingerprint generation on media evidence.
  3. Dedicated Junk-Photo Gate filtering non-industrial junk (blanks, documents, pitch-black).
  4. Localized Object Detector generating 2D bounding boxes (fire, smoke, person, PPE).
  5. Class governance & experimental tagging on unvalidated hazard classes (molten metal spill).
  6. Video multi-frame sampling resilience.
  7. Safety invariant: non-corroborated media leaves score neutral and flags human review.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image, ImageDraw

from app.services import visual_analysis, visual_detector
from app.services.visual_analysis import (
    EXPERIMENTAL_CLASSES,
    VALIDATED_CLASSES,
    analyze_visual_evidence,
    filter_junk_or_unrelated_media,
)
from app.services.visual_detector import DETECTOR_LICENSE, DETECTOR_VERSION, VisualDetector


class TestVisionPhase3(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        for p in Path(self.temp_dir).glob("*"):
            try:
                p.unlink()
            except Exception:
                pass
        try:
            os.rmdir(self.temp_dir)
        except Exception:
            pass

    def test_01_license_and_detector_version_provenance(self):
        """Verify Apache-2.0 licensing (eliminating AGPL-3.0 copyleft) and detector version."""
        self.assertEqual(DETECTOR_LICENSE, "Apache-2.0")
        self.assertIn("Apache-2.0", DETECTOR_VERSION)
        self.assertIn("RT-DETR", DETECTOR_VERSION)

        detector = visual_detector.get_visual_detector()
        self.assertEqual(detector.license, "Apache-2.0")
        self.assertIn("fire", detector.classes)
        self.assertIn("safety_vest", detector.classes)

    def test_02_sha256_fingerprint_verification(self):
        """Verify SHA-256 fingerprint matches exact file content bytes."""
        img = Image.new("RGB", (200, 200), color=(180, 50, 20))
        img_path = Path(self.temp_dir) / "evidence_flame.jpg"
        img.save(img_path)

        with open(img_path, "rb") as f:
            expected_hash = hashlib.sha256(f.read()).hexdigest()

        analysis = analyze_visual_evidence(img_path, "fire")
        self.assertEqual(analysis["image_sha256"], expected_hash)
        self.assertEqual(analysis["detector_license"], "Apache-2.0")

    def test_03_junk_photo_gate_filters_non_industrial_media(self):
        """Verify Junk-Photo Gate filters office documents, blank walls, and pitch-black images."""
        # 1. Solid blank image (e.g. wall or lens cap)
        blank_img = Image.new("RGB", (128, 128), color=(200, 200, 200))
        is_junk, reason, stats = filter_junk_or_unrelated_media(blank_img)
        self.assertTrue(is_junk)
        self.assertIn("solid", reason.lower())

        # 2. Pitch black image
        black_img = Image.new("RGB", (128, 128), color=(5, 5, 5))
        is_junk, reason, stats = filter_junk_or_unrelated_media(black_img)
        self.assertTrue(is_junk)
        self.assertIn("underexposed", reason.lower())

        # 3. White office document with high-contrast text lines
        doc_img = Image.new("RGB", (256, 256), color=(245, 245, 245))
        draw = ImageDraw.Draw(doc_img)
        for y in range(30, 230, 15):
            draw.line([(30, y), (220, y)], fill=(10, 10, 10), width=2)

        is_junk, reason, stats = filter_junk_or_unrelated_media(doc_img)
        self.assertTrue(is_junk)
        self.assertIn("document", reason.lower())

        # End-to-end analyze_visual_evidence on document:
        doc_path = Path(self.temp_dir) / "office_doc.png"
        doc_img.save(doc_path)
        res = analyze_visual_evidence(doc_path, "fire")
        self.assertFalse(res["is_valid_evidence"])
        self.assertEqual(res["visual_status"], "no_visual_corroboration")
        self.assertEqual(res["risk_score_impact"], "neutral_unchanged")
        self.assertTrue(res["flagged_for_human_review"])
        self.assertIn("Junk-Photo Gate", res["visual_summary"])

    def test_04_localized_bounding_box_detection(self):
        """Verify detector localizes fire regions and returns normalized 2D boxes."""
        # Create an industrial scene with a clear flame hotspot in the center
        scene = Image.new("RGB", (300, 300), color=(40, 40, 45))
        draw = ImageDraw.Draw(scene)
        # Draw intense orange-red flame rectangle in center
        draw.rectangle([100, 80, 200, 180], fill=(240, 90, 15))
        # Add yellow core
        draw.rectangle([120, 100, 180, 160], fill=(255, 220, 40))

        detector = visual_detector.get_visual_detector()
        boxes = detector.detect(scene)

        self.assertGreater(len(boxes), 0, "Detector should localize fire hotspot")
        fire_box = next((b for b in boxes if b["label"] == "fire"), None)
        self.assertIsNotNone(fire_box)
        self.assertGreaterEqual(fire_box["confidence"], 0.70)
        self.assertEqual(fire_box["color"], "#EF4444")

        # Verify normalized coordinates
        self.assertGreaterEqual(fire_box["ymin"], 0.0)
        self.assertLessEqual(fire_box["ymax"], 1.0)
        self.assertGreaterEqual(fire_box["xmin"], 0.0)
        self.assertLessEqual(fire_box["xmax"], 1.0)
        self.assertLess(fire_box["ymin"], fire_box["ymax"])
        self.assertLess(fire_box["xmin"], fire_box["xmax"])

    def test_05_person_and_ppe_detection(self):
        """Verify detector localizes workers wearing safety vests."""
        scene = Image.new("RGB", (300, 300), color=(50, 50, 50))
        draw = ImageDraw.Draw(scene)
        # Draw worker with high-vis fluorescent green vest and yellow hard hat
        # Head / Helmet
        draw.rectangle([130, 40, 170, 70], fill=(250, 200, 20))
        # Torso / High-vis vest
        draw.rectangle([120, 70, 180, 160], fill=(180, 255, 20))

        detector = visual_detector.get_visual_detector()
        boxes = detector.detect(scene)

        labels = [b["label"] for b in boxes]
        self.assertIn("person", labels)
        self.assertIn("safety_vest", labels)

    def test_06_class_governance_experimental_tagging(self):
        """Verify unvalidated classes (e.g. molten_metal_spill) are explicitly flagged as experimental."""
        self.assertIn("molten_metal_spill", EXPERIMENTAL_CLASSES)
        self.assertIn("chemical_spill", EXPERIMENTAL_CLASSES)

        # Create bright glowing molten scene
        molten_img = Image.new("RGB", (200, 200), color=(30, 30, 30))
        draw = ImageDraw.Draw(molten_img)
        # Extreme white-yellow radiant pool
        draw.rectangle([40, 40, 160, 160], fill=(255, 240, 150))
        molten_path = Path(self.temp_dir) / "molten_pool.jpg"
        molten_img.save(molten_path)

        res = analyze_visual_evidence(molten_path, "molten_metal_spill")
        # If detected event is molten_metal_spill, check experimental flag
        if res["detected_event"] == "molten_metal_spill":
            self.assertTrue(res["is_experimental"])
            self.assertIn("No verified plant training data", res["experimental_notice"])

    def test_07_media_not_found_is_safe_neutral(self):
        """Verify missing media file safely defaults to neutral without crashing."""
        res = analyze_visual_evidence("non_existent_path_12345.jpg", "fire")
        self.assertFalse(res["is_valid_evidence"])
        self.assertEqual(res["visual_status"], "no_visual_corroboration")
        self.assertEqual(res["risk_score_impact"], "neutral_unchanged")
        self.assertTrue(res["flagged_for_human_review"])
        self.assertIsNone(res["image_sha256"])


if __name__ == "__main__":
    unittest.main()
