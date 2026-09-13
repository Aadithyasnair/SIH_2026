"""
Alert Generator Script for SIH26146 Explainability Layer (Module D).

Purpose:
Consumes upstream outputs (or schema-compliant data) from Module B (correlation/clustering/patterns/propagation)
and Module C (AI/ML detection), applies SHAP/feature importance explanation, risk ranking, plain-language reasoning,
and geo summary generation, producing the final ranked `alerts.json`.
"""

import os
import sys
import json
import uuid
import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add repository root to Python path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from shared.schemas.records import Alert
except ImportError:
    from sih26146.shared.schemas.records import Alert

try:
    from explainability.risk_ranker import calculate_risk_score, rank_alerts
    from explainability.reason_generator import generate_explanation
    from explainability.geo_summary_generator import generate_geo_summary
    from explainability.shap_explainer import get_top_contributors
except ImportError:
    from sih26146.explainability.risk_ranker import calculate_risk_score, rank_alerts
    from sih26146.explainability.reason_generator import generate_explanation
    from sih26146.explainability.geo_summary_generator import generate_geo_summary
    from sih26146.explainability.shap_explainer import get_top_contributors


def process_upstream_data_to_alerts(
    input_records: List[Dict[str, Any]],
    model_path: str = "ml_detection/models/isolation_forest.joblib",
) -> List[Dict[str, Any]]:
    """
    Transforms upstream records into final ranked, explainable Alert records.
    """
    alerts = []
    
    for rec in input_records:
        txid = rec.get("txid", "unknown_txid")
        involved_addresses = rec.get("involved_addresses", rec.get("input_addresses", []) + rec.get("output_addresses", []))
        anomaly_score = float(rec.get("anomaly_score", 0.5))
        propagated_risk = float(rec.get("propagated_risk_score", 0.0))
        correlation_conf = float(rec.get("correlation_confidence", 0.8))
        cluster_risk = float(rec.get("cluster_risk_signal", 0.0))
        pattern_type = rec.get("pattern_type")
        cluster_id = rec.get("cluster_id")
        flags = rec.get("flags", [])
        timestamp = rec.get("timestamp", datetime.datetime.now(datetime.timezone.utc).isoformat())
        
        # Calculate final risk score
        risk_score = calculate_risk_score(
            anomaly_score=anomaly_score,
            propagated_risk_score=propagated_risk,
            correlation_confidence=correlation_conf,
            cluster_risk_signal=cluster_risk,
            pattern_type=pattern_type,
            flags=flags,
        )
        
        # Extract top feature contributors
        feature_dict = rec.get("features", {})
        top_features = []
        if feature_dict:
            top_features = get_top_contributors(feature_dict=feature_dict, model_path=model_path, top_n=3)

        # Build plain language explanation
        alert_ctx = {
            "pattern_type": pattern_type,
            "propagated_risk_score": propagated_risk,
            "hop_count": rec.get("hop_count", 5),
            "wallet_count": rec.get("wallet_count", 10),
            "hop_distance": rec.get("hop_distance", 2),
            "flags": flags,
            "risk_score": risk_score,
            "anomaly_score": anomaly_score,
        }
        explanation = generate_explanation(alert_ctx, top_features=top_features)

        # Build geographic summary
        countries = rec.get("countries", [])
        events = rec.get("network_events", [])
        time_window = rec.get("time_window_minutes", 40.0)
        geo_summary = generate_geo_summary(countries=countries, events=events, time_window_minutes=time_window)

        # Instantiate Pydantic model for strict validation
        alert_obj = Alert(
            alert_id=rec.get("alert_id", str(uuid.uuid4())),
            txid=txid,
            involved_addresses=involved_addresses,
            risk_score=risk_score,
            anomaly_score=anomaly_score,
            propagated_risk_score=propagated_risk,
            pattern_type=pattern_type,
            cluster_id=cluster_id,
            flags=flags,
            explanation=explanation,
            timestamp=timestamp,
            geo_summary=geo_summary,
        )
        
        alerts.append(alert_obj.model_dump())

    # Rank alerts descending by risk_score
    ranked_alerts = sorted(alerts, key=lambda x: x["risk_score"], reverse=True)
    return ranked_alerts


