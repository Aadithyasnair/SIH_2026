import json
import os

from shared.schemas.records import NetworkEvent, BlockchainTxn, CorrelationEdge, Alert, Cluster

SAMPLE_DATA = os.path.join(os.path.dirname(__file__), "..", "..", "shared", "sample_data")


def _validate(filename, model):
    path = os.path.join(SAMPLE_DATA, filename)
    assert os.path.exists(path), f"{filename} missing — that module hasn't shipped output yet"
    with open(path) as f:
        records = json.load(f)
    assert len(records) > 0, f"{filename} is empty"
    for rec in records:
        model(**rec)


def test_module_a_network_events():
    _validate("network_events.json", NetworkEvent)


def test_module_a_blockchain_txns():
    _validate("blockchain_txns.json", BlockchainTxn)


def test_module_b_correlation_edges():
    _validate("correlation_edges.json", CorrelationEdge)


def test_module_b_clusters():
    _validate("clusters.json", Cluster)


def test_module_d_alerts():
    _validate("alerts.json", Alert)
