"""
Training & Multi-Facet Evaluation Pipeline for VitaLens V2 Deep Neural Network.
Trains VitaLensSpecialtyNet from scratch on the 306-dimensional multi-modal dataset.
Evaluates:
- Global metrics: Top-1 Accuracy, Top-2 Accuracy, Top-3 Accuracy, Macro F1, Weighted F1
- Calibration: Expected Calibration Error (ECE), Multi-Class Brier Score
- Subsets: Separate evaluation on Isolated, Mixed, Discordant, and Normal-Control cohorts
- Per-Specialty: Precision, Recall, F1, Support, and Confusion Matrix
- Standalone Regression Suite: Report #2 Test A, B, C and Gilbert's syndrome observation
Exports production artifacts strictly to backend/app/ml/models/v2/.
"""

import os
import sys
import json
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

training_dir = os.path.abspath(os.path.dirname(__file__))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, brier_score_loss

from dataset_generator_v2 import SPECIALTIES, CANONICAL_BIOMARKERS_V2, generate_v2_dataset
from feature_pipeline_v2 import ClinicalFeaturePipelineV2
from app.ml.models.specialty_network import VitaLensSpecialtyNet

def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def plot_training_history(history, save_path):
    """Plots and saves loss and accuracy curves across training epochs."""
    epochs = range(1, len(history["train_loss"]) + 1)
    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(epochs, history["train_loss"], "b-o", label="Training Loss", markersize=4)
    plt.plot(epochs, history["val_loss"], "r--s", label="Validation Loss", markersize=4)
    plt.title("Cross-Entropy Loss vs Epochs", fontsize=12, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    plt.subplot(1, 2, 2)
    plt.plot(epochs, [a * 100 for a in history["train_acc"]], "b-o", label="Training Accuracy", markersize=4)
    plt.plot(epochs, [a * 100 for a in history["val_acc"]], "g--^", label="Validation Accuracy", markersize=4)
    plt.title("Accuracy (%) vs Epochs", fontsize=12, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy (%)")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()

    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[OK] Training curves saved to: {save_path}")

def plot_confusion_matrix(y_true, y_pred, classes, save_path):
    """Plots and saves normalized confusion matrix graphic."""
    cm = confusion_matrix(y_true, y_pred)
    cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

    fig, ax = plt.subplots(figsize=(10, 8))
    cax = ax.matshow(cm_norm, cmap=plt.cm.Blues, alpha=0.85)
    fig.colorbar(cax)

    ax.set_xticks(range(len(classes)))
    ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=45, ha="left", fontsize=9)
    ax.set_yticklabels(classes, fontsize=9)

    for i in range(len(classes)):
        for j in range(len(classes)):
            val = cm[i, j]
            ax.text(j, i, f"{val}\n({cm_norm[i, j]*100:.0f}%)",
                    ha="center", va="center",
                    color="white" if cm_norm[i, j] > 0.5 else "black",
                    fontsize=8, fontweight="bold")

    plt.title("VitaLens Specialty V2 Confusion Matrix", fontsize=13, fontweight="bold", pad=20)
    plt.xlabel("Predicted Specialty", fontsize=11, fontweight="bold")
    plt.ylabel("True Specialty", fontsize=11, fontweight="bold")
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[OK] Confusion matrix saved to: {save_path}")

def compute_top_k_accuracy(y_true: np.ndarray, y_probs: np.ndarray, k: int = 2) -> float:
    """Computes Top-K accuracy score."""
    top_k_preds = np.argsort(y_probs, axis=1)[:, -k:]
    hits = [y_true[i] in top_k_preds[i] for i in range(len(y_true))]
    return float(np.mean(hits))

def compute_calibration_metrics(y_true: np.ndarray, y_probs: np.ndarray, num_bins: int = 10) -> Dict[str, float]:
    """Computes Expected Calibration Error (ECE) and Multi-Class Brier Score."""
    confidences = np.max(y_probs, axis=1)
    predictions = np.argmax(y_probs, axis=1)
    accuracies = (predictions == y_true).astype(float)

    # 1. Expected Calibration Error (ECE)
    bin_boundaries = np.linspace(0, 1, num_bins + 1)
    ece = 0.0
    for i in range(num_bins):
        in_bin = (confidences > bin_boundaries[i]) & (confidences <= bin_boundaries[i + 1])
        prop_in_bin = np.mean(in_bin)
        if prop_in_bin > 0:
            accuracy_in_bin = np.mean(accuracies[in_bin])
            avg_confidence_in_bin = np.mean(confidences[in_bin])
            ece += np.abs(accuracy_in_bin - avg_confidence_in_bin) * prop_in_bin

    # 2. Multi-Class Brier Score: 1/N * sum((p_ik - y_ik)^2)
    num_classes = y_probs.shape[1]
    y_one_hot = np.zeros_like(y_probs)
    for i, target in enumerate(y_true):
        y_one_hot[i, target] = 1.0
    brier_score = float(np.mean(np.sum((y_probs - y_one_hot) ** 2, axis=1)))

    return {
        "expected_calibration_error": round(float(ece), 4),
        "brier_score": round(brier_score, 4)
    }

def evaluate_subset(y_true: np.ndarray, y_probs: np.ndarray, subset_name: str) -> Dict[str, Any]:
    """Evaluates accuracy, top-2, top-3, and macro F1 on a specific cohort subset."""
    if len(y_true) == 0:
        return {"support": 0}
    preds = np.argmax(y_probs, axis=1)
    acc = accuracy_score(y_true, preds)
    top2 = compute_top_k_accuracy(y_true, y_probs, k=2)
    top3 = compute_top_k_accuracy(y_true, y_probs, k=3)
    macro_f1 = f1_score(y_true, preds, average="macro", zero_division=0)

    return {
        "support": int(len(y_true)),
        "accuracy": round(float(acc), 4),
        "top2_accuracy": round(float(top2), 4),
        "top3_accuracy": round(float(top3), 4),
        "macro_f1": round(float(macro_f1), 4)
    }

def run_external_regression_benchmarks(
    model: nn.Module,
    pipeline: ClinicalFeaturePipelineV2,
    device: torch.device
) -> Dict[str, Any]:
    """
    Executes observational regression benchmarks on Report #2 historical scenarios
    and Gilbert's control. Strictly non-training, post-convergence evaluation.
    """
    model.eval()
    results = {}

    # Report #2 Biomarkers (24 Schema)
    report2_abnormal_biomarkers = {
        "tsh": 6.8, "free_t4": 0.72, "ferritin": 9.0, "iron": 42.0,
        "hemoglobin": 11.2, "rbc_count": 3.78, "hematocrit": 34.1,
        "wbc_count": 12400.0, "platelet_count": 472000.0,
        "total_bilirubin": 1.4, "ldl_cholesterol": 112.0
    }

    scenarios = {
        "report_2_test_a": {
            "concern": "Feeling unusually tired and dizzy",
            "symptoms": "Dizziness, Headache, Fatigue",
            "body_region": "General",
            "biomarkers": report2_abnormal_biomarkers
        },
        "report_2_test_b": {
            "concern": "Neck swelling and feeling unusually tired",
            "symptoms": "Neck swelling, fatigue",
            "body_region": "General",
            "biomarkers": report2_abnormal_biomarkers
        },
        "report_2_test_c": {
            "concern": "Routine follow-up for abnormal laboratory results",
            "symptoms": "Fatigue",
            "body_region": "General",
            "biomarkers": report2_abnormal_biomarkers
        },
        "gilbert_syndrome_control": {
            "concern": "Routine annual wellness checkup, feeling completely fine",
            "symptoms": "Routine checkup",
            "body_region": "General / Whole Body",
            "biomarkers": {"total_bilirubin": 1.6}  # All others normal
        }
    }

    for name, s in scenarios.items():
        row = {
            "primary_concern": s["concern"],
            "symptoms": s["symptoms"],
            "body_region": s["body_region"],
            "full_text": f"Primary Concern: {s['concern']}. Symptoms: {s['symptoms']}. Affected Area: {s['body_region']}.",
            "severity_score": 5.0,
            "duration_days": 7.0
        }
        for b_name in CANONICAL_BIOMARKERS_V2:
            if b_name in s["biomarkers"]:
                row[f"val_{b_name}"] = s["biomarkers"][b_name]
                row[f"flag_{b_name}"] = "HIGH" if "tsh" in b_name or "wbc" in b_name or "platelet" in b_name or "bilirubin" in b_name or "ldl" in b_name else "LOW"
            else:
                row[f"val_{b_name}"] = pipeline.scaler.mean_[CANONICAL_BIOMARKERS_V2.index(b_name) * 2] if hasattr(pipeline.scaler, "mean_") else 1.0
                row[f"flag_{b_name}"] = "NORMAL"

        x_vec = pipeline.transform([row])
        with torch.no_grad():
            logits = model(torch.tensor(x_vec, dtype=torch.float32).to(device))
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]

        top_indices = np.argsort(probs)[::-1]
        results[name] = {
            "winner": SPECIALTIES[top_indices[0]],
            "confidence": round(float(probs[top_indices[0]]), 4),
            "top_3": [
                {"specialty": SPECIALTIES[idx], "probability": round(float(probs[idx]), 4)}
                for idx in top_indices[:3]
            ],
            "gastroenterology_prob": round(float(probs[SPECIALTIES.index("Gastroenterology")]), 4)
        }

    return results

