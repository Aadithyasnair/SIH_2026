import pytest
from shared.schemas.records import NetworkEvent, BlockchainTxn
from correlation.correlation_rules import correlate_network_and_blockchain


def test_correlation_time_window_and_confidence_bounds():
    """Test requirement (f): confidence scores are in [0, 1] and time window matches."""
    events = [
        NetworkEvent(
            event_id="ev_near",
            timestamp="2026-03-10T12:00:00Z",
            src_ip="198.51.100.1",
            dst_ip="83.136.255.40",
            src_port=50000,
            dst_port=8333,
            protocol="TCP",
            packet_size=300,
            src_geo_country="US",
            src_asn="AS15169",
            dst_geo_country="DE",
            dst_asn="AS24940"
        ),
        NetworkEvent(
            event_id="ev_far",
            timestamp="2026-03-10T12:10:00Z",  # 10 minutes later (far outside 30s)
            src_ip="198.51.100.1",
            dst_ip="83.136.255.40",
            src_port=50001,
            dst_port=8333,
            protocol="TCP",
            packet_size=300,
            src_geo_country="US",
            src_asn="AS15169",
            dst_geo_country="DE",
            dst_asn="AS24940"
        )
    ]
    txns = [
        BlockchainTxn(
            txid="tx_target",
            timestamp="2026-03-10T12:00:08Z",  # 8s difference from ev_near
            input_addresses=["addr_in_1"],
            output_addresses=["addr_out_1"],
            input_amounts=[1.0],
            output_amounts=[0.999],
            fee=0.001,
            script_type="P2PKH"
        )
    ]

    edges = correlate_network_and_blockchain(events, txns, time_window_seconds=30.0)

    # ev_near should correlate, ev_far should NOT
    correlated_event_ids = [e.network_event_id for e in edges]
    assert "ev_near" in correlated_event_ids
    assert "ev_far" not in correlated_event_ids

    # Assert confidence strictly bounded in [0.0, 1.0]
    for edge in edges:
        assert 0.0 <= edge.confidence <= 1.0
        assert edge.txid == "tx_target"


def test_ip_reuse_detection():
    """Test IP reuse detection when same IP is involved with multiple transactions."""
    events = [
        NetworkEvent(
            event_id=f"ev_ip_{i}",
            timestamp=f"2026-03-10T12:00:0{i}Z",
            src_ip="198.51.100.99",
            dst_ip="83.136.255.40",
            src_port=50000 + i,
            dst_port=8333,
            protocol="TCP",
            packet_size=400,
            src_geo_country="US",
            src_asn="AS15169",
            dst_geo_country="DE",
            dst_asn="AS24940"
        )
        for i in range(4)
    ]
    txns = [
        BlockchainTxn(
            txid=f"tx_ip_{i}",
            timestamp=f"2026-03-10T12:00:0{i+1}Z",
            input_addresses=[f"addr_{i}"],
            output_addresses=[f"out_{i}"],
            input_amounts=[1.0],
            output_amounts=[0.99],
            fee=0.01,
            script_type="P2PKH"
        )
        for i in range(3)
    ]

    edges = correlate_network_and_blockchain(events, txns, time_window_seconds=30.0)
    assert len(edges) >= 3
    # Same IP 198.51.100.99 broadcast transactions for addr_0, addr_1, addr_2 -> ip_reuse must be flagged
    corr_types = [e.correlation_type for e in edges]
    assert "ip_reuse" in corr_types


def test_ip_reuse_not_flagged_for_single_wallet():
    """Verify that an IP repeatedly broadcasting for the SAME single wallet is not mislabeled as multi-wallet reuse."""
    events = [
        NetworkEvent(
            event_id=f"ev_single_{i}",
            timestamp=f"2026-03-10T12:00:0{i*5}Z",
            src_ip="198.51.100.50",
            dst_ip="83.136.255.40",
            src_port=50100 + i,
            dst_port=8333,
            protocol="TCP",
            packet_size=400,
            src_geo_country="US",
            src_asn="AS15169",
            dst_geo_country="DE",
            dst_asn="AS24940"
        )
        for i in range(3)
    ]
    # All transactions belong to the same wallet: addr_single_user
    txns = [
        BlockchainTxn(
            txid=f"tx_single_{i}",
            timestamp=f"2026-03-10T12:00:0{i*5 + 1}Z",
            input_addresses=["addr_single_user"],
            output_addresses=["addr_merchant"],
            input_amounts=[1.0],
            output_amounts=[0.99],
            fee=0.01,
            script_type="P2PKH"
        )
        for i in range(3)
    ]

    edges = correlate_network_and_blockchain(events, txns, time_window_seconds=10.0)
    # Because only one wallet is associated with this IP, it must not be labeled as ip_reuse
    corr_types = [e.correlation_type for e in edges]
    assert "ip_reuse" not in corr_types
