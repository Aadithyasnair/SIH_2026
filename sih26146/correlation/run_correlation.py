"""
Pipeline Runner for Module 2: Correlation, Clustering, Pattern Detection & Risk Propagation
Executes the full pipeline and writes standardized outputs.
"""
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from sih26146.shared.schemas.records import NetworkEvent, BlockchainTxn, CorrelationEdge, Cluster
from sih26146.correlation.graph_builder import build_graph, add_correlation_edges, export_graphml
from sih26146.correlation.correlation_rules import correlate_network_and_blockchain
from sih26146.correlation.pattern_detection import detect_patterns
from sih26146.correlation.risk_propagation import propagate_risk
from sih26146.correlation.entity_clustering import cluster_entities


def run_pipeline(
    sample_dir: Path,
    output_dir: Path = None
) -> Dict[str, Any]:
    if output_dir is None:
        output_dir = sample_dir

    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. Load data
    with open(sample_dir / "network_events.json", "r", encoding="utf-8") as f:
        events_data = json.load(f)
    with open(sample_dir / "blockchain_txns.json", "r", encoding="utf-8") as f:
        txns_data = json.load(f)

    labels_data = {}
    labels_file = sample_dir / "labels.json"
    if labels_file.exists():
        with open(labels_file, "r", encoding="utf-8") as f:
            labels_data = json.load(f)

    events = [NetworkEvent(**e) for e in events_data]
    txns = [BlockchainTxn(**t) for t in txns_data]

    print(f"[1/6] Ingested {len(events)} network events and {len(txns)} blockchain transactions.")

    # 2. Build multi-entity graph
    graph = build_graph(events, txns)
    print(f"[2/6] Built graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges.")

    # 3. Correlate network and blockchain
    corr_edges = correlate_network_and_blockchain(events, txns, time_window_seconds=30.0)
    add_correlation_edges(graph, corr_edges)
    print(f"[3/6] Identified {len(corr_edges)} correlation edges.")

    # 4. Pattern Detection (Peeling chains & CoinJoin mixing)
    pattern_results = detect_patterns(graph, txns)
    flagged_patterns = {k: v for k, v in pattern_results.items() if v.pattern_type != "none"}
    print(f"[4/6] Pattern detection flagged {len(flagged_patterns)} suspicious transaction topologies.")

    # 5. Algorithmic Risk Propagation
    risk_scores = propagate_risk(graph, labels_data)
    print(f"[5/6] Risk scores propagated across {len(risk_scores)} wallet addresses.")

    # 6. Dual-Signal Entity Clustering
    clusters = cluster_entities(graph, txns, risk_scores=risk_scores)
    print(f"[6/6] Formed {len(clusters)} entity clusters with explainable labels and descriptions.")

    # Save outputs
    # correlation_edges.json
    edges_dump = [e.model_dump() for e in corr_edges]
    with open(output_dir / "correlation_edges.json", "w", encoding="utf-8") as f:
        json.dump(edges_dump, f, indent=2)

    # clusters.json
    clusters_dump = [c.model_dump() for c in clusters]
    with open(output_dir / "clusters.json", "w", encoding="utf-8") as f:
        json.dump(clusters_dump, f, indent=2)

    # enriched transactions / alert precursors
    enriched_txns = []
    for tx in txns:
        pat = pattern_results.get(tx.txid)
        # Find highest risk among involved addresses
        involved = tx.input_addresses + tx.output_addresses
        max_involved_risk = max([risk_scores.get(addr, 0.0) for addr in involved], default=0.0)

        tx_dict = tx.model_dump()
        tx_dict["pattern_type"] = pat.pattern_type if pat else "none"
        tx_dict["flags"] = pat.flags if pat else []
        tx_dict["propagated_risk_score"] = max_involved_risk
        enriched_txns.append(tx_dict)

    with open(output_dir / "enriched_txns.json", "w", encoding="utf-8") as f:
        json.dump(enriched_txns, f, indent=2)

    # Export GraphML for Neo4j / integration
    export_graphml(graph, str(output_dir / "entity_graph.graphml"))

    return {
        "graph": graph,
        "correlation_edges": corr_edges,
        "clusters": clusters,
        "pattern_results": pattern_results,
        "risk_scores": risk_scores
    }


def main():
    parser = argparse.ArgumentParser(description="Run Module 2 Correlation Pipeline")
    parser.add_argument("--data-dir", type=str, default="/Users/sufiyankhan/Desktop/SIH2026/sih26146/shared/sample_data")
    parser.add_argument("--output-dir", type=str, default=None)
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    out_dir = Path(args.output_dir) if args.output_dir else data_dir
    run_pipeline(data_dir, out_dir)
    print("\n[SUCCESS] Correlation pipeline finished.")


if __name__ == "__main__":
    main()
