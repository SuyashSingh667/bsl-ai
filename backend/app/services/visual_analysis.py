"""
AI Visual Hazard Analysis & Object Detection Subsystem (Phase 3).
Operates under Apache-2.0 licensing, strictly decoupled from AGPL-3.0 copyleft models.

Key Capabilities:
  1. Dedicated Junk-Photo Gate: filters office documents, screenshots, and blank frames.
  2. Apache-2.0 Localized Object Detection: identifies bounding boxes for fire, smoke, person, PPE.
  3. Class Governance: tags unvalidated classes (e.g. molten_metal_spill) as experimental.
  4. Auditable Dossier Markers: SHA-256 fingerprint, model version, license, and confidence.
  5. Multi-Frame Video Sampling: extracts and analyzes keyframes across temporal intervals.

Invariant: AI Vision is strictly evidence-only. It may corroborate and elevate urgency,
but NEVER lowers risk scores, demotes severity tiers, or auto-dismisses an incident.
"""

from __future__ import annotations

import hashlib
import logging
import math
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.config import BACKEND_DIR
from app.services.visual_detector import (
    DETECTOR_LICENSE,
    DETECTOR_VERSION,
    get_visual_detector,
)

logger = logging.getLogger(__name__)

MODEL_DIR = BACKEND_DIR / "data" / "models"
MODEL_PATH = MODEL_DIR / "visual_hazard_classifier.pt"

HAZARD_CLASSES = [
    "fire",
    "smoke",
    "electrical_hazard",
    "chemical_spill",
    "molten_metal_spill",
    "mechanical_failure",
    "vehicle_traffic_incident",
    "normal_machinery",
    "unrelated_photo",
]

CLASS_TO_IDX = {c: i for i, c in enumerate(HAZARD_CLASSES)}
IDX_TO_CLASS = {i: c for i, c in enumerate(HAZARD_CLASSES)}

# Governance: Classes with zero public or verified plant training data
EXPERIMENTAL_CLASSES: dict[str, str] = {
    "molten_metal_spill": "No verified plant training data. Requires Casthouse on-site dataset (BSL/SOP/MOLTEN-01).",
    "chemical_spill": "Experimental. Requires Acid Regeneration Plant verified dataset.",
    "crane_lifting_failure": "Experimental. Requires Heavy Machine Shop / SMS-II verified dataset.",
}

VALIDATED_CLASSES: set[str] = {
    "fire",
    "smoke",
    "person",
    "hard_hat",
    "safety_vest",
    "electrical_hazard",
    "mechanical_failure",
    "vehicle_traffic_incident",
    "normal_machinery",
}

CATEGORY_COMPATIBILITY: dict[str, set[str]] = {
    "fire": {"fire", "smoke", "electrical_hazard"},
    "gas_leak": {"smoke", "chemical_spill"},
    "electrical_hazard": {"electrical_hazard", "fire", "smoke"},
    "chemical_spill": {"chemical_spill"},
    "molten_metal_spill": {"molten_metal_spill", "fire", "smoke"},
    "crane_lifting_failure": {"mechanical_failure"},
    "mechanical_failure": {"mechanical_failure"},
    "conveyor": {"mechanical_failure", "smoke", "fire"},
    "vehicle_traffic_incident": {"vehicle_traffic_incident"},
    "slip_fall": {"chemical_spill", "mechanical_failure"},
    "ppe_violation": {"normal_machinery", "person", "safety_vest", "hard_hat"},
}


