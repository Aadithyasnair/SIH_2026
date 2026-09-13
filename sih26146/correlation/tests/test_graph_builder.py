import pytest
import networkx as nx
from sih26146.shared.schemas.records import NetworkEvent, BlockchainTxn, CorrelationEdge
from sih26146.correlation.graph_builder import build_graph, add_correlation_edges


def test_same_txn_edges_link_multi_address_txns():
    """Test requirement (a): SAME_TXN edges link multi-address transactions correctly."""
    events = [
        NetworkEvent(
            event_id="ev_001",
            timestamp="2026-03-10T12:00:00Z",
            src_ip="198.51.100.1",
            dst_ip="83.136.255.40",
            src_port=54321,
            dst_port=8333,
            protocol="TCP",
            packet_size=500,
            src_geo_country="US",
            src_asn="AS15169",
            dst_geo_country="DE",
            dst_asn="AS24940"
        )
    ]
    txns = [
        BlockchainTxn(
            txid="tx_test_multi_in",
            timestamp="2026-03-10T12:00:10Z",
            input_addresses=["addr_in_A", "addr_in_B", "addr_in_C"],
            output_addresses=["addr_out_D", "addr_out_E"],
            input_amounts=[1.0, 2.0, 3.0],
            output_amounts=[4.5, 1.499],
            fee=0.001,
            script_type="P2PKH"
        )
    ]

    G = build_graph(events, txns)

    # Verify nodes
    assert G.has_node("198.51.100.1")
    assert G.nodes["198.51.100.1"]["node_type"] == "ip"
    assert G.has_node("tx_test_multi_in")
    assert G.nodes["tx_test_multi_in"]["node_type"] == "txn"
    assert G.has_node("addr_in_A")
    assert G.nodes["addr_in_A"]["node_type"] == "wallet"

    # Verify SAME_TXN co-input edges between addr_in_A, addr_in_B, addr_in_C
    co_in_edges = [
        (u, v) for u, v, d in G.edges(data=True)
        if d.get("edge_type") == "SAME_TXN" and d.get("relation") == "co_input"
    ]
    assert ("addr_in_A", "addr_in_B") in co_in_edges
    assert ("addr_in_B", "addr_in_A") in co_in_edges
    assert ("addr_in_B", "addr_in_C") in co_in_edges
    assert ("addr_in_A", "addr_in_C") in co_in_edges

    # Verify input and output edges
    in_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("edge_type") == "INPUT_OF"]
    assert ("addr_in_A", "tx_test_multi_in") in in_edges
    out_edges = [(u, v) for u, v, d in G.edges(data=True) if d.get("edge_type") == "OUTPUT_OF"]
    assert ("tx_test_multi_in", "addr_out_D") in out_edges


def test_add_correlation_edges():
    events = [
        NetworkEvent(
            event_id="ev_002",
            timestamp="2026-03-10T12:00:00Z",
            src_ip="198.51.100.2",
            dst_ip="83.136.255.40",
            src_port=54322,
            dst_port=8333,
            protocol="TCP",
            packet_size=400,
            src_geo_country="US",
            src_asn="AS15169",
            dst_geo_country="DE",
            dst_asn="AS24940"
        )
    ]
    txns = [
        BlockchainTxn(
            txid="tx_002",
            timestamp="2026-03-10T12:00:05Z",
            input_addresses=["addr_1"],
            output_addresses=["addr_2"],
            input_amounts=[1.0],
            output_amounts=[0.999],
            fee=0.001,
            script_type="P2PKH"
        )
    ]

    G = build_graph(events, txns)
    corr_edges = [
        CorrelationEdge(
            edge_id="corr_001",
            network_event_id="ev_002",
            txid="tx_002",
            confidence=0.92,
            correlation_type="time_window"
        )
    ]

    add_correlation_edges(G, corr_edges)
    corr_in_g = [
        d for _, _, d in G.edges(data=True)
        if d.get("edge_type") == "CORRELATES_WITH"
    ]
    assert len(corr_in_g) == 1
    assert corr_in_g[0]["confidence"] == 0.92
