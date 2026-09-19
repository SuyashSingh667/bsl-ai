"""
AI Visual Hazard Analysis & Event Classification Engine.
Employs a deep PyTorch neural network (HazardVisionNet) combining multi-scale
convolutional representations with color-space thermal profiles and spatial
frequency signatures to detect industrial hazards:
  - Fire & combustion flames
  - Dense smoke plumes
  - Electrical arc flash & high-voltage sparking
  - Chemical spills & corrosive puddles
  - Molten metal & slag breakout
  - Mechanical failure & torn equipment
  - Vehicle collisions
  - Normal plant machinery (no hazard)
  - Unrelated / non-industrial photos (selfies, documents, objects)

Prevents arbitrary risk score inflation by verifying semantic alignment
between the uploaded image and the reported incident category.
"""

from __future__ import annotations

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
    "ppe_violation": {"normal_machinery"},
}


class HazardVisionNet(nn.Module):
    """
    Hybrid Convolutional & Spectral Feature Neural Network for Industrial Hazard Detection.
    Combines:
      1. Multi-scale 2D CNN feature map (local edge, texture, spatial gradients)
      2. 32-dimensional chromatic and thermal profile vector (HSV flame ratios, luminance peaks, smoke entropy)
    """

    def __init__(self, num_classes: int = len(HAZARD_CLASSES)):
        super().__init__()
        # Conv block 1: 3 -> 32
        self.conv1 = nn.Conv2d(3, 32, kernel_size=5, stride=2, padding=2)
        self.bn1 = nn.BatchNorm2d(32)

        # Conv block 2: 32 -> 64
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, stride=2, padding=1)
        self.bn2 = nn.BatchNorm2d(64)

        # Conv block 3: 64 -> 128
        self.conv3 = nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1)
        self.bn3 = nn.BatchNorm2d(128)

        # Global pooling
        self.avgpool = nn.AdaptiveAvgPool2d((2, 2))
        self.maxpool = nn.AdaptiveMaxPool2d((2, 2))

        # CNN feature dimension: 128 * 4 * 2 = 1024
        cnn_feat_dim = 128 * 4 * 2

        # Chromatic & spectral auxiliary input dimension: 32
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
        logits = self.classifier(combined)
        return logits


_MODEL_INSTANCE: HazardVisionNet | None = None


def extract_auxiliary_features(pil_img: Image.Image) -> torch.Tensor:
    """
    Computes 32-dim domain-specific industrial visual descriptor:
      - RGB means & variances (6 dims)
      - HSV means & variances (6 dims)
      - Red-Yellow flame dominance index (3 dims)
      - Molten radiation index (2 dims)
      - Arc spark luminance peak density (3 dims)
      - Chemical liquid sheen / puddle contrast (3 dims)
      - Smoke diffusion gradient / entropy (4 dims)
      - Aspect ratio & padding (5 dims)
    """
    img_rgb = pil_img.convert("RGB").resize((128, 128))
    arr = np.array(img_rgb, dtype=np.float32) / 255.0

    r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    # RGB statistics
    r_mean, g_mean, b_mean = float(np.mean(r)), float(np.mean(g)), float(np.mean(b))
    r_var, g_var, b_var = float(np.var(r)), float(np.var(g)), float(np.var(b))

    # HSV conversion
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    delta = max_c - min_c + 1e-6

    # Value
    v = max_c
    # Saturation
    s = np.where(max_c == 0, 0, delta / (max_c + 1e-6))
    # Hue estimation
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

    # Flame dominance: high red, moderate green, low blue, high brightness
    flame_mask = (r > 0.55) & (g > 0.25) & (b < 0.35) & (v > 0.6)
    flame_ratio = float(np.mean(flame_mask))
    flame_intensity = float(np.mean(r[flame_mask])) if flame_ratio > 0 else 0.0
    flame_red_ratio = float(r_mean / (b_mean + 1e-4))

    # Molten steel: intense glowing yellow/white with high saturation
    molten_mask = (r > 0.8) & (g > 0.65) & (b > 0.2) & (v > 0.85)
    molten_ratio = float(np.mean(molten_mask))
    molten_radiance = float(np.mean(v[molten_mask])) if molten_ratio > 0 else 0.0

    # Electrical arc / sparks: intense localized pinpoint white/blue highlights against darker ambient
    luminance = 0.299 * r + 0.587 * g + 0.114 * b
    spark_max = float(np.max(luminance))
    spark_mean = float(np.mean(luminance))
    spark_contrast = spark_max - spark_mean

    # A genuine spark is high contrast (>0.4) and localized (0.5% - 10% of pixels).
    # Large white areas (documents, walls, overexposure) have low contrast or >15% coverage.
    is_overexposed_or_white = (spark_mean > 0.75) or (spark_contrast < 0.3)
    if is_overexposed_or_white:
        spark_ratio = 0.0
    else:
        raw_spark_mask = (luminance > 0.90) & (s < 0.4)
        raw_ratio = float(np.mean(raw_spark_mask))
        spark_ratio = raw_ratio if 0.005 <= raw_ratio <= 0.12 else 0.0

    # Flat or uniform image (blank, document, wall) detection
    is_flat_uniform = (r_var + g_var + b_var < 0.015)

    # Chemical spill: reflective puddle or localized discoloration
    grad_x = np.abs(luminance[:, 1:] - luminance[:, :-1])
    grad_y = np.abs(luminance[1:, :] - luminance[:-1, :])
    edge_density = float(np.mean(grad_x) + np.mean(grad_y))
    blue_green_stain = float(np.mean((g + b) / (2.0 * r + 1e-4)))
    puddle_flatness = float(1.0 / (np.std(luminance) + 0.05))

    # Smoke: low contrast, diffuse grayish veil across large regions
    smoke_mask = (s < 0.2) & (v > 0.25) & (v < 0.8) & (np.abs(r - g) < 0.1) & (np.abs(g - b) < 0.1)
    smoke_ratio = float(np.mean(smoke_mask)) if not is_flat_uniform else 0.0
    smoke_softness = float(1.0 / (edge_density + 0.01))
    entropy_approx = float(-np.mean(luminance * np.log(luminance + 1e-6)))
    smoke_dispersion = float(np.var(smoke_mask))

    # Aspect and normalization
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
    # Mean-std normalization
    mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
    std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
    norm = (img_np - mean) / std
    tensor = torch.from_numpy(norm).permute(2, 0, 1).unsqueeze(0).float()
    aux = extract_auxiliary_features(pil_img)
    return tensor, aux