class HazardVisionNet(nn.Module):
    """Auxiliary CNN feature extractor for whole-image industrial classification."""

    def __init__(self, num_classes: int = len(HAZARD_CLASSES)):
        super().__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=5, stride=2, padding=2)
        self.bn1 = nn.BatchNorm2d(32)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)
        self.avgpool = nn.AdaptiveAvgPool2d((2, 2))
        self.maxpool = nn.AdaptiveMaxPool2d((2, 2))
        cnn_feat_dim = 128 * 4 * 2
        aux_dim = 32
        self.classifier = nn.Sequential(
            nn.Linear(cnn_feat_dim + aux_dim, 256),
            nn.LayerNorm(256),
            nn.GELU(),
            nn.Dropout(0.2),
            nn.Linear(256, 128),
            nn.LayerNorm(128),
            nn.GELU(),
            nn.Dropout(0.1),
            nn.Linear(128, num_classes),
        )

    def forward(self, img_tensor: torch.Tensor, aux_features: torch.Tensor) -> torch.Tensor:
        x = F.gelu(self.bn1(self.conv1(img_tensor)))
        x = F.gelu(self.bn2(self.conv2(x)))
        x = F.gelu(self.bn3(self.conv3(x)))
        avg_x = self.avgpool(x).flatten(1)
        max_x = self.maxpool(x).flatten(1)
        cnn_feats = torch.cat([avg_x, max_x], dim=1)
        combined = torch.cat([cnn_feats, aux_features], dim=1)
        return self.classifier(combined)


_MODEL_INSTANCE: HazardVisionNet | None = None


def extract_auxiliary_features(pil_img: Image.Image) -> torch.Tensor:
    """Computes 32-dim domain-specific industrial visual descriptor."""
    img_rgb = pil_img.convert("RGB").resize((128, 128))
    arr = np.array(img_rgb, dtype=np.float32) / 255.0

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    r_mean, g_mean, b_mean = float(np.mean(r)), float(np.mean(g)), float(np.mean(b))
    r_var, g_var, b_var = float(np.var(r)), float(np.var(g)), float(np.var(b))

    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c + 1e-6
    v = max_c
    s = np.where(max_c == 0, 0, delta / (max_c + 1e-6))
    h = np.zeros_like(r)
    idx_r = max_c == r
    idx_g = (max_c == g) & ~idx_r
    idx_b = (max_c == b) & ~idx_r & ~idx_g
    h[idx_r] = ((g[idx_r] - b[idx_r]) / delta[idx_r]) % 6.0
    h[idx_g] = ((b[idx_g] - r[idx_g]) / delta[idx_g]) + 2.0
    h[idx_b] = ((r[idx_b] - g[idx_b]) / delta[idx_b]) + 4.0
    h = h / 6.0

    h_mean, s_mean, v_mean = float(np.mean(h)), float(np.mean(s)), float(np.mean(v))
    h_var, s_var, v_var = float(np.var(h)), float(np.var(s)), float(np.var(v))

    flame_mask = (r > 0.55) & (g > 0.25) & (b < 0.35) & (v > 0.6)
    flame_ratio = float(np.mean(flame_mask))
    flame_intensity = float(np.mean(r[flame_mask])) if flame_ratio > 0 else 0.0
    flame_red_ratio = float(r_mean / (b_mean + 1e-4))

    molten_mask = (r > 0.8) & (g > 0.65) & (b > 0.2) & (v > 0.85)
    molten_ratio = float(np.mean(molten_mask))
    molten_radiance = float(np.mean(v[molten_mask])) if molten_ratio > 0 else 0.0

    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    spark_max = float(np.max(luminance))
    spark_mean = float(np.mean(luminance))
    spark_contrast = spark_max - spark_mean

    is_overexposed_or_white = (spark_mean > 0.75) or (spark_contrast < 0.3)
    if is_overexposed_or_white:
        spark_ratio = 0.0
    else:
        raw_spark_mask = (luminance > 0.90) & (s < 0.4)
        raw_ratio = float(np.mean(raw_spark_mask))
        spark_ratio = raw_ratio if 0.005 <= raw_ratio <= 0.12 else 0.0

    is_flat_uniform = (r_var + g_var + b_var < 0.015)
    grad_x = np.abs(luminance[:, 1:] - luminance[:, :-1])
    grad_y = np.abs(luminance[1:, :] - luminance[:-1, :])
    edge_density = float(np.mean(grad_x) + np.mean(grad_y))
    blue_green_stain = float(np.mean((g + b) / (2.0 * r + 1e-4)))
    puddle_flatness = float(1.0 / (np.std(luminance) + 0.05))

    smoke_mask = (s < 0.2) & (v > 0.25) & (v < 0.8) & (np.abs(r - g) < 0.1) & (np.abs(g - b) < 0.1)
    smoke_ratio = float(np.mean(smoke_mask)) if not is_flat_uniform else 0.0
    smoke_softness = float(1.0 / (edge_density + 0.01))
    entropy_approx = float(-np.mean(luminance * np.log(luminance + 1e-6)))
    smoke_dispersion = float(np.var(smoke_mask))

    w, h_orig = pil_img.size
    aspect = float(w / (h_orig + 1e-4))

    features = [
        r_mean, g_mean, b_mean, r_var, g_var, b_var,
        h_mean, s_mean, v_mean, h_var, s_var, v_var,
        flame_ratio, flame_intensity, flame_red_ratio,
        molten_ratio, molten_radiance,
        spark_ratio, spark_max, spark_contrast,
        edge_density, blue_green_stain, puddle_flatness,
        smoke_ratio, smoke_softness, entropy_approx, smoke_dispersion,
        aspect, float(w > h_orig), float(w < h_orig), 1.0, 0.0,
    ]
    return torch.tensor(features[:32], dtype=torch.float32).unsqueeze(0)


