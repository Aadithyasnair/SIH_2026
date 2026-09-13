"""
Tests for ML Model Components in Module C.
Validates Isolation Forest, PyTorch Autoencoder training, scoring,
normalization, saving, and loading.
"""
import pytest
import numpy as np
import torch
import tempfile
from pathlib import Path

from ml_detection.models_components import (
    Autoencoder,
    train_isolation_forest,
    score_isolation_forest,
    train_autoencoder,
    score_autoencoder,
    combine_anomaly_scores,
)


@pytest.fixture
def synthetic_features():
    np.random.seed(42)
    # 20 samples, 10 features
    return np.random.randn(20, 10).astype(np.float64)


def test_isolation_forest_train_and_score(synthetic_features):
    model, s_min, s_max = train_isolation_forest(
        synthetic_features, contamination=0.1, random_state=42
    )
    scores = score_isolation_forest(model, synthetic_features, s_min, s_max)

    assert len(scores) == len(synthetic_features)
    assert np.all(scores >= 0.0)
    assert np.all(scores <= 1.0)


def test_autoencoder_train_and_score(synthetic_features):
    model, err_min, err_max = train_autoencoder(
        synthetic_features,
        latent_dim=4,
        epochs=15,
        batch_size=4,
        random_state=42,
    )
    scores = score_autoencoder(model, synthetic_features, err_min, err_max)

    assert len(scores) == len(synthetic_features)
    assert np.all(scores >= 0.0)
    assert np.all(scores <= 1.0)


def test_combine_anomaly_scores():
    if_scores = np.array([0.1, 0.5, 0.9])
    ae_scores = np.array([0.2, 0.6, 0.8])
    combined = combine_anomaly_scores(if_scores, ae_scores, alpha=0.5)

    assert len(combined) == 3
    assert np.isclose(combined[0], 0.15)
    assert np.isclose(combined[1], 0.55)
    assert np.isclose(combined[2], 0.85)
    assert np.all(combined >= 0.0) and np.all(combined <= 1.0)


def test_autoencoder_state_dict_save_load(synthetic_features):
    input_dim = synthetic_features.shape[1]
    model = Autoencoder(input_dim=input_dim, latent_dim=4)

    with tempfile.TemporaryDirectory() as tmpdir:
        pt_path = Path(tmpdir) / "test_ae.pt"
        torch.save(
            {"state_dict": model.state_dict(), "input_dim": input_dim, "latent_dim": 4},
            pt_path,
        )

        loaded_ckpt = torch.load(pt_path, map_location="cpu", weights_only=False)
        loaded_model = Autoencoder(input_dim=loaded_ckpt["input_dim"], latent_dim=loaded_ckpt["latent_dim"])
        loaded_model.load_state_dict(loaded_ckpt["state_dict"])
        loaded_model.eval()

        # Check output matches
        x = torch.tensor(synthetic_features[:2], dtype=torch.float32)
        with torch.no_grad():
            out_orig = model(x)
            out_loaded = loaded_model(x)

        assert torch.allclose(out_orig, out_loaded)


def test_train_pipeline_save_and_load(tmp_path):
    """
    End-to-end test verifying train_pipeline saves all expected artifacts
    and load_model_artifacts successfully loads them for inference.
    """
    from ml_detection.train_model import train_pipeline
    from ml_detection.predict import load_model_artifacts, score_transactions, clear_artifact_cache
    from ml_detection.data_loader import load_blockchain_txns

    data_dir = Path("shared/sample_data")
    txns = load_blockchain_txns(data_dir)

    clear_artifact_cache()
    # Fast training run in temporary directory
    train_result = train_pipeline(
        data_dir=data_dir,
        models_dir=tmp_path,
        contamination=0.1,
        latent_dim=4,
        ae_epochs=2,
        batch_size=128,
        random_state=42,
    )

    # Check all required artifact files exist
    expected_artifacts = [
        "scaler.joblib",
        "feature_cols.joblib",
        "isolation_forest.joblib",
        "autoencoder.pt",
        "calibration.joblib",
        "impute_medians.joblib",
        "wallet_histories.joblib",
    ]
    for art in expected_artifacts:
        art_path = tmp_path / art
        assert art_path.exists(), f"Missing artifact {art} in {tmp_path}"
        assert art_path.stat().st_size > 0

    # Test load_model_artifacts
    artifacts = load_model_artifacts(models_dir=tmp_path)
    assert artifacts["scaler"] is not None
    assert len(artifacts["feature_cols"]) > 15
    assert artifacts["if_model"] is not None
    assert artifacts["ae_model"] is not None
    assert "s_min" in artifacts["calibration"]
    assert isinstance(artifacts["impute_medians"], dict)
    assert isinstance(artifacts["wallet_histories"], dict)

    # Test scoring with loaded artifacts
    preds = score_transactions(transactions=txns[:5], models_dir=tmp_path)
    assert len(preds) == 5
    for p in preds:
        assert 0.0 <= p["anomaly_score"] <= 1.0