def train_v2_model(
    data_path: str,
    output_dir: str,
    epochs: int = 45,
    batch_size: int = 32,
    learning_rate: float = 1e-3
) -> Dict[str, Any]:
    """
    Executes training of VitaLens V2 Deep Neural Network with multi-facet evaluation.
    DO NOT CALL THIS FUNCTION UNTIL EXPLICITLY APPROVED BY USER.
    """
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[i] Using compute device: {device}")

    # 1. Load Dataset
    if not os.path.exists(data_path):
        print(f"[i] Dataset not found at {data_path}. Generating V2 dataset...")
        generate_v2_dataset(samples_per_specialty=600, output_path=data_path)

    df = pd.read_csv(data_path)
    print(f"[OK] Loaded V2 dataset: {len(df)} samples.")

    # 2. Strict Partitioning: Train (70%), Val (15%), Test (15%)
    train_df = df[df["split"] == "train"].copy().reset_index(drop=True)
    val_df = df[df["split"] == "val"].copy().reset_index(drop=True)
    test_df = df[df["split"] == "test"].copy().reset_index(drop=True)

    print(f"[i] Splits: Train={len(train_df)} | Val={len(val_df)} | Test={len(test_df)}")

    # 3. Fit Feature Pipeline strictly on Training Split
    pipeline = ClinicalFeaturePipelineV2(max_tfidf_features=256)
    X_train = pipeline.fit_transform(train_df)
    y_train = train_df["specialty_id"].values

    X_val = pipeline.transform(val_df)
    y_val = val_df["specialty_id"].values

    X_test = pipeline.transform(test_df)
    y_test = test_df["specialty_id"].values

    input_dim = X_train.shape[1]
    assert input_dim == 306, f"Expected 306 features, got {input_dim}"
    print(f"[OK] Feature Pipeline Fitted. Total Dimensions: {input_dim}")

    # 4. DataLoaders
    train_loader = DataLoader(
        TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long)),
        batch_size=batch_size, shuffle=True
    )
    val_loader = DataLoader(
        TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.long)),
        batch_size=batch_size, shuffle=False
    )
    test_loader = DataLoader(
        TensorDataset(torch.tensor(X_test, dtype=torch.float32), torch.tensor(y_test, dtype=torch.long)),
        batch_size=batch_size, shuffle=False
    )

    # 5. Initialize Model
    model = VitaLensSpecialtyNet(
        input_dim=306,
        num_classes=len(SPECIALTIES),
        hidden_dims=(256, 128, 64),
        dropout_rate=0.25
    ).to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=0.05)
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=4, factor=0.5)

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_val_loss = float("inf")
    best_weights = None

    print("\n" + "="*70)
    print("STARTING PYTORCH V2 TRAINING LOOP")
    print("="*70)

    for epoch in range(1, epochs + 1):
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0

        for bx, by in train_loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            out = model(bx)
            loss = criterion(out, by)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * bx.size(0)
            _, preds = torch.max(out, 1)
            correct_train += (preds == by).sum().item()
            total_train += by.size(0)

        epoch_train_loss = running_loss / total_train
        epoch_train_acc = correct_train / total_train

        # Validation
        model.eval()
        running_val_loss = 0.0
        correct_val = 0
        total_val = 0
        with torch.no_grad():
            for bx, by in val_loader:
                bx, by = bx.to(device), by.to(device)
                out = model(bx)
                loss = criterion(out, by)
                running_val_loss += loss.item() * bx.size(0)
                _, preds = torch.max(out, 1)
                correct_val += (preds == by).sum().item()
                total_val += by.size(0)

        epoch_val_loss = running_val_loss / total_val
        epoch_val_acc = correct_val / total_val

        scheduler.step(epoch_val_loss)
        history["train_loss"].append(epoch_train_loss)
        history["val_loss"].append(epoch_val_loss)
        history["train_acc"].append(epoch_train_acc)
        history["val_acc"].append(epoch_val_acc)

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_weights = model.state_dict().copy()

        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] "
                  f"Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc*100:.2f}% | "
                  f"Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc*100:.2f}%")

    print("[OK] Training complete. Restoring best validation checkpoint...")
    model.load_state_dict(best_weights)

    # 6. Evaluation on Held-Out Test Set
    model.eval()
    all_probs = []
    with torch.no_grad():
        for bx, _ in test_loader:
            bx = bx.to(device)
            out = model(bx)
            probs = torch.softmax(out, dim=-1)
            all_probs.append(probs.cpu().numpy())
    all_probs = np.vstack(all_probs)
    all_preds = np.argmax(all_probs, axis=1)

    # Overall metrics
    overall_acc = accuracy_score(y_test, all_preds)
    top2_acc = compute_top_k_accuracy(y_test, all_probs, k=2)
    top3_acc = compute_top_k_accuracy(y_test, all_probs, k=3)
    macro_f1 = f1_score(y_test, all_preds, average="macro")
    weighted_f1 = f1_score(y_test, all_preds, average="weighted")
    calibration = compute_calibration_metrics(y_test, all_probs)
    rep_dict = classification_report(y_test, all_preds, target_names=SPECIALTIES, output_dict=True)

    # Subset metrics
    subset_results = {}
    for cat in ["ISOLATED", "MIXED", "DISCORDANT", "NORMAL_CONTROL"]:
        cat_indices = test_df[test_df["case_category"] == cat].index.values
        if len(cat_indices) > 0:
            sub_y = y_test[cat_indices]
            sub_probs = all_probs[cat_indices]
            subset_results[cat.lower()] = evaluate_subset(sub_y, sub_probs, cat)

    # Standalone regression evaluations
    regression_evals = run_external_regression_benchmarks(model, pipeline, device)

    # 7. Save Plots & Artifacts strictly to output_dir
    os.makedirs(output_dir, exist_ok=True)
    curves_path = os.path.join(output_dir, "loss_accuracy_curves.png")
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    plot_training_history(history, curves_path)
    plot_confusion_matrix(y_test, all_preds, SPECIALTIES, cm_path)

    model_save_path = os.path.join(output_dir, "specialty_model_v2.pt")
    pipeline_save_path = os.path.join(output_dir, "feature_pipeline_v2.joblib")
    metadata_save_path = os.path.join(output_dir, "model_metadata_v2.json")

    torch.save({
        "state_dict": model.state_dict(),
        "input_dim": 306,
        "num_classes": len(SPECIALTIES),
        "hidden_dims": (256, 128, 64),
        "dropout_rate": 0.25,
        "classes": SPECIALTIES
    }, model_save_path)
    pipeline.save(pipeline_save_path)

    metadata = {
        "model_version": "2.0.0",
        "dataset_version": "2.0.0",
        "feature_schema_version": "2.0.0",
        "framework": f"PyTorch {torch.__version__}",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "random_seed": 42,
        "canonical_biomarkers": CANONICAL_BIOMARKERS_V2,
        "feature_dimensions": {
            "total_input_dim": 306,
            "tfidf_text_dim": 256,
            "biomarker_numerical_and_flags_dim": 48,
            "clinical_metadata_dim": 2
        },
        "training_configuration": {
            "architecture": "VitaLensSpecialtyNetV2",
            "hidden_dims": [256, 128, 64],
            "dropout_rate": 0.25,
            "batch_size": batch_size,
            "learning_rate": learning_rate,
            "weight_decay": 1e-4,
            "optimizer": "AdamW",
            "lr_scheduler": "ReduceLROnPlateau(min, factor=0.5, patience=4)",
            "loss_function": "CrossEntropyLoss(label_smoothing=0.05)",
            "epochs_trained": epochs,
            "best_validation_loss": round(float(best_val_loss), 4)
        },
        "dataset_split": {
            "total_samples": len(df),
            "train_samples": len(train_df),
            "val_samples": len(val_df),
            "test_samples": len(test_df),
            "stratified_by": ["specialty_id", "case_category"]
        },
        "evaluation_results": {
            "overall": {
                "accuracy": round(float(overall_acc), 4),
                "top2_accuracy": round(float(top2_acc), 4),
                "top3_accuracy": round(float(top3_acc), 4),
                "macro_f1": round(float(macro_f1), 4),
                "weighted_f1": round(float(weighted_f1), 4),
                "expected_calibration_error": calibration["expected_calibration_error"],
                "brier_score": calibration["brier_score"]
            },
            "subsets": subset_results,
            "per_specialty": {
                k: {
                    "precision": round(v["precision"], 4),
                    "recall": round(v["recall"], 4),
                    "f1_score": round(v["f1-score"], 4),
                    "support": v["support"]
                }
                for k, v in rep_dict.items() if k in SPECIALTIES
            }
        },
        "regression_evaluations": regression_evals
    }

    with open(metadata_save_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n[OK] Model weights saved to: {model_save_path}")
    print(f"[OK] Pipeline saved to: {pipeline_save_path}")
    print(f"[OK] Metadata saved to: {metadata_save_path}")

    return metadata

if __name__ == "__main__":
    dataset_file = r"c:\Users\Uzair\Documents\AML_REACT_PROJECT\backend\app\ml\data\medical_specialty_dataset_v2.csv"
    models_folder = r"c:\Users\Uzair\Documents\AML_REACT_PROJECT\backend\app\ml\models\v2"

    meta = train_v2_model(
        data_path=dataset_file,
        output_dir=models_folder,
        epochs=45,
        batch_size=32,
        learning_rate=1e-3
    )
