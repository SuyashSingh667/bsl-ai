# Vision Model License Evaluation & Architectural Choice

**Project**: BSL AI — Voice-First Industrial Safety Incident Platform  
**Target Deployment**: Steel Authority of India Limited (SAIL) — Bokaro Steel Plant  
**Date**: September 2026  
**Document Status**: Approved Architecture Decision Record (ADR)

---

## 1. Executive Summary & Objective

In Phase 3 of the BSL AI modernization, the visual hazard module transitions from a monolithic whole-image CNN classifier (`HazardVisionNet`) to an object detector capable of localizing hazards (`fire`, `smoke`, `person`, `ppe`) with bounding box overlays for auditable incident dossiers.

Before deploying any computer vision model into an enterprise industrial platform, open-source software licenses must be rigorously scrutinized. Deploying models with viral copyleft licenses into a proprietary intranet or cloud backend can expose enterprise source code to forced disclosure or legal liabilities.

This document evaluates candidate detection architectures against **intellectual property constraints, enterprise licensing compliance, edge/server performance, and life-safety reliability**.

---

## 2. License Analysis of Candidate Architectures

### 2.1 Ultralytics YOLO (YOLOv5, YOLOv8, YOLOv11)
* **License**: **GNU Affero General Public License v3.0 (AGPL-3.0)**
* **Copyright Holder**: Ultralytics Inc.
* **Key Provision (Section 13 — Remote Network Interaction)**:
  > *"If you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network ... an opportunity to receive the Corresponding Source of your version..."*
* **Enterprise Risk Analysis**:
  1. **Network Copyleft Trigger**: BSL AI serves plant supervisors, command dispatchers, and mobile workers over HTTP/WebSocket networks. Under AGPL-3.0, any proprietary backend (FastAPI, SQLite/PostgreSQL schemas, RAG engines, proprietary SOP retrieval pipelines) that links to or runs Ultralytics code can be construed as a combined derivative work.
  2. **Proprietary Code Disclosure**: SAIL or platform operators could be legally compelled to release all accompanying backend source code under AGPL-3.0.
  3. **Commercial Enterprise Exemption Cost**: Ultralytics offers proprietary commercial licenses, but these require recurring enterprise subscriptions with per-seat or per-server fees, creating vendor lock-in.
* **Conclusion**: **REJECTED** for default distribution without an existing corporate enterprise agreement.

---

### 2.2 RT-DETR (Real-Time DEtection TRansformer — Baidu / Lyglinj / Hugging Face)
* **License**: **Apache License 2.0**
* **Copyright Holders**: Baidu Inc. / Open-Source Contributors
* **Key Provisions**:
  - Grants perpetual, worldwide, non-exclusive, no-charge, royalty-free patent and copyright license.
  - Allows commercial use, modification, distribution, and private/internal use without requiring derived works to be open-sourced.
* **Technical Advantages**:
  1. **NMS-Free Architecture**: Unlike YOLO which relies on heuristic Non-Maximum Suppression (NMS) causing unpredictable latency spikes, RT-DETR uses a direct set-prediction transformer with Hungarian matching, guaranteeing constant-time inference.
  2. **High Accuracy on Industrial Assets**: Superior feature representation on dense, diffuse hazards like smoke plumes and fire boundaries.
  3. **Standard ONNX Export**: Directly compatible with `onnxruntime` across CPU, CUDA, and TensorRT runtimes.
* **Conclusion**: **PRIMARY SELECTION (RECOMMENDED)**.

---

### 2.3 YOLOX (Megvii)
* **License**: **Apache License 2.0**
* **Copyright Holder**: Megvii Technology
* **Key Provisions**: Permissive commercial usage, modification, and integration without copyleft contagion.
* **Technical Advantages**: Anchor-free CNN architecture, lightweight, fast training on custom datasets.
* **Conclusion**: **APPROVED ALTERNATIVE (Permissive)**.

---

### 2.4 Torchvision Object Detectors (Faster R-CNN, MobileNetV3-SSDLite, RetinaNet)
* **License**: **BSD-3-Clause**
* **Copyright Holder**: PyTorch Foundation / Meta Platforms, Inc.
* **Key Provisions**: Fully permissive 3-clause license allowing proprietary commercial usage and binary redistribution with standard copyright attribution.
* **Technical Advantages**: Zero extra dependency overhead; natively available within existing PyTorch installations.
* **Conclusion**: **APPROVED NATIVE BASELINE (Permissive)**.

---

## 3. Comparison Matrix

| Attribute | Ultralytics YOLOv8/v11 | RT-DETR | YOLOX | Torchvision SSDLite |
|---|---|---|---|---|
| **License** | **AGPL-3.0** (Viral Copyleft) | **Apache-2.0** (Permissive) | **Apache-2.0** (Permissive) | **BSD-3-Clause** (Permissive) |
| **Enterprise Network Safe** | ❌ High Risk (Section 13) | ✅ 100% Safe | ✅ 100% Safe | ✅ 100% Safe |
| **Commercial Royalty-Free** | ❌ Requires Paid License | ✅ Free & Open | ✅ Free & Open | ✅ Free & Open |
| **Post-Processing Latency** | Heuristic NMS | ✅ NMS-Free (Deterministic) | Heuristic NMS | Heuristic NMS |
| **ONNX Runtime Support** | Yes | ✅ Native ONNX Export | Yes | Yes |
| **Bounding Box Granularity** | High | High (Transformer Attention) | High | Moderate |
| **BSL Recommendation** | **Prohibited by default** | **Target Architecture** | **Approved Backup** | **Supported Native** |

---

## 4. Architectural Decision Record (ADR)

1. **Standard License Policy**: BSL AI strictly adopts **Apache-2.0** and **BSD-3-Clause** models for all edge and server-side visual detection.
2. **Detector Abstraction Interface**:
   - Define a modular `VisualDetector` interface in `backend/app/services/visual_detector.py`.
   - The detector outputs normalized bounding boxes in standard format: `[ymin, xmin, ymax, xmax]`, class label, confidence score, and visual presentation color.
   - Decoupled from proprietary model weight formats to allow drop-in replacement with certified on-site plant checkpoints.
3. **Auditability in Dossier**:
   - Every inference response embeds `detector_license: "Apache-2.0"` and `model_version: "BSL-Vision-Detector-v2.5 (Apache-2.0 / RT-DETR)"` to provide unambiguous legal and technical provenance in audit trails.
