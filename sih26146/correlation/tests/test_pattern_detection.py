import pytest
from sih26146.shared.schemas.records import BlockchainTxn
from sih26146.correlation.graph_builder import build_graph
from sih26146.correlation.pattern_detection import detect_patterns


def test_peeling_chain_detection():
    """Test peeling chain detection on a 4-hop chain and ensure normal txns don't false positive."""
    # Build 4-hop peeling chain
    peel_txns = []
    current_val = 10.0
    for hop in range(4):
        fwd_val = current_val - 0.5 - 0.001
        peel_txns.append(
            BlockchainTxn(
                txid=f"tx_peel_{hop}",
                timestamp=f"2026-03-10T12:0{hop}:00Z",
                input_addresses=[f"addr_peel_fwd_{hop}"],
                output_addresses=[f"addr_peel_fwd_{hop+1}", f"addr_peel_out_{hop}"],
                input_amounts=[current_val],
                output_amounts=[fwd_val, 0.5],
                fee=0.001,
                script_type="P2PKH"
            )
        )
        current_val = fwd_val

    # Add a completely normal 1-in, 1-out transaction
    normal_tx = BlockchainTxn(
        txid="tx_normal_payment",
        timestamp="2026-03-10T13:00:00Z",
        input_addresses=["addr_alice"],
        output_addresses=["addr_bob"],
        input_amounts=[0.5],
        output_amounts=[0.499],
        fee=0.001,
        script_type="P2WPKH"
    )

    all_txns = peel_txns + [normal_tx]
    G = build_graph([], all_txns)
    patterns = detect_patterns(G, all_txns)

    # All peel hops should be flagged as peeling_chain
    for hop in range(4):
        res = patterns[f"tx_peel_{hop}"]
        assert res.pattern_type == "peeling_chain"
        assert any("peeling_chain" in f for f in res.flags)
        assert res.confidence >= 0.70

    # Normal transaction must NOT be flagged (no false positive)
    norm_res = patterns["tx_normal_payment"]
    assert norm_res.pattern_type == "none"
    assert len(norm_res.flags) == 0


def test_coinjoin_mixing_detection():
    """Test CoinJoin / mixing detection on equal-denomination multi-party transaction."""
    cj_tx = BlockchainTxn(
        txid="tx_coinjoin_5_party",
        timestamp="2026-03-10T14:00:00Z",
        input_addresses=[f"addr_cj_in_{i}" for i in range(5)],
        output_addresses=[f"addr_cj_out_{i}" for i in range(5)],
        input_amounts=[0.1, 0.1, 0.1, 0.1, 0.1],
        output_amounts=[0.0999, 0.0999, 0.0999, 0.0999, 0.0999],
        fee=0.0005,
        script_type="P2WPKH"
    )

    G = build_graph([], [cj_tx])
    patterns = detect_patterns(G, [cj_tx])

    res = patterns["tx_coinjoin_5_party"]
    assert res.pattern_type == "coinjoin_mixing"
    assert any("coinjoin" in f for f in res.flags)
    assert res.confidence >= 0.70


def test_coinjoin_rejects_unequal_inputs_with_equal_outputs():
    """Verify that transactions with unequal inputs but equal outputs are NOT flagged as CoinJoin."""
    unequal_in_tx = BlockchainTxn(
        txid="tx_unequal_inputs",
        timestamp="2026-03-10T14:15:00Z",
        input_addresses=["addr_in_1", "addr_in_2", "addr_in_3", "addr_in_4"],
        output_addresses=["addr_out_1", "addr_out_2", "addr_out_3", "addr_out_4"],
        input_amounts=[5.0, 0.1, 0.2, 0.05],  # Highly unequal inputs
        output_amounts=[1.3, 1.3, 1.3, 1.3],   # Equal outputs
        fee=0.001,
        script_type="P2WPKH"
    )

    G = build_graph([], [unequal_in_tx])
    patterns = detect_patterns(G, [unequal_in_tx])
    assert patterns["tx_unequal_inputs"].pattern_type == "none"


def test_peeling_chain_enforces_chronological_order():
    """Verify that an out-of-order or reverse-timestamp transaction is not chained as a later hop."""
    # Hop 0: at 12:10:00
    tx_0 = BlockchainTxn(
        txid="tx_hop_0",
        timestamp="2026-03-10T12:10:00Z",
        input_addresses=["addr_fwd_0"],
        output_addresses=["addr_fwd_1", "addr_peel_0"],
        input_amounts=[10.0],
        output_amounts=[9.5, 0.5],
        fee=0.001,
        script_type="P2PKH"
    )
    # Hop 1: earlier timestamp 12:00:00 (occurred BEFORE hop 0!)
    tx_1_past = BlockchainTxn(
        txid="tx_hop_1_past",
        timestamp="2026-03-10T12:00:00Z",
        input_addresses=["addr_fwd_1"],
        output_addresses=["addr_fwd_2", "addr_peel_1"],
        input_amounts=[9.5],
        output_amounts=[9.0, 0.5],
        fee=0.001,
        script_type="P2PKH"
    )

    all_txs = [tx_0, tx_1_past]
    G = build_graph([], all_txs)
    patterns = detect_patterns(G, all_txs)

    # Neither should form a >=3 hop peeling chain
    assert patterns["tx_hop_0"].pattern_type == "none"
    assert patterns["tx_hop_1_past"].pattern_type == "none"
