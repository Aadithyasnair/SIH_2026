"""
Training Pipeline for Module C (AI/ML Detection).
Loads pipeline data, extracts features, trains Isolation Forest and Autoencoder,
calibrates anomaly score normalizations, and saves model artifacts.
"""
from pathlib import Path
import argparse
import sys
import os
from typing import Dict, Any, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
import torch

# Ensure repo root is on sys.path
root_dir = Path(__file__).resolve().parents[1]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ml_detection.data_loader import (
    load_blockchain_txns,
    load_network_events,
    load_correlation_edges,
    load_clusters,
    load_entity_graph,
)
from ml_detection.feature_engineering import (
    engineer_features,
    clean_features,
    FEATURE_COLUMNS,
)
from ml_detection.models_components import (
    Autoencoder,
    train_isolation_forest,
    score_isolation_forest,
    train_autoencoder,
    score_autoencoder,
    combine_anomaly_scores,
)


def train_pipeline(
    data_dir: Path,
    models_dir: Path,
    alpha: float = 0.5,
    contamination: float = 0.20,
    ae_epochs: int = 250,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Execute the complete training pipeline and persist artifacts.
    """
    models_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1/7] Loading pipeline data from: {data_dir}")
    txns = load_blockchain_txns(data_dir)
    events = load_network_events(data_dir)
    edges = load_correlation_edges(data_dir)
    clusters = load_clusters(data_dir)
    graph = load_entity_graph(data_dir)

    print(f"      Loaded {len(txns)} transactions, {len(events)} network events, "
          f"{len(edges)} correlation edges, {len(clusters)} clusters.")

    if not txns:
        raise ValueError(f"No transactions found in {data_dir} to train on!")

    print("[2/7] Engineering features...")
    raw_df = engineer_features(
        transactions=txns,
        network_events=events,
        correlation_edges=edges,
        clusters=clusters,
        graph=graph,
    )
    cleaned_df, feature_cols = clean_features(raw_df, FEATURE_COLUMNS)
    print(f"      Extracted {len(feature_cols)} features for {len(cleaned_df)} transactions.")

    print("[3/7] Standardizing features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(cleaned_df.values)

    print("[4/7] Training Isolation Forest...")
    if_model, s_min, s_max = train_isolation_forest(
        X_scaled=X_scaled,
        contamination=contamination,
        random_state=random_state,
    )
    if_scores = score_isolation_forest(if_model, X_scaled, s_min, s_max)
    print(f"      Isolation Forest trained. Raw range: [{s_min:.4f}, {s_max:.4f}]")

    print(f"[5/7] Training Feedforward Autoencoder ({ae_epochs} epochs)...")
    ae_model, err_min, err_max = train_autoencoder(
        X_scaled=X_scaled,
        latent_dim=4,
        epochs=ae_epochs,
        lr=0.005,
        batch_size=min(8, len(X_scaled)),
        random_state=random_state,
    )
    ae_scores = score_autoencoder(ae_model, X_scaled, err_min, err_max)
    print(f"      Autoencoder trained. Error range: [{err_min:.6f}, {err_max:.6f}]")

    print("[6/7] Combining normalized anomaly signals...")
    combined_scores = combine_anomaly_scores(if_scores, ae_scores, alpha=alpha)

    print(f"[7/7] Persisting model artifacts to {models_dir}...")
    # 1. Scaler & Feature Columns
    joblib.dump(scaler, models_dir / "scaler.joblib")
    joblib.dump(feature_cols, models_dir / "feature_cols.joblib")

    # 2. Isolation Forest
    joblib.dump(if_model, models_dir / "isolation_forest.joblib")

    # 3. PyTorch Autoencoder
    torch.save(
        {
            "state_dict": ae_model.state_dict(),
            "input_dim": len(feature_cols),
            "latent_dim": 4,
        },
        models_dir / "autoencoder.pt",
    )

    # 4. Calibration parameters
    calibration = {
        "s_min": s_min,
        "s_max": s_max,
        "err_min": err_min,
        "err_max": err_max,
        "alpha": alpha,
        "contamination": contamination,
    }
    joblib.dump(calibration, models_dir / "calibration.joblib")

    print("\n[SUCCESS] Model training complete and artifacts saved.")
    print("Training Summary:")
    print(f"  Total samples: {len(X_scaled)}")
    print(f"  Anomaly scores min/mean/max: "
          f"{combined_scores.min():.4f} / {combined_scores.mean():.4f} / {combined_scores.max():.4f}")

    return {
        "scaler": scaler,
        "feature_cols": feature_cols,
        "if_model": if_model,
        "ae_model": ae_model,
        "calibration": calibration,
        "combined_scores": combined_scores,
        "txids": list(cleaned_df.index),
    }


def main():
    parser = argparse.ArgumentParser(description="Train Module C Anomaly Detection Pipeline")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="sih26146/shared/sample_data",
        help="Path to directory with shared pipeline data",
    )
    parser.add_argument(
        "--models-dir",
        type=str,
        default="ml_detection/models",
        help="Path to directory where trained model artifacts are saved",
    )
    parser.add_argument("--alpha", type=float, default=0.5, help="Weight for Isolation Forest in ensemble")
    parser.add_argument("--epochs", type=int, default=250, help="Epochs to train Autoencoder")
    args = parser.parse_args()

    train_pipeline(
        data_dir=Path(args.data_dir),
        models_dir=Path(args.models_dir),
        alpha=args.alpha,
        ae_epochs=args.epochs,
    )


if __name__ == "__main__":
    from typing import Dict, Any
    main()
