import pytest
from sih26146.shared.schemas.records import BlockchainTxn, Cluster
from sih26146.correlation.graph_builder import build_graph
from sih26146.correlation.query_api import get_subgraph, get_clusters, get_cluster_by_id


def test_subgraph_query_structure_and_depth():
    txns = [
        BlockchainTxn(
            txid="tx_center",
            timestamp="2026-03-10T12:00:00Z",
            input_addresses=["wallet_in_1"],
            output_addresses=["wallet_out_1"],
            input_amounts=[1.0],
            output_amounts=[0.99],
            fee=0.01,
            script_type="P2PKH"
        ),
        BlockchainTxn(
            txid="tx_next_hop",
            timestamp="2026-03-10T12:05:00Z",
            input_addresses=["wallet_out_1"],
            output_addresses=["wallet_out_2"],
            input_amounts=[0.99],
            output_amounts=[0.98],
            fee=0.01,
            script_type="P2PKH"
        )
    ]

    G = build_graph([], txns)
    sub = get_subgraph(G, "tx_center", depth=2)

    assert "nodes" in sub and "edges" in sub
    assert isinstance(sub["nodes"], list)
    assert isinstance(sub["edges"], list)

    node_ids = [n["id"] for n in sub["nodes"]]
    assert "tx_center" in node_ids
    assert "wallet_in_1" in node_ids
    assert "wallet_out_1" in node_ids


def test_clusters_query():
    clusters = [
        Cluster(
            cluster_id="cl_001",
            label="Mixing Cluster",
            member_addresses=["addr_1", "addr_2"],
            member_count=2,
            avg_risk_score=0.85,
            description="High risk mixing pattern.",
            clustering_method="common_input_ownership+node2vec_embedding"
        )
    ]

    all_cl = get_clusters(clusters)
    assert len(all_cl) == 1
    assert all_cl[0]["cluster_id"] == "cl_001"

    single_cl = get_cluster_by_id(clusters, "cl_001")
    assert single_cl is not None
    assert single_cl["label"] == "Mixing Cluster"

    none_cl = get_cluster_by_id(clusters, "non_existent")
    assert none_cl is None