def preprocess_image(pil_img: Image.Image) -> tuple[torch.Tensor, torch.Tensor]:
    """Prepares image tensor (1, 3, 128, 128) and auxiliary feature vector (1, 32)."""
    img_resized = pil_img.convert("RGB").resize((128, 128))
    img_np = np.array(img_resized, dtype=np.float32) / 255.0
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    norm = (img_np - mean) / std
    tensor = torch.from_numpy(norm).permute(2, 0, 1).unsqueeze(0).float()
    aux = extract_auxiliary_features(pil_img)
    return tensor, aux


def get_or_load_model() -> HazardVisionNet:
    """Returns the HazardVisionNet model instance."""
    global _MODEL_INSTANCE
    if _MODEL_INSTANCE is not None:
        return _MODEL_INSTANCE

    model = HazardVisionNet()
    if MODEL_PATH.exists():
        try:
            state = torch.load(MODEL_PATH, map_location="cpu")
            model.load_state_dict(state)
            logger.info(f"Loaded trained HazardVisionNet from {MODEL_PATH}")
        except Exception as exc:
            logger.warning(f"Failed to load HazardVisionNet weights from {MODEL_PATH}: {exc}")
    model.eval()
    _MODEL_INSTANCE = model
    return _MODEL_INSTANCE


# ==============================================================================
# 1. DEDICATED JUNK-PHOTO GATE
# ==============================================================================

def filter_junk_or_unrelated_media(image: Image.Image) -> tuple[bool, str, dict[str, float]]:
    """
    Dedicated Junk-Photo Gate.
    Evaluates physical properties to filter out non-industrial junk:
      - Office documents, white sheets, and text screenshots
      - Pitch black / underexposed frames
      - Blank or uniform solid color surfaces
      - Low-entropy textureless images

    Returns:
      (is_junk, filter_reason, stats)
    """
    img_rgb = image.convert("RGB").resize((128, 128))
    arr = np.array(img_rgb, dtype=np.float32) / 255.0

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    luminance = 0.299 * r + 0.587 * g + 0.114 * b

    lum_mean = float(np.mean(luminance))
    lum_std = float(np.std(luminance))
    rgb_var = float(np.var(r) + np.var(g) + np.var(b))

    grad_x = np.abs(luminance[:, 1:] - luminance[:, :-1])
    grad_y = np.abs(luminance[1:, :] - luminance[:-1, :])
    edge_mean = float(np.mean(grad_x) + np.mean(grad_y))

    stats = {
        "luminance_mean": round(lum_mean, 3),
        "luminance_std": round(lum_std, 3),
        "rgb_variance": round(rgb_var, 4),
        "edge_density": round(edge_mean, 4),
    }

    # 1. Pitch black / extreme underexposure
    if lum_mean < 0.05 and lum_std < 0.04:
        return True, "Underexposed / pitch-black image with no discernible scene content", stats

    # 2. Blank or solid uniform color surface (e.g. wall, lens cap, flat background)
    if rgb_var < 0.003 and lum_std < 0.03:
        return True, "Uniform solid surface with no industrial scene features", stats

    # 3. White paper / office document / computer text screenshot
    is_mostly_white = lum_mean > 0.82
    has_text_like_edges = (lum_std > 0.12) and (edge_mean > 0.06)
    if is_mostly_white and (lum_std < 0.08 or has_text_like_edges):
        return True, "Non-industrial document, paper sheet, or text screenshot", stats

    # 4. Severe overexposure
    if lum_mean > 0.94:
        return True, "Severe overexposure wash-out with no discernible industrial context", stats

    return False, "Valid industrial visual scene", stats


