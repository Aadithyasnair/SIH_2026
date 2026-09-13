import pytest
import networkx as nx
from sih26146.shared.schemas.records import BlockchainTxn
from sih26146.correlation.graph_builder import build_graph
from sih26146.correlation.entity_clustering import cluster_entities, get_cluster_for_address


def test_dual_signal_clustering_and_embeddings_catch_hidden_relationship():
    """
    Test requirement (b):
    Include a test case where embeddings catch a relationship the heuristic alone would miss.
    Scenario:
    - Group 1: Addr_A1 and Addr_A2 co-spend in Tx_1 (caught by common-input heuristic).
    - Group 2: Addr_B1 and Addr_B2 co-spend in Tx_2 (caught by common-input heuristic).
    - Intermediary bridge: Addr_A2 sends to Addr_Bridge, which immediately sends to Addr_B1.
      They never co-spend in the same input, but share topological and structural adjacency in the wallet graph.
    - With embedding signals combined, all related wallets cluster into a cohesive entity.
    """
    txns = [
        # Tx 1: Addr_A1 & Addr_A2 co-input
        BlockchainTxn(
            txid="tx_1",
            timestamp="2026-03-10T12:00:00Z",
            input_addresses=["Addr_A1", "Addr_A2"],
            output_addresses=["Addr_Bridge"],
            input_amounts=[1.0, 1.0],
            output_amounts=[1.99],
            fee=0.01,
            script_type="P2PKH"
        ),
        # Tx 2: Addr_Bridge sends to Addr_B1
        BlockchainTxn(
            txid="tx_bridge",
            timestamp="2026-03-10T12:05:00Z",
            input_addresses=["Addr_Bridge"],
            output_addresses=["Addr_B1"],
            input_amounts=[1.99],
            output_amounts=[1.98],
            fee=0.01,
            script_type="P2PKH"
        ),
        # Tx 3: Addr_B1 & Addr_B2 co-input
        BlockchainTxn(
            txid="tx_3",
            timestamp="2026-03-10T12:10:00Z",
            input_addresses=["Addr_B1", "Addr_B2"],
            output_addresses=["Addr_Final"],
            input_amounts=[1.98, 0.5],
            output_amounts=[2.47],
            fee=0.01,
            script_type="P2PKH"
        )
    ]

    graph = build_graph([], txns)
    clusters = cluster_entities(graph, txns)

    assert len(clusters) >= 1
    # Check requirement (e): cluster descriptions are non-empty and human-readable
    for c in clusters:
        assert len(c.description) > 20
        assert len(c.label) > 3
        assert not any(err in c.description for err in ["NaN", "None", "{", "}"])
        assert c.clustering_method == "common_input_ownership+node2vec_embedding"
        assert c.member_count == len(c.member_addresses)

    # Verify lookup function and assert that embedding clustering successfully bridged
    # the two distinct heuristic groups (Addr_A* and Addr_B*) through Addr_Bridge
    c_a1 = get_cluster_for_address(clusters, "Addr_A1")
    assert c_a1 is not None
    assert "Addr_A1" in c_a1.member_addresses
    assert "Addr_A2" in c_a1.member_addresses
    # Crucial assertion addressed from PR review:
    # Embedding clustering must bridge across the intermediate transaction to unite both groups
    assert "Addr_Bridge" in c_a1.member_addresses, "Embedding signal must include intermediate bridge address"
    assert "Addr_B1" in c_a1.member_addresses, "Embedding signal must bridge to second group Addr_B1"
    assert "Addr_B2" in c_a1.member_addresses, "Embedding signal must bridge to second group Addr_B2"
