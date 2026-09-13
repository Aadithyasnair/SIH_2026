import pytest
from shared.schemas.records import BlockchainTxn
from correlation.graph_builder import build_graph
from correlation.risk_propagation import propagate_risk


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


def test_risk_does_not_propagate_to_upstream_funder():
    """
    Test that risk propagates outward along fund transfers, not backward into innocent upstream funders.
    Scenario:
    - InnocentFunder sends funds to SeedIllicitWallet
    - SeedIllicitWallet sends funds to TaintedDestination
    InnocentFunder must NOT receive propagated risk.
    """
    txns = [
        BlockchainTxn(
            txid="tx_fund_seed",
            timestamp="2026-03-10T12:00:00Z",
            input_addresses=["addr_innocent_funder"],
            output_addresses=["addr_seed_illicit"],
            input_amounts=[5.0],
            output_amounts=[4.999],
            fee=0.001,
            script_type="P2PKH"
        ),
        BlockchainTxn(
            txid="tx_seed_spends",
            timestamp="2026-03-10T12:05:00Z",
            input_addresses=["addr_seed_illicit"],
            output_addresses=["addr_tainted_dest"],
            input_amounts=[4.999],
            output_amounts=[4.998],
            fee=0.001,
            script_type="P2PKH"
        )
    ]

    G = build_graph([], txns)
    labels = {"seed_illicit_wallets": ["addr_seed_illicit"]}

    risk_scores = propagate_risk(G, labels, method="hop_decay")

    assert risk_scores["addr_seed_illicit"] == 1.0
    assert risk_scores["addr_tainted_dest"] >= 0.50
    # Innocent upstream funder must remain at 0.0 (no backward propagation)
    assert risk_scores["addr_innocent_funder"] == 0.0
