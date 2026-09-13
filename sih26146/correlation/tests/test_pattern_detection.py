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
