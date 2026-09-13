import pytest
from sih26146.shared.schemas.records import BlockchainTxn
from sih26146.correlation.graph_builder import build_graph
from sih26146.correlation.risk_propagation import propagate_risk


def test_risk_propagation_decay_across_hops():
    """
    Test requirement (d):
    A wallet directly connected (1-hop) to a seed illicit wallet gets meaningfully higher
    propagated_risk_score than one 4+ hops away. Assert that mathematical decay actually occurs.
    """
    # Create linear chain: Seed -> Hop1 -> Hop2 -> Hop3 -> Hop4 -> Hop5
    txns = []
    addrs = [f"addr_hop_{i}" for i in range(6)]
    seed_wallet = addrs[0]

    for i in range(5):
        txns.append(
            BlockchainTxn(
                txid=f"tx_chain_{i}",
                timestamp=f"2026-03-10T12:0{i}:00Z",
                input_addresses=[addrs[i]],
                output_addresses=[addrs[i+1]],
                input_amounts=[1.0],
                output_amounts=[0.999],
                fee=0.001,
                script_type="P2PKH"
            )
        )

    G = build_graph([], txns)
    labels = {"seed_illicit_wallets": [seed_wallet]}

    risk_scores = propagate_risk(G, labels, method="hybrid")

    # Seed wallet must have risk 1.0
    assert risk_scores[seed_wallet] == 1.0

    # 1-hop neighbor (addr_hop_1) must have high risk
    score_hop_1 = risk_scores["addr_hop_1"]
    assert score_hop_1 >= 0.40

    # 4-hop and 5-hop neighbors must show significant decay
    score_hop_4 = risk_scores["addr_hop_4"]
    score_hop_5 = risk_scores["addr_hop_5"]

    # Assert decay monotonically holds
    assert score_hop_1 > score_hop_4, f"Hop 1 ({score_hop_1}) should be strictly > Hop 4 ({score_hop_4})"
    assert score_hop_4 >= score_hop_5

    # Check bounds [0.0, 1.0]
    for w, r in risk_scores.items():
        assert 0.0 <= r <= 1.0
