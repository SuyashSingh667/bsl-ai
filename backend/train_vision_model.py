"""
Training script for HazardVisionNet Industrial Visual Hazard Classifier.
Generates an augmented dataset of industrial hazard signatures and negative controls,
trains the hybrid CNN + spectral neural network, and saves weights to data/models/visual_hazard_classifier.pt.
"""

from __future__ import annotations

import os
import random
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFilter
import torch
import torch.nn as nn
import torch.optim as optim

from app.services.visual_analysis import (
    HAZARD_CLASSES,
    CLASS_TO_IDX,
    HazardVisionNet,
    preprocess_image,
    MODEL_DIR,
    MODEL_PATH,
)

# Ensure model directory exists
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def generate_synthetic_hazard_image(hazard_type: str, size: tuple[int, int] = (128, 128)) -> Image.Image:
    """Generates realistic synthetic visual representations of plant hazard categories."""
    w, h = size
    img = Image.new("RGB", size, color=(40, 44, 52))
    draw = ImageDraw.Draw(img)

    # Base background: industrial metal floor / wall
    for y in range(0, h, 8):
        shade = random.randint(30, 60)
        draw.line([(0, y), (w, y)], fill=(shade, shade + 2, shade + 5), width=1)

    if hazard_type == "fire":
        # Draw dark machinery with active orange/yellow/red flame shapes
        flame_base_x = random.randint(30, 80)
        flame_base_y = random.randint(70, 110)
        for _ in range(random.randint(15, 30)):
            fx = flame_base_x + random.randint(-25, 25)
            fy = flame_base_y + random.randint(-40, 10)
            rad = random.randint(10, 35)
            color = random.choice([
                (255, random.randint(40, 80), 0),      # Deep red-orange
                (255, random.randint(140, 200), 10),   # Vibrant yellow
                (255, random.randint(210, 255), 100),  # Hot core
            ])
            draw.ellipse([fx - rad, fy - rad, fx + rad, fy + rad], fill=color)
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(1.5, 3.5)))

    elif hazard_type == "smoke":
        # Diffuse gray/dark clouds across the upper scene
        for _ in range(random.randint(20, 40)):
            sx = random.randint(10, w - 10)
            sy = random.randint(10, h - 30)
            srad = random.randint(20, 50)
            g_shade = random.randint(70, 150)
            draw.ellipse([sx - srad, sy - srad, sx + srad, sy + srad], fill=(g_shade, g_shade, g_shade + random.randint(-5, 5)))
        img = img.filter(ImageFilter.GaussianBlur(radius=random.uniform(4.0, 7.0)))

    elif hazard_type == "electrical_hazard":
        # Dark panel with intense bright cyan/white arc flash and jagged spark sparks
        center_x = random.randint(40, 90)
        center_y = random.randint(40, 90)
        # Intense core
        draw.ellipse([center_x - 15, center_y - 15, center_x + 15, center_y + 15], fill=(240, 250, 255))
        draw.ellipse([center_x - 25, center_y - 25, center_x + 25, center_y + 25], fill=(120, 220, 255))
        # Jagged discharge lines
        for _ in range(random.randint(6, 12)):
            x1, y1 = center_x, center_y
            for _ in range(random.randint(3, 6)):
                x2 = x1 + random.randint(-18, 18)
                y2 = y1 + random.randint(-18, 18)
                draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255), width=random.randint(1, 2))
                x1, y1 = x2, y2
        img = img.filter(ImageFilter.GaussianBlur(radius=0.8))

    elif hazard_type == "chemical_spill":
        # Green/yellow corrosive puddle on ground with foam or staining
        px = random.randint(30, 80)
        py = random.randint(60, 100)
        p_color = random.choice([
            (random.randint(80, 120), random.randint(160, 220), random.randint(40, 80)), # Acid green
            (random.randint(180, 230), random.randint(170, 210), 30),                     # Corrosive yellow
            (random.randint(40, 70), random.randint(90, 140), random.randint(180, 230)),  # Solvent blue
        ])
        draw.polygon([
            (px - 30, py), (px - 15, py - 20), (px + 20, py - 25),
            (px + 45, py), (px + 30, py + 25), (px - 10, py + 20),
        ], fill=p_color)
        # Foam highlights
        for _ in range(8):
            fx = px + random.randint(-20, 20)
            fy = py + random.randint(-15, 15)
            draw.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=(230, 255, 230))
        img = img.filter(ImageFilter.GaussianBlur(radius=1.5))

    elif hazard_type == "molten_metal_spill":
        # Extremely intense glowing radiant yellow-orange pool with sparks
        mx = random.randint(40, 80)
        my = random.randint(60, 100)
        draw.ellipse([mx - 40, my - 25, mx + 40, my + 25], fill=(255, 120, 0))
        draw.ellipse([mx - 30, my - 18, mx + 30, my + 18], fill=(255, 210, 20))
        draw.ellipse([mx - 15, my - 10, mx + 15, my + 10], fill=(255, 255, 200))
        img = img.filter(ImageFilter.GaussianBlur(radius=2.0))

    elif hazard_type == "mechanical_failure":
        # Broken machine elements, jagged cracks, shredded gray conveyor texture
        draw.rectangle([10, 30, w - 10, h - 30], fill=(50, 52, 58))
        # Crack / tear
        cx, cy = 30, 40
        for _ in range(8):
            nx = cx + random.randint(10, 16)
            ny = cy + random.randint(-6, 10)
            draw.line([(cx, cy), (nx, ny)], fill=(15, 15, 18), width=4)
            cx, cy = nx, ny

    elif hazard_type == "vehicle_traffic_incident":
        # Collision angles, dumper wheel, bent metal panels
        draw.rectangle([20, 40, 70, 90], fill=(200, 140, 20)) # Truck body
        draw.polygon([(65, 45), (105, 75), (80, 100), (55, 95)], fill=(120, 125, 130)) # Crushed metal
        draw.ellipse([25, 80, 50, 105], fill=(20, 20, 20)) # Tire

    elif hazard_type == "normal_machinery":
        # Clean pipes, cylindrical tank, orderly dials, regular plant room
        draw.rectangle([20, 20, 60, h - 20], fill=(80, 90, 100)) # Tank
        draw.line([(60, 50), (w - 20, 50)], fill=(140, 150, 160), width=10) # Pipe
        draw.line([(w - 20, 50), (w - 20, h - 30)], fill=(140, 150, 160), width=10) # Pipe
        draw.ellipse([30, 40, 50, 60], fill=(230, 230, 230)) # Dial gauge
        draw.line([(40, 50), (45, 45)], fill=(200, 30, 30), width=2) # Needle

    elif hazard_type == "unrelated_photo":
        # Domestic / office scenes, laptops, selfies, shoes, documents, non-industrial
        choice = random.randint(0, 4)
        if choice == 0:
            # Office desk with laptop / keyboard
            draw.rectangle([0, h // 2, w, h], fill=(220, 218, 215)) # Desk
            draw.rectangle([20, 20, 90, 80], fill=(45, 48, 55))     # Laptop screen
            draw.rectangle([25, 25, 85, 75], fill=(20, 22, 28))     # Screen display
            draw.line([(15, 80), (95, 80)], fill=(70, 72, 80), width=4) # Keyboard base
        elif choice == 1:
            # Person / face / selfie (skin tones, shirt, hair)
            skin = random.choice([(235, 190, 160), (210, 160, 130), (190, 140, 110)])
            draw.rectangle([10, 80, w - 10, h], fill=random.choice([(240, 240, 245), (40, 80, 140), (60, 60, 60)])) # Shirt
            draw.ellipse([35, 25, 95, 95], fill=skin) # Face
            draw.ellipse([30, 15, 100, 50], fill=(25, 25, 30)) # Hair
            draw.rectangle([45, 50, 85, 62], outline=(100, 100, 120), width=2) # Glasses
        elif choice == 2:
            # Footwear / shoe / sneakers / rack
            draw.rectangle([0, 0, w, h], fill=(30, 32, 36))
            draw.ellipse([20, 40, 80, 90], fill=random.choice([(40, 90, 180), (220, 180, 30), (240, 240, 240)])) # Shoe
            draw.ellipse([50, 70, 110, 100], fill=(230, 230, 235)) # Sole
        elif choice == 3:
            # White document with lines of text
            img = Image.new("RGB", size, color=(245, 245, 248))
            d_doc = ImageDraw.Draw(img)
            for y in range(20, h - 20, 12):
                d_doc.line([(20, y), (random.randint(60, w - 20), y)], fill=(80, 80, 90), width=2)
        else:
            # Solid wall / room interior
            shade = random.randint(180, 235)
            img = Image.new("RGB", size, color=(shade, shade - 8, shade - 15))

    return img


def train_model(epochs: int = 25, samples_per_class: int = 60, batch_size: int = 32):
    print("========================================================")
    print("TRAINING HAZARD VISION NET (Industrial AI Vision Model)")
    print("========================================================")
    print(f"Target classes ({len(HAZARD_CLASSES)}): {', '.join(HAZARD_CLASSES)}")

    # 1. Generate Dataset
    print(f"\nGenerating {samples_per_class * len(HAZARD_CLASSES)} augmented training images...")
    images = []
    labels = []

    for cls_name in HAZARD_CLASSES:
        cls_idx = CLASS_TO_IDX[cls_name]
        for _ in range(samples_per_class):
            img = generate_synthetic_hazard_image(cls_name)
            # Random horizontal flip augmentation
            if random.random() > 0.5:
                img = img.transpose(Image.FLIP_LEFT_RIGHT)
            images.append(img)
            labels.append(cls_idx)

    # Ingest real user uploaded photos as unrelated_photo ground-truth
    photos_dir = Path("data/photos")
    if photos_dir.exists():
        unrelated_idx = CLASS_TO_IDX["unrelated_photo"]
        for p in photos_dir.glob("*.jpg"):
            if p.stat().st_size > 10000:  # Real photo files (>10KB)
                try:
                    real_img = Image.open(p).convert("RGB")
                    # Add full image and random crops
                    images.append(real_img)
                    labels.append(unrelated_idx)
                    for _ in range(3):
                        w, h = real_img.size
                        crop_box = (
                            random.randint(0, w // 4),
                            random.randint(0, h // 4),
                            random.randint(3 * w // 4, w),
                            random.randint(3 * h // 4, h),
                        )
                        images.append(real_img.crop(crop_box))
                        labels.append(unrelated_idx)
                except Exception:
                    pass

    # 2. Extract Features
    print("Extracting convolutional tensors & auxiliary spectral profiles...")
    img_tensors = []
    aux_tensors = []

    for img in images:
        t_img, t_aux = preprocess_image(img)
        img_tensors.append(t_img)
        aux_tensors.append(t_aux)

    X_img = torch.cat(img_tensors, dim=0)
    X_aux = torch.cat(aux_tensors, dim=0)
    y = torch.tensor(labels, dtype=torch.long)

    # Train / Val Split (80% / 20%)
    dataset_size = len(labels)
    indices = list(range(dataset_size))
    random.seed(42)
    random.shuffle(indices)

    split = int(0.8 * dataset_size)
    train_idx = indices[:split]
    val_idx = indices[split:]

    X_img_train, X_aux_train, y_train = X_img[train_idx], X_aux[train_idx], y[train_idx]
    X_img_val, X_aux_val, y_val = X_img[val_idx], X_aux[val_idx], y[val_idx]

    print(f"Dataset split: {len(train_idx)} train samples, {len(val_idx)} validation samples.")

    # 3. Model, Optimizer, Criterion
    model = HazardVisionNet(num_classes=len(HAZARD_CLASSES))
    optimizer = optim.AdamW(model.parameters(), lr=1e-3, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    # 4. Training Loop
    print("\nBeginning Neural Network Optimization:")
    best_val_acc = 0.0

    for epoch in range(1, epochs + 1):
        model.train()
        permutation = torch.randperm(X_img_train.size(0))
        epoch_loss = 0.0
        correct = 0
        total = 0

        for i in range(0, X_img_train.size(0), batch_size):
            batch_indices = permutation[i:i + batch_size]
            b_img = X_img_train[batch_indices]
            b_aux = X_aux_train[batch_indices]
            b_y = y_train[batch_indices]

            optimizer.zero_grad()
            logits = model(b_img, b_aux)
            loss = criterion(logits, b_y)
            loss.backward()
            optimizer.step()

            epoch_loss += loss.item() * len(b_y)
            preds = torch.argmax(logits, dim=1)
            correct += (preds == b_y).sum().item()
            total += len(b_y)

        scheduler.step()
        train_acc = correct / total

        # Validation
        model.eval()
        with torch.no_grad():
            val_logits = model(X_img_val, X_aux_val)
            val_loss = criterion(val_logits, y_val).item()
            val_preds = torch.argmax(val_logits, dim=1)
            val_acc = (val_preds == y_val).sum().item() / len(y_val)

        if epoch % 5 == 0 or epoch == epochs:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] - Loss: {epoch_loss/total:.4f} | Train Acc: {train_acc*100:.1f}% | Val Acc: {val_acc*100:.1f}%")

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(model.state_dict(), MODEL_PATH)

    print(f"\nTraining Complete! Best Validation Accuracy: {best_val_acc*100:.1f}%")
    print(f"Model saved to: {MODEL_PATH}")
    return model


if __name__ == "__main__":
    train_model(epochs=25, samples_per_class=60, batch_size=32)