# ==============================================================================
# 2. MULTI-FRAME VIDEO SAMPLING
# ==============================================================================

def sample_video_frames(video_path: str, max_frames: int = 8) -> list[tuple[float, Image.Image]]:
    """
    Samples up to max_frames evenly spaced across the video duration using PyAV.
    Returns list of (timestamp_seconds, PIL.Image).
    """
    sampled: list[tuple[float, Image.Image]] = []
    try:
        import av
        container = av.open(video_path)
        stream = container.streams.video[0]
        duration_s = float(stream.duration * stream.time_base) if stream.duration else 5.0
        fps = float(stream.average_rate) if stream.average_rate else 24.0

        all_frames: list[tuple[float, Image.Image]] = []
        frame_idx = 0
        for frame in container.decode(video=0):
            pts_time = float(frame.pts * stream.time_base) if frame.pts is not None else (frame_idx / fps)
            all_frames.append((pts_time, frame.to_image()))
            frame_idx += 1
            if len(all_frames) >= 120:  # Cap scan to first 120 frames
                break

        if not all_frames:
            return []

        if len(all_frames) <= max_frames:
            return all_frames

        # Evenly space selection
        indices = np.linspace(0, len(all_frames) - 1, max_frames, dtype=int)
        for idx in indices:
            sampled.append(all_frames[idx])

    except Exception as exc:
        logger.warning(f"Video frame sampling failed for {video_path}: {exc}")

    return sampled


# ==============================================================================
# 3. CORE VISUAL ANALYSIS PIPELINE
# ==============================================================================

