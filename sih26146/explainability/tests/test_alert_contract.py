import pytest
import datetime
from sih26146.shared.schemas.records import Alert
from sih26146.explainability.risk_ranker import calculate_risk_score
from sih26146.explainability.reason_generator import generate_explanation
from sih26146.explainability.geo_summary_generator import generate_geo_summary


def test_alert_pydantic_schema_validation():
    """Verify that generated alert records validate against the shared Alert Pydantic model."""
    anomaly_score = 0.85
    propagated_risk = 0.6
    pattern_type = "peeling_chain"
    flags = ["suspicious_layering", "high_value_burst"]
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

    risk_score = calculate_risk_score(
        anomaly_score=anomaly_score,
        propagated_risk_score=propagated_risk,
        correlation_confidence=0.9,
        cluster_risk_signal=0.7,
        pattern_type=pattern_type,
        flags=flags,
    )

    alert_dict = {
        "pattern_type": pattern_type,
        "propagated_risk_score": propagated_risk,
        "hop_count": 5,
        "flags": flags,
        "risk_score": risk_score,
    }

    explanation = generate_explanation(alert_dict)
    geo_summary = generate_geo_summary(countries=["Germany", "Netherlands", "United States"], time_window_minutes=40.0)

    # Build Alert model
    alert_record = Alert(
        txid="0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        involved_addresses=["1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa", "12c6DSiU4Rq3P4ZxziKxzrL5LmMBrzjrJX"],
        risk_score=risk_score,
        anomaly_score=anomaly_score,
        propagated_risk_score=propagated_risk,
        pattern_type=pattern_type,
        cluster_id="cluster-99",
        flags=flags,
        explanation=explanation,
        timestamp=timestamp,
        geo_summary=geo_summary,
    )

    assert alert_record.alert_id is not None
    assert alert_record.risk_score == risk_score
    assert 0.0 <= alert_record.risk_score <= 1.0
    assert alert_record.explanation == explanation
    assert alert_record.geo_summary == geo_summary
    assert alert_record.pattern_type == "peeling_chain"
