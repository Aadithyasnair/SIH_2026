import pytest

try:
    from explainability.risk_ranker import calculate_risk_score, rank_alerts
except ImportError:
    from sih26146.explainability.risk_ranker import calculate_risk_score, rank_alerts


def test_risk_score_range():
    """Verify that calculated risk_score is always strictly bounded in [0.0, 1.0]."""
    # Min values
    score_min = calculate_risk_score(
        anomaly_score=0.0,
        propagated_risk_score=0.0,
        correlation_confidence=0.0,
        cluster_risk_signal=0.0,
        pattern_type="none",
    )
    assert 0.0 <= score_min <= 1.0
    assert score_min == 0.0

    # Max values with boosts
    score_max = calculate_risk_score(
        anomaly_score=1.0,
        propagated_risk_score=1.0,
        correlation_confidence=1.0,
        cluster_risk_signal=1.0,
        pattern_type="peeling_chain",
        flags=["suspicious_burst", "darknet_touch"],
    )
    assert 0.0 <= score_max <= 1.0
    assert score_max == 1.0

    # Out-of-bounds input clamping
    score_clamped = calculate_risk_score(
        anomaly_score=2.5,
        propagated_risk_score=10.0,
        correlation_confidence=-1.0,
        cluster_risk_signal=5.0,
    )
    assert 0.0 <= score_clamped <= 1.0


def test_pattern_boost_does_not_replace_model_score():
    """Verify that pattern boosts add to but do not overwrite the model score."""
    base_score = calculate_risk_score(
        anomaly_score=0.4,
        propagated_risk_score=0.2,
        correlation_confidence=0.5,
        cluster_risk_signal=0.1,
        pattern_type=None,
    )

    boosted_score = calculate_risk_score(
        anomaly_score=0.4,
        propagated_risk_score=0.2,
        correlation_confidence=0.5,
        cluster_risk_signal=0.1,
        pattern_type="peeling_chain",
    )

    assert boosted_score > base_score
    assert boosted_score <= 1.0


def test_rank_alerts():
    """Verify that alerts are sorted descending by risk_score."""
    alerts = [
        {"txid": "tx1", "anomaly_score": 0.2},
        {"txid": "tx2", "anomaly_score": 0.9, "pattern_type": "peeling_chain"},
        {"txid": "tx3", "anomaly_score": 0.5},
    ]
    ranked = rank_alerts(alerts)
    assert len(ranked) == 3
    assert ranked[0]["txid"] == "tx2"
    assert ranked[0]["risk_score"] >= ranked[1]["risk_score"]
    assert ranked[1]["risk_score"] >= ranked[2]["risk_score"]
