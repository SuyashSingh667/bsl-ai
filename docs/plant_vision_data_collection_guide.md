# Industrial Plant Computer Vision: Data Collection & Annotation Guide

**Facility**: Steel Authority of India Limited (SAIL) — Bokaro Steel Plant (BSL)  
**Target Applications**: BSL AI Visual Hazard Localization & PPE Compliance Subsystems  
**Date**: September 2026  
**Audience**: Safety Officers, CCTV Network Engineers, Industrial Computer Vision Practitioners

---

## 1. Background & Hazard Class Governance

In heavy metallurgy facilities (blast furnaces, basic oxygen furnaces, continuous casting, hot rolling mills), AI models cannot rely on generic internet imagery. Hazards like **molten metal breakout**, **acid bath spills**, and **overhead crane cable ruptures** have unique radiometric and physical profiles.

### 1.1 Validated vs. Experimental Classes
| Class Name | Status in BSL AI | Training Data Provenance | UI Treatment |
|---|---|---|---|
| `fire` | **Validated** | D-Fire, Flame-Detection Datasets | Corroborative Alert |
| `smoke` | **Validated** | Industrial Chimney & Wildfire Plumes | Corroborative Alert |
| `person` | **Validated** | COCO, CrowdHuman | Localization Box |
| `hard_hat` | **Validated** | SHWD (Safety Helmet Wearing Dataset) | PPE Compliance Tag |
| `safety_vest` | **Validated** | Pictor-v3 High-Vis Vest Dataset | PPE Compliance Tag |
| `molten_metal_spill` | **Experimental** | ⚠️ Zero public datasets | **Explicit Warning Banner** |
| `chemical_spill` | **Experimental** | ⚠️ Acid plant specific | **Explicit Warning Banner** |
| `crane_lifting_failure` | **Experimental** | ⚠️ Heavy machine bay specific | **Explicit Warning Banner** |

> [!CAUTION]
> **Safety Rule on Unvalidated Classes**:
> Any prediction labeled `molten_metal_spill`, `chemical_spill`, or `crane_lifting_failure` is classified as `is_experimental: True` in BSL AI until verified on-site Bokaro datasets are trained and audited by the Head of Plant Safety. Operators are never shown uncertified detections as reliable facts.

---

## 2. Directory Structure

Datasets must be collected, sanitized, and stored following the standard industrial layout:

```text
data/plant_dataset/
├── README.md                          # Dataset manifest & safety officer signoff
├── classes.yaml                       # Class definitions & integer mappings
├── train/
│   ├── images/
│   │   ├── BSL_BF1_20260901_001.jpg
│   │   └── ...
│   └── labels/
│       ├── BSL_BF1_20260901_001.txt   # YOLO format annotation
│       └── ...
├── val/
│   ├── images/
│   └── labels/
└── test/
    ├── images/
    └── labels/
```

---

## 3. Class Index Mapping (`classes.yaml`)

```yaml
# BSL AI Plant Vision Class Definitions
names:
  0: fire
  1: smoke
  2: person
  3: hard_hat
  4: safety_vest
  5: molten_metal_spill    # Requires Casthouse approval
  6: chemical_spill        # Requires Acid Regeneration Plant approval
  7: crane_lifting_failure # Requires SMS-II / Machine Shop approval

nc: 8
license: Apache-2.0
reviewed_by_safety_officer: true
```

---

## 4. Annotation Standards

### 4.1 YOLO Bounding Box Format (`.txt`)
Each image in `images/` must have a corresponding `.txt` file in `labels/` with identical base name.
Each line contains:
```text
<class_id> <x_center> <y_center> <width> <height>
```
* Coordinates must be normalized between `0.000000` and `1.000000` relative to image width and height.
* Example:
  ```text
  0 0.482500 0.612000 0.125000 0.240000
  2 0.450000 0.550000 0.150000 0.420000
  3 0.452000 0.360000 0.055000 0.062000
  ```

### 4.2 COCO Format (`annotations.json`)
For transformer detectors (RT-DETR) or evaluation suites, annotations should also be exported to COCO JSON format:
```json
{
  "images": [{"id": 1, "file_name": "BSL_BF1_001.jpg", "width": 1920, "height": 1080}],
  "annotations": [
    {
      "id": 1,
      "image_id": 1,
      "category_id": 0,
      "bbox": [862, 531, 240, 259],
      "area": 62160,
      "iscrowd": 0
    }
  ],
  "categories": [{"id": 0, "name": "fire"}, {"id": 1, "name": "smoke"}, ...]
}
```

---

## 5. Sample Size Requirements & Environmental Variations

To achieve acceptable generalization without overfitting or false positives:

| Class | Minimum Training Images | Minimum Validation Images | Environmental Conditions Required |
|---|---|---|---|
| `molten_metal_spill` | **500** | 100 | Day & Night, Casthouse floor, Torpedo ladle transfer, Tundish overflow, bright glowing liquid vs cooling crust |
| `chemical_spill` | **400** | 80 | Acid regeneration plant, Pickling line, wet puddle reflections vs corrosive froth |
| `fire` | **600** | 120 | Coke ovens gas flame, Cable trench fire, Conveyor belt friction fire |
| `smoke` | **600** | 120 | White steam vs black soot plume vs yellow BF gas plume |
| `ppe` (`hard_hat`, `safety_vest`) | **1,000** | 200 | Distant workers (low resolution), dirty vests, steam haze, backlit lighting |

### 5.1 Mandatory Real-World Variations:
1. **Dust & Fly Ash**: Bokaro blast furnace and sinter plant air has airborne dust particulates that trigger false smoke alarms on uncalibrated models.
2. **Sodium Vapor vs. High-Bay LED**: Older plant bays use 2000K orange sodium lamps that resemble fire glow; new bays use 5500K LED. Both must be sampled.
3. **Steam vs. Toxic Fumes**: Quenching towers produce dense white water vapor (benign) which must not be confused with chemical toxic smoke.

---

## 6. Worker Privacy & Data Sanitation Protocol

1. **Face Blurring**: All captured images of workers must have facial regions blurred (`sigma=15` Gaussian blur) prior to inclusion in the public or shared training dataset.
2. **Employee Badge Masking**: Gate passes, biometric card lanyards, and vehicle registration numbers must be redacted to comply with Indian Digital Personal Data Protection Act (DPDPA 2023).
3. **Restricted Zone Redaction**: High-security defense production cells or classified electrical substation switchboards must not be photographed without written clearance from the General Manager (Safety).
