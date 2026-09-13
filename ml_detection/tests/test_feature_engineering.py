"""
Tests for Feature Engineering in Module C.
Validates extraction, robust handling of missing/sparse signals, and absence of NaNs.
"""
import pytest
import numpy as np
import pandas as pd
from ml_detection.feature_engineering import (
    engineer_features,
    clean_features,
    extract_features_for_txn,
    FEATURE_COLUMNS,
)


@pytest.fixture
def sample_txn():
    return {
        "txid": "tx_test_001",
        "timestamp": "2026-03-10T12:00:00+00:00",
        "input_addresses": ["1TestAddrIn1", "1TestAddrIn2"],
        "output_addresses": ["1TestAddrOut1", "1TestAddrOut2"],
        "input_amounts": [1.5, 2.5],
        "output_amounts": [3.8, 0.1998],
        "fee": 0.0002,
        "script_type": "P2WPKH",
        "pattern_type": "none",
        "flags": [],
        "propagated_risk_score": 0.0,
    }


def test_feature_columns_definition():
    assert len(FEATURE_COLUMNS) > 15
    # Ensure no label fields are defined as features
    for col in FEATURE_COLUMNS:
        assert "label" not in col.lower()
        assert "ground_truth" not in col.lower()


def test_extract_features_for_single_txn(sample_txn):
    feat = extract_features_for_txn(sample_txn)
    assert isinstance(feat, dict)
    for col in FEATURE_COLUMNS:
        assert col in feat
        assert isinstance(feat[col], (int, float))
        assert not np.isnan(feat[col])
        assert not np.isinf(feat[col])


def test_engineer_features_empty_context(sample_txn):
    txns = [sample_txn]
    df = engineer_features(txns)
    assert len(df) == 1
    assert df.index[0] == "tx_test_001"
    for col in FEATURE_COLUMNS:
        assert col in df.columns


def test_clean_features_handles_nan_and_inf():
    dirty_data = {
        "total_input_btc": [np.nan, 2.0, np.inf],
        "total_output_btc": [1.0, -np.inf, 3.0],
    }
    dirty_df = pd.DataFrame(dirty_data, index=["tx1", "tx2", "tx3"])
    cleaned, cols = clean_features(dirty_df, expected_cols=FEATURE_COLUMNS)

    assert not cleaned.isna().any().any()
    assert not np.isinf(cleaned.values).any()
    assert len(cols) == len(FEATURE_COLUMNS)
    assert list(cleaned.columns) == FEATURE_COLUMNS


def test_robust_to_missing_fields():
    sparse_txn = {"txid": "sparse_tx_1"}
    feat = extract_features_for_txn(sparse_txn)
    assert feat["total_input_btc"] == 0.0
    assert feat["total_output_btc"] == 0.0
    assert feat["pattern_type_code"] == 0.0
    assert feat["propagated_risk_score"] == 0.0
