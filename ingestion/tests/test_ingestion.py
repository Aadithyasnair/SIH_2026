"""
Unit Tests for SIH26146 Module 1: Data Ingestion & Preprocessing
"""

import json
from pathlib import Path
import pytest

from ingestion.time_aligner import normalize_timestamp
from ingestion.data_validator import DataValidator
from ingestion.network_parser import parse_network_events
from ingestion.blockchain_parser import parse_blockchain_txns
from ingestion.synthetic_generator import SyntheticDataGenerator
from shared.schemas.records import NetworkEvent, BlockchainTxn


def test_time_aligner_iso_string():
    raw_ts = "2026-01-15T08:37:00+00:00"
    normalized = normalize_timestamp(raw_ts)
    assert normalized.startswith("2026-01-15T08:37:00")


def test_time_aligner_epoch_seconds():
    # Unix timestamp for 2026-01-15 08:37:00 UTC = 1768466220
    normalized = normalize_timestamp(1768466220)
    assert "2026-01-15" in normalized


def test_time_aligner_epoch_millis():
    normalized = normalize_timestamp(1768466220000)
    assert "2026-01-15" in normalized


def test_time_aligner_invalid():
    with pytest.raises(ValueError):
        normalize_timestamp("invalid_date_string_xyz")


def test_data_validator_quarantine():
    validator = DataValidator()

    # Valid NetworkEvent dict
    valid_rec = {
        "event_id": "net_test_123",
        "timestamp": "2026-01-15T08:37:00+00:00",
        "src_ip": "1.2.3.4",
        "dst_ip": "5.6.7.8",
        "src_port": 50000,
        "dst_port": 8333,
        "protocol": "TCP",
        "packet_size": 1000,
        "src_geo_country": "US",
        "src_asn": "AS1234",
        "dst_geo_country": "US",
        "dst_asn": "AS1234",
    }
    event = validator.validate_record(valid_rec, NetworkEvent)
    assert event is not None
    assert event.event_id == "net_test_123"

    # Malformed record (packet_size bad type)
    bad_rec = dict(valid_rec)
    bad_rec["packet_size"] = "not_an_int"
    quarantined_event = validator.validate_record(bad_rec, NetworkEvent)
    assert quarantined_event is None
    assert validator.get_quarantine_stats()["total_quarantined"] == 1


def test_network_parser():
    raw_data = [
        {
            "event_id": "net_001",
            "timestamp": "2026-01-15T08:37:00+00:00",
            "src_ip": "10.0.0.1",
            "dst_ip": "10.0.0.2",
            "port": 8333,
            "protocol": "TCP",
            "packet_size": 512,
        },
        {
            "event_id": "net_002_bad",
            "timestamp": "invalid_time",
            "src_ip": "10.0.0.1",
            "dst_ip": "10.0.0.2",
        }
    ]

    validator = DataValidator()
    events = parse_network_events(raw_data, validator=validator)
    assert len(events) == 1
    assert events[0].event_id == "net_001"
    assert validator.get_quarantine_stats()["total_quarantined"] == 1


def test_blockchain_parser():
    raw_txns = [
        # Simplified format (single wallet)
        {
            "txid": "tx_simplified_001",
            "timestamp": "2026-01-15T08:37:00+00:00",
            "wallet_from": "1SenderWallet123",
            "wallet_to": "1ReceiverWallet456",
            "amount_btc": 1.5,
            "fee": 0.0001,
        },
        # Full multi-address format
        {
            "txid": "tx_multi_002",
            "timestamp": "2026-01-15T08:38:00+00:00",
            "input_addresses": ["1InA", "1InB"],
            "output_addresses": ["1OutA"],
            "input_amounts": [1.0, 1.0],
            "output_amounts": [1.999],
            "fee": 0.001,
            "script_type": "P2WPKH",
        },
    ]

    validator = DataValidator()
    txns = parse_blockchain_txns(raw_txns, validator=validator)
    assert len(txns) == 2
    assert txns[0].wallet_from == "1SenderWallet123"
    assert txns[0].amount_btc == 1.5
    assert txns[1].script_type == "P2WPKH"


def test_synthetic_generator_small():
    gen = SyntheticDataGenerator(network_count=100, txn_count=50, anomaly_ratio=0.10, inject_anomalies=True, seed=123)
    net_events, bc_txns, labels = gen.generate()

    assert len(net_events) >= 100
    assert len(bc_txns) >= 50
    assert len(labels["scenarios"]) > 0
    assert len(labels["anomalous_txids"]) > 0

    # Ensure anomaly percentage >= 5%
    anomaly_tx_count = len(labels["anomalous_txids"])
    anomaly_pct = anomaly_tx_count / len(bc_txns)
    assert anomaly_pct >= 0.05, f"Expected anomaly percentage >= 5%, got {anomaly_pct * 100:.2f}%"


def test_synthetic_generator_full_count():
    gen = SyntheticDataGenerator(network_count=5000, txn_count=2000, anomaly_ratio=0.07, inject_anomalies=True, seed=42)
    net_events, bc_txns, labels = gen.generate()

    assert len(net_events) == 5000
    assert len(bc_txns) == 2000
    assert len(labels["anomalous_txids"]) >= 100 # >5% of 2000
    assert "rapid_ip_burst" in labels["anomalous_txids"].values()
    assert "smurfing_consolidation" in labels["anomalous_txids"].values()
    assert "peeling_chain" in labels["anomalous_txids"].values()
    assert "coinjoin_mixing" in labels["anomalous_txids"].values()
