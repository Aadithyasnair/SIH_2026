"""
Prediction Interface for Module C (AI/ML Detection).
Loads saved model artifacts, preprocesses transactions, and scores unseen data.

Callable by Module F (Backend) or any other downstream module:
    from ml_detection.predict import score_transactions
    scores = score_transactions(transactions)
"""
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
import joblib
import numpy as np
import pandas as pd
import torch

from ml_detection.feature_engineering import (
    engineer_features,
    clean_features,
    FEATURE_COLUMNS,
)
from ml_detection.models_components import (
    Autoencoder,
    score_isolation_forest,
    score_autoencoder,
    combine_anomaly_scores,
)

# Global in-process artifact cache for fast repeated inference
_CACHED_ARTIFACTS: Dict[str, Any] = {}


def _resolve_models_dir(models_dir: Optional[Union[str, Path]] = None) -> Path:
    """Resolve models directory relative to project root if not specified."""
    if models_dir is not None:
        return Path(models_dir).resolve()

    # Default relative to this file
    here = Path(__file__).resolve().parent
    default_dir = here / "models"
    if default_dir.exists():
        return default_dir

    # Fallback to root ml_detection/models
    root = here.parent
    return root / "ml_detection" / "models"


def load_model_artifacts(models_dir: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load all preprocessing and model artifacts required for inference.
    Uses in-memory cache to avoid disk re-reads on repeated calls.
    """
    m_dir = _resolve_models_dir(models_dir)
    cache_key = str(m_dir)

    if cache_key in _CACHED_ARTIFACTS:
        return _CACHED_ARTIFACTS[cache_key]

    scaler_path = m_dir / "scaler.joblib"
    cols_path = m_dir / "feature_cols.joblib"
    if_path = m_dir / "isolation_forest.joblib"
    ae_path = m_dir / "autoencoder.pt"
    calib_path = m_dir / "calibration.joblib"

    if not (scaler_path.exists() and cols_path.exists() and if_path.exists()
            and ae_path.exists() and calib_path.exists()):
        raise FileNotFoundError(
            f"Required model artifacts missing in {m_dir}. Please run train_model.py first."
        )

    scaler = joblib.load(scaler_path)
    feature_cols = joblib.load(cols_path)
    if_model = joblib.load(if_path)
    calibration = joblib.load(calib_path)

    # Load PyTorch Autoencoder
    ae_checkpoint = torch.load(ae_path, map_location=torch.device("cpu"), weights_only=False)
    input_dim = ae_checkpoint.get("input_dim", len(feature_cols))
    latent_dim = ae_checkpoint.get("latent_dim", 4)
    ae_model = Autoencoder(input_dim=input_dim, latent_dim=latent_dim)
    ae_model.load_state_dict(ae_checkpoint["state_dict"])
    ae_model.eval()

    artifacts = {
        "scaler": scaler,
        "feature_cols": feature_cols,
        "if_model": if_model,
        "ae_model": ae_model,
        "calibration": calibration,
    }
    _CACHED_ARTIFACTS[cache_key] = artifacts
    return artifacts


def clear_artifact_cache():
    """Clear the in-memory artifact cache (e.g. after retraining)."""
    _CACHED_ARTIFACTS.clear()


def score_transactions(
    transactions: List[Dict[str, Any]],
    data_context: Optional[Dict[str, Any]] = None,
    models_dir: Optional[Union[str, Path]] = None,
) -> List[Dict[str, Any]]:
    """
    Score a list of Bitcoin transactions for anomalous behavior.

    Args:
        transactions: List of transaction dicts matching BlockchainTxn format
                      (optionally enriched with pattern_type, flags, propagated_risk_score).
        data_context: Optional supplementary context with keys:
                      - 'network_events': List[Dict]
                      - 'correlation_edges': List[Dict]
                      - 'clusters': List[Dict]
                      - 'graph': nx.Graph
                      If omitted, sensible default values are used.
        models_dir: Optional path to directory containing trained model artifacts.

    Returns:
        List of dicts:
        [
            {
                "txid": "...",
                "anomaly_score": float in [0.0, 1.0],
                "features": { ... engineered feature dictionary ... }
            }
        ]
    """
    if not transactions:
        return []

    # Load cached artifacts
    artifacts = load_model_artifacts(models_dir)
    scaler = artifacts["scaler"]
    feature_cols = artifacts["feature_cols"]
    if_model = artifacts["if_model"]
    ae_model = artifacts["ae_model"]
    calib = artifacts["calibration"]

    # Extract optional context
    ctx = data_context or {}
    network_events = ctx.get("network_events")
    correlation_edges = ctx.get("correlation_edges")
    clusters = ctx.get("clusters")
    graph = ctx.get("graph")

    # 1. Feature Engineering
    features_df = engineer_features(
        transactions=transactions,
        network_events=network_events,
        correlation_edges=correlation_edges,
        clusters=clusters,
        graph=graph,
    )

    # 2. Cleaning & column alignment
    cleaned_df, _ = clean_features(features_df, feature_cols)

    # 3. Scaling using saved scaler (never refit on inference data)
    X_scaled = scaler.transform(cleaned_df.values)

    # 4. Model inference
    if_scores = score_isolation_forest(
        model=if_model,
        X_scaled=X_scaled,
        s_min=calib["s_min"],
        s_max=calib["s_max"],
    )

    ae_scores = score_autoencoder(
        model=ae_model,
        X_scaled=X_scaled,
        err_min=calib["err_min"],
        err_max=calib["err_max"],
    )

    # 5. Combined score
    combined = combine_anomaly_scores(
        if_scores=if_scores,
        ae_scores=ae_scores,
        alpha=calib.get("alpha", 0.5),
    )

    # Build response format
    results: List[Dict[str, Any]] = []
    for idx, tx in enumerate(transactions):
        txid = tx.get("txid", cleaned_df.index[idx])
        score = float(np.clip(combined[idx], 0.0, 1.0))
        # Export feature dict for explainability (Module D)
        feat_dict = {col: float(cleaned_df.iloc[idx][col]) for col in feature_cols}

        results.append({
            "txid": txid,
            "anomaly_score": round(score, 4),
            "features": feat_dict,
        })

    return results
