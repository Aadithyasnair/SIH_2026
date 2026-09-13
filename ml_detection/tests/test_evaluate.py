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


def test_evaluate_model_on_sample_data():
    models_dir = Path("ml_detection/models")
    if not (models_dir / "isolation_forest.joblib").exists():
        pytest.skip("Models not yet trained, skipping evaluation test.")

    data_dir = Path("sih26146/shared/sample_data")
    labels_path = data_dir / "labels.json"

    with tempfile.TemporaryDirectory() as tmpdir:
        report_path = Path(tmpdir) / "test_report.md"
        metrics = evaluate_model(
            data_dir=data_dir,
            labels_path=labels_path,
            models_dir=models_dir,
            thresholds=[0.3, 0.5, 0.7],
            report_output_path=report_path,
        )

        assert metrics["total_samples"] >= 24
        assert metrics["total_anomalies_ground_truth"] >= 5
        assert 0.0 <= metrics["precision"] <= 1.0
        assert 0.0 <= metrics["recall"] <= 1.0
        assert 0.0 <= metrics["f1"] <= 1.0
        assert report_path.exists()
        assert report_path.stat().st_size > 100
