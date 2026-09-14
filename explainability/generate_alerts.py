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
    in_path = REPO_ROOT / input_file if not Path(input_file).is_absolute() else Path(input_file)
    if not in_path.exists():
        raise FileNotFoundError(f"Required upstream file {in_path} not found. Please run ML pipeline first.")

    with open(in_path, "r", encoding="utf-8") as f:
        records = json.load(f)
    print(f"Loaded {len(records)} real upstream records from {in_path}")

    alerts = process_upstream_data_to_alerts(records)
    
    # Save alerts.json at root, explainability/, and shared/sample_data/
    root_output = REPO_ROOT / output_file if not Path(output_file).is_absolute() else Path(output_file)
    explainability_output = REPO_ROOT / "explainability" / "alerts.json"
    sample_output = REPO_ROOT / "shared" / "sample_data" / "alerts.json"
    
    with open(root_output, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    os.makedirs(explainability_output.parent, exist_ok=True)
    with open(explainability_output, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)

    os.makedirs(sample_output.parent, exist_ok=True)
    with open(sample_output, "w", encoding="utf-8") as f:
        json.dump(alerts, f, indent=2)
        
    print(f"Successfully generated {len(alerts)} alerts into {root_output}, {explainability_output}, and {sample_output}")
    return alerts

if __name__ == "__main__":
    generate_alerts_json()
