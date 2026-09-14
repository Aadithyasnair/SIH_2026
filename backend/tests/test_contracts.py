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


def test_alerts_cluster_id_consistency():
    """Confirm cluster_id references in Alert records correspond to real Cluster records."""
    alerts_path = os.path.join(SAMPLE_DATA, "alerts.json")
    clusters_path = os.path.join(SAMPLE_DATA, "clusters.json")
    with open(alerts_path) as f:
        alerts = json.load(f)
    with open(clusters_path) as f:
        clusters = json.load(f)

    valid_cluster_ids = {c["cluster_id"] for c in clusters}
    for a in alerts:
        cid = a.get("cluster_id")
        if cid is not None:
            assert cid in valid_cluster_ids, f"Alert {a.get('alert_id')} references orphaned cluster_id '{cid}'"