def generate_alerts_json(
    input_file: str = "shared/sample_data/anomaly_scores.json",
    output_file: str = "alerts.json",
):
    """
    Reads upstream input json and produces ranked alerts.json.
    """
    records = []
    if os.path.exists(input_file):
        with open(input_file, "r", encoding="utf-8") as f:
            records = json.load(f)
    else:
        # Generate sample representative upstream records if file doesn't exist yet
        records = [
            {
                "alert_id": "952d7d55-a8d4-48bf-b9d4-463d9e03c067",
                "txid": "b6f123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
                "involved_addresses": ["1PeelAddr1xxxx", "1PeelAddr2xxxx"],
                "anomaly_score": 0.88,
                "propagated_risk_score": 0.75,
                "correlation_confidence": 0.92,
                "cluster_risk_signal": 0.80,
                "pattern_type": "peeling_chain",
                "cluster_id": "cluster-peel-01",
                "flags": ["peeling_chain_detected", "suspicious_layering"],
                "timestamp": "2026-09-14T00:00:00Z",
                "hop_count": 5,
                "countries": ["Germany", "Netherlands", "United States"],
                "time_window_minutes": 40.0,
                "features": {"amount_zscore": 3.4, "txn_frequency": 12.0, "geo_diversity": 3.0},
            },
            {
                "alert_id": "7f88938c-6c46-414e-9ca8-cddc786d9a82",
                "txid": "c7f987654321fedcba987654321fedcba987654321fedcba987654321fedcba",
                "involved_addresses": ["1MixerIn1xxxx", "1MixerIn2xxxx", "1MixerOut1xxxx"],
                "anomaly_score": 0.92,
                "propagated_risk_score": 0.30,
                "correlation_confidence": 0.85,
                "cluster_risk_signal": 0.90,
                "pattern_type": "coinjoin_mixing",
                "cluster_id": "cluster-mix-04",
                "flags": ["coinjoin_mixing_detected", "equal_amount_distribution"],
                "timestamp": "2026-09-14T00:05:00Z",
                "wallet_count": 12,
                "countries": ["Panama", "Switzerland"],
                "time_window_minutes": 15.0,
                "features": {"small_remainder_ratio": 0.95, "degree_centrality": 0.82},
            },
            {
                "alert_id": "84207cf3-8e6a-43c9-8a53-d6579762d469",
                "txid": "d8a112233445566778899aabbccddeeff112233445566778899aabbccddeeff",
                "involved_addresses": ["1Hop2RiskAddrxxxx"],
                "anomaly_score": 0.65,
                "propagated_risk_score": 0.82,
                "correlation_confidence": 0.78,
                "cluster_risk_signal": 0.60,
                "pattern_type": "none",
                "cluster_id": "cluster-hop-09",
                "flags": ["propagated_illicit_link"],
                "timestamp": "2026-09-14T00:10:00Z",
                "hop_distance": 2,
                "source_label": "a ransomware seed wallet",
                "countries": ["Russian Federation", "Cyprus"],
                "time_window_minutes": 25.0,
                "features": {"propagated_risk": 0.82, "burst_count": 5.0},
            },
            {
                "alert_id": "2204ca4f-507f-481b-a80b-fbb98d84875d",
                "txid": "e9b2233445566778899aabbccddeeff00112233445566778899aabbccddeeff",
                "involved_addresses": ["1HighValAddrxxxx"],
                "anomaly_score": 0.79,
                "propagated_risk_score": 0.15,
                "correlation_confidence": 0.90,
                "cluster_risk_signal": 0.30,
                "pattern_type": "none",
                "cluster_id": None,
                "flags": ["high_value_burst"],
                "timestamp": "2026-09-14T00:15:00Z",
                "countries": ["Germany"],
                "time_window_minutes": 5.0,
                "features": {"amount_zscore": 4.1, "txn_frequency": 15.0},
            },
            {
                "alert_id": "137bcce6-4874-4355-aa7e-7671a5aebfe9",
                "txid": "f0c33445566778899aabbccddeeff00112233445566778899aabbccddeeff11",
                "involved_addresses": ["1NormalUserAddrxxxx"],
                "anomaly_score": 0.12,
                "propagated_risk_score": 0.05,
                "correlation_confidence": 0.95,
                "cluster_risk_signal": 0.0,
                "pattern_type": "none",
                "cluster_id": None,
                "flags": [],
                "timestamp": "2026-09-14T00:20:00Z",
                "countries": ["United States"],
                "time_window_minutes": 2.0,
                "features": {"amount_zscore": 0.1},
            },
        ]

    alerts = process_upstream_data_to_alerts(records)
    
    # Save alerts.json at root, explainability/, and shared/sample_data/
    root_output = Path(output_file)
    explainability_output = Path("explainability/alerts.json")
    sample_output = Path("shared/sample_data/alerts.json")
    
    with open(root_output, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    os.makedirs("explainability", exist_ok=True)
    with open(explainability_output, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    os.makedirs("shared/sample_data", exist_ok=True)
    with open(sample_output, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)
        
    print(f"Successfully generated {len(alerts)} alerts into {root_output}, {explainability_output}, and {sample_output}")
    return alerts

if __name__ == "__main__":
    generate_alerts_json()