def get_or_load_model() -> HazardVisionNet:
    """Returns the trained HazardVisionNet model, loading from disk or initializing."""
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
    else:
        logger.info(f"No trained weights found at {MODEL_PATH}; initializing fresh architecture.")

    model.eval()
    _MODEL_INSTANCE = model
    return _MODEL_INSTANCE


def extract_frame_from_video(video_path: str) -> Image.Image | None:
    """Extracts a middle video frame from a video file using av or returns None."""
    try:
        import av
        container = av.open(video_path)
        frames = []
        for frame in container.decode(video=0):
            frames.append(frame.to_image())
            if len(frames) >= 15:
                break
        if frames:
            return frames[len(frames) // 2]
    except Exception as exc:
        logger.warning(f"Failed to decode video frame from {video_path}: {exc}")
    return None


def analyze_visual_evidence(file_path: str | Path, reported_category: str) -> dict[str, Any]:
    """
    Analyzes an uploaded photographic or video proof file.
    Determines:
      - Detected visual hazard event
      - Model confidence
      - Alignment with reported category
      - Whether visual evidence should increase risk score or remain neutral
    """
    path = Path(file_path)
    if not path.exists():
        return {
            "is_valid_evidence": False,
            "detected_event": "file_not_found",
            "confidence": 0.0,
            "category_alignment": False,
            "risk_score_impact": "neutral",
            "visual_summary": "No file was found at the provided path.",
            "event_probabilities": {},
        }

    # Handle video vs image
    is_video = path.suffix.lower() in [".mp4", ".webm", ".mov", ".mkv", ".avi"]
    pil_img: Image.Image | None = None

    if is_video:
        pil_img = extract_frame_from_video(str(path))
        if pil_img is None:
            # Fallback placeholder if video is 0-byte or corrupted
            pil_img = Image.new("RGB", (128, 128), color=(30, 30, 30))
    else:
        try:
            pil_img = Image.open(path).convert("RGB")
        except Exception as exc:
            logger.warning(f"Could not open image {path}: {exc}")
            return {
                "is_valid_evidence": False,
                "detected_event": "corrupted_file",
                "confidence": 0.0,
                "category_alignment": False,
                "risk_score_impact": "neutral",
                "visual_summary": f"Uploaded file is not a readable image ({exc}).",
                "event_probabilities": {},
            }

    # Preprocess & run model inference
    model = get_or_load_model()
    img_t, aux_t = preprocess_image(pil_img)

    with torch.no_grad():
        logits = model(img_t, aux_t)
        probs = F.softmax(logits, dim=1)[0]

    prob_dict = {IDX_TO_CLASS[i]: round(float(probs[i]), 3) for i in range(len(HAZARD_CLASSES))}
    top_idx = int(torch.argmax(probs))
    detected_event = IDX_TO_CLASS[top_idx]
    confidence = float(probs[top_idx])

    # Check semantic compatibility with reported category
    norm_cat = reported_category.lower()
    compatible_events = CATEGORY_COMPATIBILITY.get(norm_cat, {norm_cat})

    # Non-hazard classifications
    is_non_hazard = detected_event in ["normal_machinery", "unrelated_photo"]
    is_aligned = detected_event in compatible_events

    if is_non_hazard:
        is_valid = False
        impact = "neutral_uninflated"
        summary = (
            f"AI Visual Model classified image as '{detected_event.replace('_', ' ').title()}' "
            f"(Confidence: {int(confidence * 100)}%). No active industrial hazard was detected in this frame. "
            f"Calculated risk score is held strictly neutral and NOT inflated."
        )
    elif is_aligned:
        is_valid = True
        impact = "verified_increases_risk"
        summary = (
            f"AI Visual Model verified active hazard: '{detected_event.replace('_', ' ').title()}' "
            f"(Confidence: {int(confidence * 100)}%). Visual evidence corroborates reported {reported_category} incident. "
            f"Verified visual confirmation applied to safety risk score."
        )
    else:
        # Hazard detected, but does not match reported category (e.g. fire uploaded for vehicle collision)
        is_valid = False
        impact = "mismatch_flagged"
        summary = (
            f"AI Visual Model detected '{detected_event.replace('_', ' ').title()}' (Confidence: {int(confidence * 100)}%), "
            f"which does not match the reported '{reported_category}' category. "
            f"Flagged for manual safety officer review; risk score not automatically elevated."
        )

    return {
        "is_valid_evidence": is_valid,
        "detected_event": detected_event,
        "confidence": round(confidence, 2),
        "category_alignment": is_aligned,
        "risk_score_impact": impact,
        "visual_summary": summary,
        "event_probabilities": prob_dict,
        "media_type": "video" if is_video else "image",
    }
