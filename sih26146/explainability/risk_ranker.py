"""
Risk Ranker Module for SIH26146 Explainability Layer (Module D).

Purpose:
Computes the final unified `risk_score` in [0, 1] for an investigative alert record by combining
upstream machine learning anomaly detection with graph-based risk propagation, correlation confidence,
cluster risk signals, and pattern boosts.

Formula & Weights:
------------------
The final risk score is computed as a weighted combination of structural and model signals,
followed by an additive pattern boost:

    Base Score = (w_anomaly * anomaly_score)
               + (w_propagation * propagated_risk_score)
               + (w_correlation * correlation_confidence)
               + (w_cluster * cluster_risk_signal)

Where default weights are:
    - w_anomaly      = 0.45  (Primary model anomaly score from Module C)
    - w_propagation  = 0.25  (Graph seed-wallet risk diffusion from Module B)
    - w_correlation  = 0.15  (Network-blockchain co-occurrence confidence from Module B)
    - w_cluster      = 0.15  (Entity cluster average risk score from Module B)

Pattern Boosts:
    - peeling_chain   : +0.15 boost
    - coinjoin_mixing : +0.15 boost
    - Additional flags: +0.05 per suspicious flag (capped at +0.10 total)

Final Risk Score:
    risk_score = min(1.0, max(0.0, Base Score + Pattern Boost))

Key Constraints:
    1. Output is strictly bounded in [0.0, 1.0].
    2. Model anomaly score remains primary (45% weight).
    3. Rules/pattern flags boost the score but never replace the primary ML model score.
"""

from typing import Dict, Any, Optional, List


def calculate_risk_score(
    anomaly_score: float,
    propagated_risk_score: float = 0.0,
    correlation_confidence: float = 0.0,
    cluster_risk_signal: float = 0.0,
    pattern_type: Optional[str] = None,
    flags: Optional[List[str]] = None,
    w_anomaly: float = 0.45,
    w_propagation: float = 0.25,
    w_correlation: float = 0.15,
    w_cluster: float = 0.15,
) -> float:
    """
    Computes the final ranked risk_score in range [0.0, 1.0].

    :param anomaly_score: Primary anomaly score from Module C (0.0 to 1.0)
    :param propagated_risk_score: Risk score propagated from illicit seed wallets (0.0 to 1.0)
    :param correlation_confidence: Confidence of IP-to-wallet correlation (0.0 to 1.0)
    :param cluster_risk_signal: Average risk score of the address cluster (0.0 to 1.0)
    :param pattern_type: Detected laundering pattern ('peeling_chain', 'coinjoin_mixing', or 'none'/None)
    :param flags: Additional diagnostic flags
    :return: Bounded risk score float between 0.0 and 1.0
    """
    # Sanitize and clamp input component scores
    a_score = max(0.0, min(1.0, float(anomaly_score)))
    p_score = max(0.0, min(1.0, float(propagated_risk_score)))
    c_conf = max(0.0, min(1.0, float(correlation_confidence)))
    cl_risk = max(0.0, min(1.0, float(cluster_risk_signal)))

    # Compute base weighted score
    base_score = (
        (w_anomaly * a_score)
        + (w_propagation * p_score)
        + (w_correlation * c_conf)
        + (w_cluster * cl_risk)
    )

    # Compute pattern boost
    pattern_boost = 0.0
    if pattern_type == "peeling_chain":
        pattern_boost += 0.15
    elif pattern_type == "coinjoin_mixing":
        pattern_boost += 0.15

    # Compute additional flag boost
    if flags:
        flag_boost = 0.0
        suspicious_keywords = ["suspicious", "rapid", "darknet", "sanctioned", "high_value", "burst"]
        for f in flags:
            if any(kw in f.lower() for kw in suspicious_keywords):
                flag_boost += 0.05
        pattern_boost += min(0.10, flag_boost)

    raw_risk = base_score + pattern_boost
    final_score = max(0.0, min(1.0, raw_risk))
    
    return round(final_score, 4)


def rank_alerts(alerts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calculates final risk scores for a list of alert dicts or records and sorts them descending by risk_score.
    """
    for alert in alerts:
        risk = calculate_risk_score(
            anomaly_score=alert.get("anomaly_score", 0.0),
            propagated_risk_score=alert.get("propagated_risk_score", 0.0),
            correlation_confidence=alert.get("correlation_confidence", 0.0),
            cluster_risk_signal=alert.get("cluster_risk_signal", 0.0),
            pattern_type=alert.get("pattern_type"),
            flags=alert.get("flags", []),
        )
        alert["risk_score"] = risk

    # Sort descending by risk_score
    return sorted(alerts, key=lambda x: x.get("risk_score", 0.0), reverse=True)
