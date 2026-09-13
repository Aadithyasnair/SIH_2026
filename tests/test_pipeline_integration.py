"""
End-to-End Pipeline Integration Test for SIH26146.
Verifies that all active layers (Module B: Correlation, Module C: ML Detection, Module D: Explainability)
work together seamlessly and adhere strictly to the shared schemas.
"""
import pytest
import json
from pathlib import Path
from shared.schemas.records import NetworkEvent, BlockchainTxn, CorrelationEdge, Cluster, Alert
from correlation.graph_builder import build_graph, add_correlation_edges
from correlation.correlation_rules import correlate_network_and_blockchain
from correlation.pattern_detection import detect_patterns
from correlation.risk_propagation import propagate_risk
from correlation.entity_clustering import cluster_entities
from ml_detection.predict import score_transactions
from explainability.generate_alerts import process_upstream_data_to_alerts
from explainability.reason_generator import BANNED_JARGON


@pytest.fixture(scope="module")
def sample_data_dir():
    return Path(__file__).resolve().parents[1] / "shared" / "sample_data"


def test_schema_contracts_and_models(sample_data_dir):
    """Verify that all saved sample datasets validate against shared Pydantic models."""
    from shared.schemas.validate_samples import main as validate_main
    # Must run without raising SystemExit or errors
    validate_main()


def test_end_to_end_layers_b_c_d_integration(sample_data_dir):
    """
    Test end-to-end dataflow from Module B -> Module C -> Module D:
    1. Module B: Ingest txns & events, build graph, correlate, detect patterns, propagate risk.
    2. Module C: Score transactions for ML anomalies (Isolation Forest + Autoencoder).
    3. Module D: Generate plain-language explanations, risk ranking, and valid Alert records.
    """
    with open(sample_data_dir / "network_events.json", "r", encoding="utf-8") as f:
        raw_events = json.load(f)[:100]
    with open(sample_data_dir / "blockchain_txns.json", "r", encoding="utf-8") as f:
        raw_txns = json.load(f)[:50]

    events = [NetworkEvent(**e) for e in raw_events]
    txns = [BlockchainTxn(**t) for t in raw_txns]

    # --- LAYER B: Correlation, Patterns & Risk Propagation ---
    graph = build_graph(events, txns)
    corr_edges = correlate_network_and_blockchain(events, txns, time_window_seconds=60.0)
    add_correlation_edges(graph, corr_edges)
    pattern_results = detect_patterns(graph, txns)

    labels_file = sample_data_dir / "labels.json"
    labels_data = {}
    if labels_file.exists():
        with open(labels_file, "r", encoding="utf-8") as f:
            labels_data = json.load(f)
    risk_scores = propagate_risk(graph, labels_data)
    clusters = cluster_entities(graph, txns, risk_scores=risk_scores)

    # Enrich transactions with Module B signals
    enriched_txns = []
    for tx in txns:
        pat = pattern_results.get(tx.txid)
        involved = tx.input_addresses + tx.output_addresses
        max_involved_risk = max([risk_scores.get(addr, 0.0) for addr in involved], default=0.0)
        tx_dict = tx.model_dump()
        tx_dict["pattern_type"] = pat.pattern_type if pat else "none"
        tx_dict["flags"] = pat.flags if pat else []
        tx_dict["propagated_risk_score"] = max_involved_risk
        enriched_txns.append(tx_dict)

    # --- LAYER C: ML Detection ---
    data_context = {
        "network_events": [e.model_dump() for e in events],
        "correlation_edges": [ce.model_dump() for ce in corr_edges],
        "clusters": [c.model_dump() for c in clusters],
        "graph": graph,
    }
    predictions = score_transactions(enriched_txns, data_context=data_context)
    assert len(predictions) == len(enriched_txns)

    # Prepare inputs for Module D
    upstream_for_d = []
    for tx_dict, pred in zip(enriched_txns, predictions):
        assert 0.0 <= pred["anomaly_score"] <= 1.0
        assert "features" in pred
        record_d = {
            "txid": tx_dict["txid"],
            "involved_addresses": tx_dict["input_addresses"] + tx_dict["output_addresses"],
            "anomaly_score": pred["anomaly_score"],
            "propagated_risk_score": tx_dict["propagated_risk_score"],
            "correlation_confidence": 0.80,
            "cluster_risk_signal": 0.50,
            "pattern_type": tx_dict["pattern_type"],
            "flags": tx_dict["flags"],
            "features": pred["features"],
            "timestamp": tx_dict["timestamp"],
            "countries": ["Germany", "United States"],
            "time_window_minutes": 15.0,
        }
        upstream_for_d.append(record_d)

    # --- LAYER D: Explainability & Alert Generation ---
    alerts = process_upstream_data_to_alerts(upstream_for_d)
    assert len(alerts) == len(upstream_for_d)

    # Verify ranking (descending risk_score)
    scores = [a["risk_score"] for a in alerts]
    assert scores == sorted(scores, reverse=True)

    # Verify every alert conforms strictly to Alert schema
    for alert_dict in alerts:
        alert_obj = Alert(**alert_dict)
        assert alert_obj.alert_id is not None
        assert len(alert_obj.alert_id) > 0
        assert 0.0 <= alert_obj.risk_score <= 1.0
        assert 0.0 <= alert_obj.anomaly_score <= 1.0
        assert alert_obj.explanation is not None
        assert len(alert_obj.explanation) > 0
        assert alert_obj.geo_summary is not None

        # Verify no banned technical jargon in explanation
        expl_lower = alert_obj.explanation.lower()
        for jargon in BANNED_JARGON:
            assert jargon not in expl_lower, f"Banned jargon '{jargon}' found in explanation: {alert_obj.explanation}"
