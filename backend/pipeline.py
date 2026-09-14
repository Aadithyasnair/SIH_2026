"""
End-to-End Pipeline Orchestration for SIH26146 Backend.
Coordinates:
  Stage 1: Data Loading & Validation (Module A)
  Stage 2: Correlation, Clustering, Pattern Detection, and Risk Propagation (Module B)
  Stage 3: AI/ML Anomaly Detection Scoring (Module C)
  Stage 4: Score Merging (Creates shared/sample_data/anomaly_scores.json)
  Stage 5: Explainability & Alert Generation (Module D)
  Stage 6: Database Persistence (Loads real alerts & clusters into Postgres)
"""
import sys
import json
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Callable

# Ensure repo root is on sys.path
REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from shared.schemas.records import NetworkEvent, BlockchainTxn, Alert, Cluster
from correlation.graph_builder import build_graph, add_correlation_edges, export_graphml
from correlation.correlation_rules import correlate_network_and_blockchain
from correlation.pattern_detection import detect_patterns
from correlation.risk_propagation import propagate_risk
from correlation.entity_clustering import cluster_entities
from ml_detection.predict import score_transactions
from ml_detection.merge_scores import merge_pipeline_scores
from explainability.generate_alerts import process_upstream_data_to_alerts

logger = logging.getLogger("pipeline")


def run_full_pipeline(
    data_dir: Optional[Path] = None,
    output_dir: Optional[Path] = None,
    progress_callback: Optional[Callable[[float, str], None]] = None,
) -> Dict[str, Any]:
    """
    Executes the entire 6-module pipeline end-to-end:
    Ingestion -> Correlation -> ML Detection -> Score Merging -> Explainability.
    Returns summary metrics and generated records.
    """
    if data_dir is None:
        data_dir = REPO_ROOT / "shared" / "sample_data"
    if output_dir is None:
        output_dir = data_dir

    def report(progress: float, stage: str):
        if progress_callback:
            progress_callback(progress, stage)
        print(f"[{int(progress * 100)}%] {stage}")

    report(0.05, "Loading ingested network events and blockchain transactions...")
    events_file = data_dir / "network_events.json"
    txns_file = data_dir / "blockchain_txns.json"
    labels_file = data_dir / "labels.json"

    if not events_file.exists() or not txns_file.exists():
        raise FileNotFoundError(f"Missing required input files in {data_dir}")

    with open(events_file, "r", encoding="utf-8") as f:
        raw_events = json.load(f)
    with open(txns_file, "r", encoding="utf-8") as f:
        raw_txns = json.load(f)

    labels_data = {}
    if labels_file.exists():
        with open(labels_file, "r", encoding="utf-8") as f:
            labels_data = json.load(f)

    events = [NetworkEvent(**e) for e in raw_events]
    txns = [BlockchainTxn(**t) for t in raw_txns]

    # --- STAGE 2: Correlation, Graph, Patterns, Risk Propagation, Clustering ---
    report(0.20, f"Building entity graph from {len(events)} events and {len(txns)} txns...")
    graph = build_graph(events, txns)

    report(0.35, "Correlating network events with blockchain transactions...")
    corr_edges = correlate_network_and_blockchain(events, txns, time_window_seconds=30.0)
    add_correlation_edges(graph, corr_edges)

    report(0.45, "Detecting peeling chains and CoinJoin mixing topologies...")
    pattern_results = detect_patterns(graph, txns)

    report(0.55, "Propagating risk scores from seed illicit wallets...")
    risk_scores = propagate_risk(graph, labels_data)

    report(0.65, "Clustering wallet entities via Common-Input-Ownership and Node2Vec embeddings...")
    clusters = cluster_entities(graph, txns, risk_scores=risk_scores)

    # Save Module B outputs
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(output_dir / "correlation_edges.json", "w", encoding="utf-8") as f:
        json.dump([e.model_dump() for e in corr_edges], f, indent=2)

    with open(output_dir / "clusters.json", "w", encoding="utf-8") as f:
        json.dump([c.model_dump() for c in clusters], f, indent=2)

    export_graphml(graph, str(output_dir / "entity_graph.graphml"))

    # Enrich transactions
    enriched_txns = []
    for tx in txns:
        pat = pattern_results.get(tx.txid)
        involved = tx.input_addresses + tx.output_addresses
        max_risk = max([risk_scores.get(addr, 0.0) for addr in involved], default=0.0)
        tx_dict = tx.model_dump()
        tx_dict["pattern_type"] = pat.pattern_type if pat else "none"
        tx_dict["flags"] = pat.flags if pat else []
        tx_dict["propagated_risk_score"] = max_risk
        enriched_txns.append(tx_dict)

    with open(output_dir / "enriched_txns.json", "w", encoding="utf-8") as f:
        json.dump(enriched_txns, f, indent=2)

    # --- STAGE 3: AI/ML Detection ---
    report(0.75, "Scoring transactions via Isolation Forest + Autoencoder models...")
    context = {
        "network_events": [e.model_dump() for e in events],
        "correlation_edges": [ce.model_dump() for ce in corr_edges],
        "clusters": [c.model_dump() for c in clusters],
        "graph": graph,
    }
    predictions = score_transactions(enriched_txns, data_context=context)

    # --- STAGE 4: Score Merging ---
    report(0.85, "Merging ML anomaly scores with Module B features into anomaly_scores.json...")
    anomaly_scores_path = output_dir / "anomaly_scores.json"
    merged_records = merge_pipeline_scores(
        enriched_txns=enriched_txns,
        predictions=predictions,
        clusters=[c.model_dump() for c in clusters],
        correlation_edges=[ce.model_dump() for ce in corr_edges],
        network_events=[e.model_dump() for e in events],
        output_path=anomaly_scores_path,
    )

    # --- STAGE 5: Explainability & Alert Generation ---
    report(0.92, "Generating ranked alerts with SHAP plain-language explanations...")
    alerts = process_upstream_data_to_alerts(merged_records)

    # Persist alerts to shared, explainability, and root
    for out_p in [
        output_dir / "alerts.json",
        REPO_ROOT / "explainability" / "alerts.json",
        REPO_ROOT / "alerts.json",
    ]:
        out_p.parent.mkdir(parents=True, exist_ok=True)
        with open(out_p, "w", encoding="utf-8") as f:
            json.dump(alerts, f, indent=2)

    report(1.0, f"Pipeline complete. Generated {len(alerts)} alerts, {len(clusters)} clusters.")

    return {
        "alerts_count": len(alerts),
        "clusters_count": len(clusters),
        "correlation_edges_count": len(corr_edges),
        "events_count": len(events),
        "txns_count": len(txns),
        "alerts": alerts,
        "clusters": clusters,
    }


if __name__ == "__main__":
    run_full_pipeline()
