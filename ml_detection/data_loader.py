"""
Data loader utilities for Module C (AI/ML Detection).
Loads shared records, pipeline outputs, and evaluation labels safely.
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import json
import networkx as nx

from sih26146.shared.schemas.records import (
    NetworkEvent,
    BlockchainTxn,
    CorrelationEdge,
    Cluster,
)


def load_json_records(file_path: Path) -> List[Dict[str, Any]]:
    """Load records from a JSON file returning a list of dicts."""
    if not file_path.exists():
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    return []


def load_blockchain_txns(sample_dir: Path) -> List[Dict[str, Any]]:
    """
    Load transactions from sample_dir.
    Prefers enriched_txns.json (Module B output with pattern_type, flags, propagated_risk_score).
    Falls back to blockchain_txns.json with default enriched fields.
    """
    enriched_path = sample_dir / "enriched_txns.json"
    if enriched_path.exists():
        return load_json_records(enriched_path)

    raw_path = sample_dir / "blockchain_txns.json"
    if raw_path.exists():
        raw_txns = load_json_records(raw_path)
        # Populate safe baseline defaults for missing Module B signals
        for tx in raw_txns:
            tx.setdefault("pattern_type", "none")
            tx.setdefault("flags", [])
            tx.setdefault("propagated_risk_score", 0.0)
        return raw_txns

    return []


def load_network_events(sample_dir: Path) -> List[Dict[str, Any]]:
    """Load network events from network_events.json."""
    return load_json_records(sample_dir / "network_events.json")


def load_correlation_edges(sample_dir: Path) -> List[Dict[str, Any]]:
    """Load correlation edges from correlation_edges.json."""
    return load_json_records(sample_dir / "correlation_edges.json")


def load_clusters(sample_dir: Path) -> List[Dict[str, Any]]:
    """Load entity clusters from clusters.json."""
    return load_json_records(sample_dir / "clusters.json")


def load_entity_graph(sample_dir: Path) -> Optional[nx.Graph]:
    """Load entity graph from entity_graph.graphml if present."""
    graph_path = sample_dir / "entity_graph.graphml"
    if graph_path.exists():
        try:
            return nx.read_graphml(graph_path)
        except Exception:
            return None
    return None


def load_labels(labels_path: Path) -> Dict[str, Any]:
    """
    Load ground truth evaluation labels from labels.json.
    IMPORTANT: Ground truth labels must ONLY be used during evaluation,
    never as model features or during unsupervised training.
    """
    if not labels_path.exists():
        return {}
    with open(labels_path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_txid_to_network_events(
    edges: List[Dict[str, Any]],
    events: List[Dict[str, Any]],
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Build mapping of txid -> list of associated NetworkEvents via CorrelationEdges.
    """
    event_by_id = {e["event_id"]: e for e in events if "event_id" in e}
    txid_map: Dict[str, List[Dict[str, Any]]] = {}
    for edge in edges:
        txid = edge.get("txid")
        event_id = edge.get("network_event_id")
        if txid and event_id in event_by_id:
            txid_map.setdefault(txid, []).append(event_by_id[event_id])
    return txid_map
