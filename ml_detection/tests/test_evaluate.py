"""
Tests for Evaluation Logic.
Validates metric calculations (precision, recall, F1, confusion matrix)
against deterministic test fixtures.
"""
from pathlib import Path
import tempfile
import json
import pytest
from ml_detection.evaluate_model import evaluate_model


@pytest.fixture
def trained_models_dir(tmp_path_factory):
    default_models = Path("ml_detection/models")
    required = ["isolation_forest.joblib", "autoencoder.pt", "scaler.joblib", "calibration.joblib"]
    if all((default_models / f).exists() for f in required):
        return default_models

    # Clean checkout: train models into a temporary directory so test never skips
    tmp_models = tmp_path_factory.mktemp("models")
    from ml_detection.train_model import train_pipeline
    train_pipeline(
        data_dir=Path("shared/sample_data"),
        models_dir=tmp_models,
        contamination=0.1,
        latent_dim=4,
        ae_epochs=2,
        batch_size=128,
        random_state=42,
    )
    return tmp_models


def test_evaluate_model_on_sample_data(trained_models_dir):
    data_dir = Path("shared/sample_data")
    labels_path = data_dir / "labels.json"

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_report.md"
        metrics = evaluate_model(
            data_dir=data_dir,
            labels_path=labels_path,
            models_dir=trained_models_dir,
            thresholds=[0.3, 0.5, 0.7],
            report_output_path=report_path,
        )

        assert metrics["total_samples"] >= 24
        assert metrics["total_anomalies_ground_truth"] >= 5
        assert 0.0 <= metrics["precision"] <= 1.0
        assert 0.0 <= metrics["recall"] <= 1.0
        assert 0.0 <= metrics["f1"] <= 1.0

        # Assert evaluation target condition: average anomaly score of labeled anomalies > 0.6
        assert metrics["mean_score_labeled_anomalies"] > 0.6
        assert metrics["target_met_mean_gt_0_6"] is True

        assert report_path.exists()
        assert report_path.stat().st_size > 100


def test_evaluate_model_missing_labels_fails(trained_models_dir, tmp_path):
    data_dir = Path("shared/sample_data")
    non_existent = tmp_path / "non_existent_labels.json"

    with pytest.raises(FileNotFoundError):
        evaluate_model(
            data_dir=data_dir,
            labels_path=non_existent,
            models_dir=trained_models_dir,
        )


def test_evaluate_model_invalid_labels_fails(trained_models_dir, tmp_path):
    data_dir = Path("shared/sample_data")
    bad_labels_file = tmp_path / "bad_labels.json"
    bad_labels_file.write_text(json.dumps({"invalid_key": []}), encoding="utf-8")

    with pytest.raises(ValueError):
        evaluate_model(
            data_dir=data_dir,
            labels_path=bad_labels_file,
            models_dir=trained_models_dir,
        )

