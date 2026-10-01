"""
Training & Evaluation Pipeline for VitaLens Deep Neural Network.
Trains VitaLensSpecialtyNet from scratch on multi-modal clinical data.
Generates evaluation reports, confusion matrices, loss curves, and exports production weights.
"""

import os
import sys

# Ensure backend root is on sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Ensure training dir is on sys.path for local module imports
training_dir = os.path.abspath(os.path.dirname(__file__))
if training_dir not in sys.path:
    sys.path.insert(0, training_dir)

import json
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader

from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

from dataset_generator import SPECIALTIES, generate_dataset
from feature_pipeline import ClinicalFeaturePipeline
from app.ml.models.specialty_network import VitaLensSpecialtyNet

# Set random seeds for deterministic reproducibility
def set_seed(seed=42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def plot_training_history(history, save_path):
    """Plots and saves loss and accuracy curves across training epochs."""
    epochs = range(1, len(history["train_loss"]) + 1)
    
    plt.figure(figsize=(12, 5))
    
    # Loss Subplot
    plt.subplot(1, 2, 1)
    plt.plot(epochs, history["train_loss"], "b-o", label="Training Loss", markersize=4)
    plt.plot(epochs, history["val_loss"], "r--s", label="Validation Loss", markersize=4)
    plt.title("Cross-Entropy Loss vs Epochs", fontsize=12, fontweight="bold")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.legend()
    
    # Accuracy Subplot
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
            
    plt.title("VitaLens Specialty Classification Confusion Matrix", fontsize=13, fontweight="bold", pad=20)
    plt.xlabel("Predicted Specialty", fontsize=11, fontweight="bold")
    plt.ylabel("True Specialty", fontsize=11, fontweight="bold")
    plt.tight_layout()
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"[OK] Confusion matrix saved to: {save_path}")

