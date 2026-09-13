"""
Tests for Prediction Interface (score_transactions).
Validates inference format, unseen data behavior, and numeric bounds [0, 1].
"""
import pytest
from pathlib import Path
from ml_detection.predict import score_transactions, clear_artifact_cache


@pytest.fixture
def unseen_txns():
    return [
        {
            "txid": "unseen_tx_normal_01",
            "timestamp": "2026-03-11T10:00:00+00:00",
            "input_addresses": ["1NormalUnseenIn1"],
            "output_addresses": ["1NormalUnseenOut1", "1ChangeUnseen1"],
            "input_amounts": [0.5],
            "output_amounts": [0.3, 0.1998],
            "fee": 0.0002,
            "script_type": "P2WPKH",
            "pattern_type": "none",
            "flags": [],
            "propagated_risk_score": 0.0,
        },
        {
            "txid": "unseen_tx_anom_02",
            "timestamp": "2026-03-11T10:05:00+00:00",
            "input_addresses": ["1IllicitUnseenIn1"],
            "output_addresses": ["1HopUnseen1", "1HopUnseen2"],
            "input_amounts": [10.0],
            "output_amounts": [9.5, 0.4999],
            "fee": 0.0001,
            "script_type": "P2PKH",
            "pattern_type": "peeling_chain",
            "flags": ["rapid_layering_structure"],
            "propagated_risk_score": 0.85,
        },
    ]


def test_score_transactions_empty():
    res = score_transactions([])
    assert res == []


def test_score_transactions_unseen(unseen_txns):
    clear_artifact_cache()
    models_dir = Path("ml_detection/models")
    if not (models_dir / "isolation_forest.joblib").exists():
        pytest.skip("Models not yet trained, skipping prediction test.")

    results = score_transactions(unseen_txns, models_dir=models_dir)
    assert len(results) == 2

    for r in results:
        assert "txid" in r
        assert "anomaly_score" in r
        assert "features" in r

        score = r["anomaly_score"]
        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0

        features = r["features"]
        assert isinstance(features, dict)
        assert len(features) > 15

    # Peeling chain with high propagated risk should score higher than standard normal
    norm_score = results[0]["anomaly_score"]
    anom_score = results[1]["anomaly_score"]
    assert anom_score > norm_score
