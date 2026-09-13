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


def test_compute_address_bursts_sorted_window():
    from ml_detection.feature_engineering import compute_address_bursts

    txs = [
        {"txid": "tx1", "timestamp": "2026-03-10T12:00:00+00:00", "input_addresses": ["addrA"]},
        {"txid": "tx2", "timestamp": "2026-03-10T12:15:00+00:00", "input_addresses": ["addrA", "addrB"]},
        {"txid": "tx3", "timestamp": "2026-03-10T12:30:00+00:00", "input_addresses": ["addrB"]},
        {"txid": "tx4", "timestamp": "2026-03-10T15:00:00+00:00", "input_addresses": ["addrA"]},  # >1h away
    ]
    bursts = compute_address_bursts(txs, window_seconds=3600.0)
    # tx1 overlaps with tx2 (shares addrA) within 1h: count = 2
    assert bursts["tx1"] == 2
    # tx2 overlaps with tx1 (addrA) and tx3 (addrB): count = 3
    assert bursts["tx2"] == 3
    # tx3 overlaps with tx2 (addrB): count = 2
    assert bursts["tx3"] == 2
    # tx4 is >1h away: count = 1
    assert bursts["tx4"] == 1


def test_cross_border_single_event_us_to_de(sample_txn):
    ev = {
        "event_id": "ev_test_1",
        "src_ip": "1.2.3.4",
        "src_geo_country": "US",
        "dst_geo_country": "DE",
        "src_asn": "AS123",
        "dst_port": 8333,
    }
    feat = extract_features_for_txn(sample_txn, associated_events=[ev])
    assert feat["is_cross_border"] == 1.0


def test_dst_port_signals_only_destination_port(sample_txn):
    # Only src_port is 8333, dst_port is 443 -> should NOT trigger dst_port_is_standard_bitcoin
    ev_src_only = {
        "event_id": "ev_src",
        "src_port": 8333,
        "dst_port": 443,
    }
    feat1 = extract_features_for_txn(sample_txn, associated_events=[ev_src_only])
    assert feat1["dst_port_is_standard_bitcoin"] == 0.0
    assert feat1["dst_port_is_tor_proxy"] == 0.0

    # dst_port is 8333 -> should trigger dst_port_is_standard_bitcoin
    ev_dst = {
        "event_id": "ev_dst",
        "src_port": 54321,
        "dst_port": 8333,
    }
    feat2 = extract_features_for_txn(sample_txn, associated_events=[ev_dst])
    assert feat2["dst_port_is_standard_bitcoin"] == 1.0


def test_clean_features_with_fitted_medians():
    df = pd.DataFrame({"total_input_btc": [np.nan]}, index=["tx_test"])
    fitted = {"total_input_btc": 42.5}
    cleaned, cols = clean_features(df, expected_cols=["total_input_btc"], impute_medians=fitted)
    assert cleaned.loc["tx_test", "total_input_btc"] == 42.5