def train_model(
    data_path: str,
    output_dir: str,
    epochs: int = 40,
    batch_size: int = 32,
    learning_rate: float = 1e-3
):
    set_seed(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"[i] Using compute device: {device}")
    
    # 1. Load or Generate Dataset
    if not os.path.exists(data_path):
        print(f"[i] Dataset not found at {data_path}. Generating synthesized clinical data...")
        df = generate_dataset(num_samples_per_class=350, output_path=data_path)
    else:
        df = pd.read_csv(data_path)
        print(f"[OK] Loaded dataset from {data_path} with {len(df)} records.")

    # 2. Train / Val / Test Stratified Split (70% / 15% / 15%)
    train_df, test_df = train_test_split(
        df, test_size=0.30, random_state=42, stratify=df["specialty_id"]
    )
    val_df, test_df = train_test_split(
        test_df, test_size=0.50, random_state=42, stratify=test_df["specialty_id"]
    )
    
    print(f"[i] Dataset Split: Train={len(train_df)} | Val={len(val_df)} | Test={len(test_df)}")

    # 3. Fit Feature Pipeline on Training Set
    pipeline = ClinicalFeaturePipeline(max_tfidf_features=256)
    X_train = pipeline.fit_transform(train_df)
    y_train = train_df["specialty_id"].values
    
    X_val = pipeline.transform(val_df)
    y_val = val_df["specialty_id"].values
    
    X_test = pipeline.transform(test_df)
    y_test = test_df["specialty_id"].values
    
    input_dim = X_train.shape[1]
    print(f"[OK] Feature Pipeline Fitted. Total Feature Dimensions: {input_dim}")

    # 4. Create PyTorch DataLoaders
    train_dataset = TensorDataset(torch.tensor(X_train, dtype=torch.float32), torch.tensor(y_train, dtype=torch.long))
    val_dataset = TensorDataset(torch.tensor(X_val, dtype=torch.float32), torch.tensor(y_val, dtype=torch.long))
    test_dataset = TensorDataset(torch.tensor(X_test, dtype=torch.float32), torch.tensor(y_test, dtype=torch.long))

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)

    # 5. Initialize PyTorch Model
    model = VitaLensSpecialtyNet(
        input_dim=input_dim,
        num_classes=len(SPECIALTIES),
        hidden_dims=(256, 128, 64),
        dropout_rate=0.25
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.AdamW(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="min", patience=4, factor=0.5)

    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": []}
    best_val_loss = float("inf")
    best_model_weights = None

    print("\n" + "="*70)
    print("STARTING PYTORCH MODEL TRAINING LOOP")
    print("="*70)

    for epoch in range(1, epochs + 1):
        # Training Phase
        model.train()
        running_loss = 0.0
        correct_train = 0
        total_train = 0
        
        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()
            
            running_loss += loss.item() * batch_x.size(0)
            _, preds = torch.max(outputs, 1)
            correct_train += (preds == batch_y).sum().item()
            total_train += batch_y.size(0)

        epoch_train_loss = running_loss / total_train
        epoch_train_acc = correct_train / total_train

        # Validation Phase
        model.eval()
        running_val_loss = 0.0
        correct_val = 0
        total_val = 0
        
        with torch.no_grad():
            for batch_x, batch_y in val_loader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                
                running_val_loss += loss.item() * batch_x.size(0)
                _, preds = torch.max(outputs, 1)
                correct_val += (preds == batch_y).sum().item()
                total_val += batch_y.size(0)

        epoch_val_loss = running_val_loss / total_val
        epoch_val_acc = correct_val / total_val

        scheduler.step(epoch_val_loss)

        history["train_loss"].append(epoch_train_loss)
        history["val_loss"].append(epoch_val_loss)
        history["train_acc"].append(epoch_train_acc)
        history["val_acc"].append(epoch_val_acc)

        if epoch_val_loss < best_val_loss:
            best_val_loss = epoch_val_loss
            best_model_weights = model.state_dict().copy()

        if epoch % 5 == 0 or epoch == 1 or epoch == epochs:
            print(f"Epoch [{epoch:02d}/{epochs:02d}] "
                  f"Train Loss: {epoch_train_loss:.4f} | Train Acc: {epoch_train_acc*100:.2f}% | "
                  f"Val Loss: {epoch_val_loss:.4f} | Val Acc: {epoch_val_acc*100:.2f}%")

    print("="*70)
    print("[OK] Training complete. Restoring best model weights...")
    model.load_state_dict(best_model_weights)

    # 6. Evaluation on Held-Out Test Set
    model.eval()
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(device)
            outputs = model(batch_x)
            _, preds = torch.max(outputs, 1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.numpy())

    test_acc = accuracy_score(all_targets, all_preds)
    test_f1_macro = f1_score(all_targets, all_preds, average="macro")
    test_f1_weighted = f1_score(all_targets, all_preds, average="weighted")
    report_dict = classification_report(all_targets, all_preds, target_names=SPECIALTIES, output_dict=True)
    report_text = classification_report(all_targets, all_preds, target_names=SPECIALTIES)

    print("\n" + "="*70)
    print("FINAL HELD-OUT TEST EVALUATION REPORT")
    print("="*70)
    print(report_text)
    print(f"Test Accuracy:       {test_acc*100:.2f}%")
    print(f"Macro F1-Score:      {test_f1_macro:.4f}")
    print(f"Weighted F1-Score:   {test_f1_weighted:.4f}")
    print("="*70)

    # 7. Save Evaluation Plots
    os.makedirs(output_dir, exist_ok=True)
    curves_path = os.path.join(output_dir, "loss_accuracy_curves.png")
    cm_path = os.path.join(output_dir, "confusion_matrix.png")
    
    plot_training_history(history, curves_path)
    plot_confusion_matrix(all_targets, all_preds, SPECIALTIES, cm_path)

    # 8. Save Serialized Production Artifacts
    model_save_path = os.path.join(output_dir, "specialty_model.pt")
    pipeline_save_path = os.path.join(output_dir, "feature_pipeline.joblib")
    metadata_save_path = os.path.join(output_dir, "model_metadata.json")

    # Save PyTorch Model Weights & Config
    torch.save({
        "state_dict": model.state_dict(),
        "input_dim": input_dim,
        "num_classes": len(SPECIALTIES),
        "hidden_dims": (256, 128, 64),
        "dropout_rate": 0.25,
        "classes": SPECIALTIES
    }, model_save_path)
    print(f"[OK] Saved PyTorch model weights to: {model_save_path}")

    # Save Feature Pipeline
    pipeline.save(pipeline_save_path)
    print(f"[OK] Saved Feature Pipeline to: {pipeline_save_path}")

    # Save Metadata JSON
    metadata = {
        "model_name": "VitaLensSpecialtyNet",
        "architecture": "Multi-Layer Perceptron (BatchNorm + Dropout)",
        "framework": f"PyTorch {torch.__version__}",
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "input_dimensions": input_dim,
        "num_classes": len(SPECIALTIES),
        "classes": SPECIALTIES,
        "metrics": {
            "test_accuracy": round(float(test_acc), 4),
            "macro_f1": round(float(test_f1_macro), 4),
            "weighted_f1": round(float(test_f1_weighted), 4),
            "epochs_trained": epochs,
            "best_validation_loss": round(float(best_val_loss), 4)
        },
        "per_class_metrics": {
            k: {
                "precision": round(v["precision"], 4),
                "recall": round(v["recall"], 4),
                "f1-score": round(v["f1-score"], 4),
                "support": v["support"]
            }
            for k, v in report_dict.items() if k in SPECIALTIES
        }
    }
    with open(metadata_save_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"[OK] Saved model metadata to: {metadata_save_path}")

    return metadata

if __name__ == "__main__":
    dataset_file = r"c:\Users\Uzair\Documents\AML_REACT_PROJECT\backend\app\ml\data\medical_specialty_dataset.csv"
    models_folder = r"c:\Users\Uzair\Documents\AML_REACT_PROJECT\backend\app\ml\models"
    
    meta = train_model(
        data_path=dataset_file,
        output_dir=models_folder,
        epochs=35,
        batch_size=32,
        learning_rate=1e-3
    )