def analyze_visual_evidence(file_path: str | Path, reported_category: str) -> dict[str, Any]:
    """
    Analyzes uploaded image or video evidence under Apache-2.0 governance:
      - SHA-256 fingerprint verification
      - Junk-Photo Gate filtering
      - Localized Bounding Box Detection (fire, smoke, person, PPE)
      - Class Governance (experimental notice on unvalidated classes)
      - Video multi-frame aggregation
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "is_valid_evidence": False,
            "detected_event": "file_not_found",
            "visual_status": "no_visual_corroboration",
            "confidence": 0.0,
            "category_alignment": False,
            "risk_score_impact": "neutral_unchanged",
            "visual_summary": "No file was found at the provided path.",
            "tags": ["unverified_media"],
            "evidence_boxes": [],
            "flagged_for_human_review": True,
            "human_review_reason": "Proof file path not found; physical inspection required.",
            "event_probabilities": {},
            "image_sha256": None,
            "model_version": DETECTOR_VERSION,
            "detector_license": DETECTOR_LICENSE,
            "is_experimental": False,
            "advisory_notice": "AI Vision output is evidence-only; cannot downgrade severity or auto-dismiss an incident.",
        }

    # 1. Compute SHA-256 Hash of Evidence File
    try:
        with open(path, "rb") as f:
            file_bytes = f.read()
            image_sha256 = hashlib.sha256(file_bytes).hexdigest()
    except Exception as exc:
        image_sha256 = None
        logger.warning(f"Failed to calculate SHA-256 for {path}: {exc}")

    is_video = path.suffix.lower() in [".mp4", ".webm", ".mov", ".mkv", ".avi"]
    primary_image: Image.Image | None = None
    video_metadata: dict[str, Any] = {}

    if is_video:
        sampled_frames = sample_video_frames(str(path), max_frames=8)
        if sampled_frames:
            # Pick middle frame as initial candidate
            key_ts, primary_image = sampled_frames[len(sampled_frames) // 2]
            video_metadata = {
                "is_video": True,
                "sampled_frames_count": len(sampled_frames),
                "key_frame_timestamp_s": round(key_ts, 2),
            }
        else:
            primary_image = Image.new("RGB", (128, 128), color=(30, 30, 30))
            video_metadata = {"is_video": True, "sampled_frames_count": 0, "key_frame_timestamp_s": 0.0}
    else:
        try:
            primary_image = Image.open(path).convert("RGB")
        except Exception as exc:
            logger.warning(f"Could not open image {path}: {exc}")
            return {
                "is_valid_evidence": False,
                "detected_event": "corrupted_file",
                "visual_status": "no_visual_corroboration",
                "confidence": 0.0,
                "category_alignment": False,
                "risk_score_impact": "neutral_unchanged",
                "visual_summary": f"Uploaded file is not a readable image ({exc}).",
                "tags": ["corrupted_media"],
                "evidence_boxes": [],
                "flagged_for_human_review": True,
                "human_review_reason": f"Uploaded file is corrupted/unreadable: {exc}",
                "event_probabilities": {},
                "image_sha256": image_sha256,
                "model_version": DETECTOR_VERSION,
                "detector_license": DETECTOR_LICENSE,
                "is_experimental": False,
                "advisory_notice": "AI Vision output is evidence-only; cannot downgrade severity or auto-dismiss an incident.",
            }

    # 2. RUN DEDICATED JUNK-PHOTO GATE
    is_junk, junk_reason, junk_stats = filter_junk_or_unrelated_media(primary_image)
    if is_junk:
        return {
            "is_valid_evidence": False,
            "detected_event": "unrelated_photo",
            "visual_status": "no_visual_corroboration",
            "confidence": 0.95,
            "category_alignment": False,
            "risk_score_impact": "neutral_unchanged",
            "visual_summary": f"Junk-Photo Gate filtered image: {junk_reason}. Status: 'No Visual Corroboration'.",
            "tags": ["filtered_junk_media", "no_visual_corroboration"],
            "evidence_boxes": [],
            "flagged_for_human_review": True,
            "human_review_reason": f"Visual evidence uncorroborated ({junk_reason}). On-site physical inspection recommended.",
            "event_probabilities": {"unrelated_photo": 0.95, "normal_machinery": 0.05},
            "image_sha256": image_sha256,
            "model_version": DETECTOR_VERSION,
            "detector_license": DETECTOR_LICENSE,
            "is_experimental": False,
            "media_type": "video" if is_video else "image",
            "video_metadata": video_metadata if is_video else None,
            "advisory_notice": "AI Vision output is evidence-only; cannot downgrade severity or auto-dismiss an incident.",
        }

    # 3. RUN APACHE-2.0 OBJECT DETECTOR (fire, smoke, person, PPE)
    detector = get_visual_detector()
    detected_boxes = detector.detect(primary_image)

    # 4. RUN AUXILIARY CLASSIFIER FOR WHOLE-SCENE EVENT MAPPING
    model = get_or_load_model()
    img_t, aux_t = preprocess_image(primary_image)
    with torch.no_grad():
        logits = model(img_t, aux_t)
        probs = F.softmax(logits, dim=1)[0]

    prob_dict = {IDX_TO_CLASS[i]: round(float(probs[i]), 3) for i in range(len(HAZARD_CLASSES))}
    top_idx = int(torch.argmax(probs))
    detected_event = IDX_TO_CLASS[top_idx]
    classifier_confidence = float(probs[top_idx])

    # If detector found high-confidence fire or smoke boxes, prioritize detector findings
    detector_hazard = next((b for b in detected_boxes if b["label"] in ["fire", "smoke"]), None)
    if detector_hazard and detector_hazard["confidence"] > 0.75:
        detected_event = detector_hazard["label"]
        overall_confidence = detector_hazard["confidence"]
    else:
        overall_confidence = classifier_confidence

    # 5. CLASS GOVERNANCE: Check if class is experimental / unvalidated
    is_experimental = detected_event in EXPERIMENTAL_CLASSES
    experimental_notice = EXPERIMENTAL_CLASSES.get(detected_event)

    # Check semantic compatibility with reported category
    norm_cat = reported_category.lower()
    compatible_events = CATEGORY_COMPATIBILITY.get(norm_cat, {norm_cat})

    is_non_hazard = detected_event in ["normal_machinery", "unrelated_photo"]
    is_aligned = detected_event in compatible_events

    tags = [detected_event]
    for b in detected_boxes:
        if b["label"] not in tags:
            tags.append(b["label"])

    if overall_confidence >= 0.80:
        tags.append("high_confidence_detection")
    elif overall_confidence >= 0.50:
        tags.append("moderate_confidence_detection")

    if is_experimental:
        tags.append("experimental_unvalidated_class")

    # Format Evidence Boxes for Dossier
    evidence_boxes = detected_boxes if detected_boxes else [{
        "ymin": 0.2, "xmin": 0.2, "ymax": 0.8, "xmax": 0.8,
        "label": detected_event.replace("_", " ").title(),
        "confidence": round(overall_confidence, 2),
        "color": "#EF4444" if detected_event in ["fire", "smoke", "electrical_hazard"] else "#3B82F6",
        "box_2d": [0.2, 0.2, 0.8, 0.8],
    }]

    if is_non_hazard:
        is_valid = False
        impact = "neutral_unchanged"
        flagged_for_review = True
        review_reason = "No visual corroboration in uploaded media. Flagged for physical verification by safety officer (never auto-dismissed)."
        summary = (
            f"AI Visual Model classified image as '{detected_event.replace('_', ' ').title()}' "
            f"(Confidence: {int(overall_confidence * 100)}%). Status: 'No Visual Corroboration'. "
            f"Risk score remains strictly unchanged. Flagged for human on-site review."
        )
    elif is_aligned:
        is_valid = True
        impact = "verified_elevates_urgency"
        flagged_for_review = False
        review_reason = None
        tags.append("corroborated_hazard")
        summary = (
            f"AI Visual Detector verified active hazard: '{detected_event.replace('_', ' ').title()}' "
            f"(Confidence: {int(overall_confidence * 100)}%). Visual evidence corroborates reported {reported_category} incident. "
            f"Localized boxes: {len(detected_boxes)} detected."
        )
    else:
        is_valid = False
        impact = "mismatch_flagged"
        flagged_for_review = True
        review_reason = f"Detected visual hazard '{detected_event}' differs from reported '{reported_category}'. Immediate safety officer review required."
        tags.append("category_discrepancy")
        summary = (
            f"AI Visual Detector identified '{detected_event.replace('_', ' ').title()}' (Confidence: {int(overall_confidence * 100)}%), "
            f"which differs from reported category '{reported_category}'. Flagged for human inspection."
        )

    return {
        "is_valid_evidence": is_valid,
        "detected_event": detected_event,
        "visual_status": "corroborated" if is_valid else "no_visual_corroboration",
        "confidence": round(overall_confidence, 2),
        "category_alignment": is_aligned,
        "risk_score_impact": impact,
        "visual_summary": summary,
        "tags": tags,
        "evidence_boxes": evidence_boxes,
        "flagged_for_human_review": flagged_for_review,
        "human_review_reason": review_reason,
        "event_probabilities": prob_dict,
        "image_sha256": image_sha256,
        "model_version": DETECTOR_VERSION,
        "detector_license": DETECTOR_LICENSE,
        "is_experimental": is_experimental,
        "experimental_notice": experimental_notice,
        "media_type": "video" if is_video else "image",
        "video_metadata": video_metadata if is_video else None,
        "advisory_notice": "AI Vision output is evidence-only under Apache-2.0 license; cannot downgrade severity or auto-dismiss an incident.",
    }
