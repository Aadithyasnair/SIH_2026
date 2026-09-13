import pytest
from sih26146.explainability.reason_generator import (
    generate_explanation,
    generate_peeling_chain_explanation,
    generate_coinjoin_explanation,
    generate_propagated_risk_explanation,
    BANNED_JARGON,
)


def test_explanation_non_empty():
    """Verify every generated explanation is non-empty."""
    alert_data = {"risk_score": 0.8, "anomaly_score": 0.75}
    exp = generate_explanation(alert_data)
    assert isinstance(exp, str)
    assert len(exp.strip()) > 0


def test_banned_jargon_check():
    """Assert that raw internal ML jargon terms do not appear in generated explanations."""
    test_cases = [
        {"pattern_type": "peeling_chain", "hop_count": 5},
        {"pattern_type": "coinjoin_mixing", "wallet_count": 12},
        {"propagated_risk_score": 0.8, "hop_distance": 2},
        {"risk_score": 0.85, "anomaly_score": 0.8},
    ]

    top_features = [
        {"feature": "amount_zscore", "value": 3.2, "direction": "increased"},
        {"feature": "degree_centrality", "value": 0.85, "direction": "increased"},
    ]

    for alert in test_cases:
        exp = generate_explanation(alert, top_features=top_features)
        exp_lower = exp.lower()
        for banned in BANNED_JARGON:
            assert banned not in exp_lower, f"Banned jargon term '{banned}' found in explanation: '{exp}'"


def test_peeling_chain_explanation_template():
    """Verify peeling chain explanation contains required semantics."""
    exp = generate_peeling_chain_explanation(hop_count=5)
    assert "chain of 5 wallets" in exp
    assert "layering to obscure the money trail" in exp


def test_coinjoin_explanation_template():
    """Verify CoinJoin/mixing explanation contains required semantics."""
    exp = generate_coinjoin_explanation(wallet_count=10)
    assert "combined funds from 10 different wallets" in exp
    assert "mixing service designed to break the link" in exp


def test_propagated_risk_explanation_template():
    """Verify propagated risk explanation contains required semantics."""
    exp = generate_propagated_risk_explanation(hop_distance=2)
    assert "2 hops away" in exp
    assert "confirmed illicit" in exp
