"""
Tests for Absence of Label Leakage.
Formally verifies that ground-truth labels are never imported, referenced, or included
in training features, model definitions, or preprocessing pipelines.
"""
import inspect
from ml_detection import feature_engineering
from ml_detection import models_components
from ml_detection import train_model


def test_no_labels_in_feature_columns():
    """Verify no feature column name references labels or ground truth."""
    forbidden = ["label", "ground_truth", "target", "is_anomalous", "is_illicit", "fraud"]
    for col in feature_engineering.FEATURE_COLUMNS:
        for f in forbidden:
            assert f not in col.lower(), f"Forbidden substring '{f}' found in feature '{col}'"


def test_feature_engineering_signature_has_no_labels():
    """Verify engineer_features does not accept a labels parameter."""
    sig = inspect.signature(feature_engineering.engineer_features)
    param_names = list(sig.parameters.keys())
    for p in param_names:
        assert "label" not in p.lower()
        assert "target" not in p.lower()
        assert "ground_truth" not in p.lower()


def test_train_model_does_not_call_load_labels():
    """Inspect train_model source to ensure load_labels is not invoked."""
    src = inspect.getsource(train_model)
    assert "load_labels" not in src, "train_model must not call load_labels!"
    assert "labels.json" not in src, "train_model must not read labels.json!"


def test_models_components_no_label_reference():
    """Inspect models_components source to ensure models are strictly unsupervised."""
    src = inspect.getsource(models_components)
    assert "labels" not in src.lower(), "models_components should be strictly unsupervised"
