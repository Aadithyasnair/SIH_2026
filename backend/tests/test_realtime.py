"""
test_realtime.py - Tests for real-time Bitcoin telemetry, origin estimation,
destination entity identification, and API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.realtime.propagation import estimate_network_origin, simulate_propagation_for_tx
from backend.realtime.entities import identify_address, classify_outputs
from backend.realtime.geolocation import resolve_ip, is_private_or_reserved_ip

client = TestClient(app)

def test_private_ip_check():
    assert is_private_or_reserved_ip("127.0.0.1") is True
    assert is_private_or_reserved_ip("192.168.1.1") is True
    assert is_private_or_reserved_ip("10.0.0.5") is True
    assert is_private_or_reserved_ip("8.8.8.8") is False

def test_resolve_loopback_ip():
    geo = resolve_ip("127.0.0.1")
    assert geo["country_code"] == "LOC"
    assert "Private" in geo["country"]

def test_simulate_propagation_deterministic():
    txid = "4b8af030e2518e27c13a0c5c36a49db2a04620f4f913d8e5784918e9d997ccae"
    hops = simulate_propagation_for_tx(txid)
    assert len(hops) == 5
    assert hops[0]["is_first_seen"] is True
    assert hops[0]["delta_ms"] == 0

    origin = estimate_network_origin(hops)
    assert origin.estimated_country != "Unknown"
    assert origin.confidence_score > 0.4
    assert origin.classification in ("POSSIBLE ORIGIN", "INCONCLUSIVE")

def test_identify_known_entities():
    # Coinbase Prime Custody
    cb = identify_address("bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh")
    assert "Coinbase" in cb["entity_name"]
    assert cb["confidence"] == "High"

    # Binance Cold Storage
    binance = identify_address("34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo")
    assert "Binance" in binance["entity_name"]
    assert "Cayman" in binance["region"]

def test_classify_outputs():
    outputs = [
        {"address": "34xp4vRoCGJym3xR7yCVPFHoCNxv4Twseo", "value_btc": 1.5},
        {"address": "bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh", "value_btc": 0.05}
    ]
    classified = classify_outputs(outputs, origin_country="United States")
    assert len(classified) == 2
    assert classified[0]["role"] in ("Primary Destination", "Change / Return")

def test_api_realtime_status_endpoint():
    res = client.get("/api/realtime/status")
    assert res.status_code == 200
    data = res.json()
    assert "running" in data
    assert "active_p2p_peers" in data

def test_api_realtime_latest_endpoint():
    res = client.get("/api/realtime/latest?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "transactions" in data
    assert isinstance(data["transactions"], list)

def test_api_dataset_info_endpoint():
    res = client.get("/api/dataset-info")
    assert res.status_code == 200
    data = res.json()
    assert "modes" in data
    assert "batch_mode" in data["modes"]
    assert "simulation_mode" in data["modes"]
    assert "realtime_mode" in data["modes"]
    assert data["modes"]["batch_mode"]["ground_truth_anomalies"] == 360

def test_api_analyze_tx_endpoint():
    res = client.post("/api/realtime/analyze-tx", json={"txid": "4b8af030e2518e27c13a0c5c36a49db2a04620f4f913d8e5784918e9d997ccae"})
    assert res.status_code == 200
    data = res.json()
    assert data["txid"] == "4b8af030e2518e27c13a0c5c36a49db2a04620f4f913d8e5784918e9d997ccae"
    assert "origin" in data
    assert "destinations" in data
    assert "propagation_hops" in data
