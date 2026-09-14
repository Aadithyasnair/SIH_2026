"""
Merge Scores Module for SIH26146.
Joins ML anomaly scores from Module C with Module B outputs
(correlation edges, clusters, enriched transactions, network events)
to produce shared/sample_data/anomaly_scores.json for Module D explainability.
"""
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


def merge_pipeline_scores(
    enriched_txns: List[Dict[str, Any]],
    predictions: List[Dict[str, Any]],
    clusters: Optional[List[Dict[str, Any]]] = None,
    correlation_edges: Optional[List[Dict[str, Any]]] = None,
    network_events: Optional[List[Dict[str, Any]]] = None,
    output_path: Optional[Path] = None,
) -> List[Dict[str, Any]]:
    """
    Merges ML anomaly scores and features with Module B signals into the
    canonical schema expected by Module D (explainability/generate_alerts.py).
    """
    pred_by_txid = {p["txid"]: p for p in predictions}

    # Build address-to-cluster lookup
    addr_to_cluster = {}
    if clusters:
        for c in clusters:
            for addr in c.get("member_addresses", []):
                addr_to_cluster[addr] = c

    # Build txid-to-correlation edges lookup
    txid_to_edges = {}
    if correlation_edges:
        for e in correlation_edges:
            txid = e.get("txid")
            if txid:
                txid_to_edges.setdefault(txid, []).append(e)

    # Build event_id lookup
    event_by_id = {}
    if network_events:
        for ev in network_events:
            ev_id = ev.get("event_id")
            if ev_id:
                event_by_id[ev_id] = ev

    merged_records = []
    for tx in enriched_txns:
        txid = tx["txid"]
        pred = pred_by_txid.get(txid, {})
        anomaly_score = float(pred.get("anomaly_score", 0.0))
        features = pred.get("features", {})

        in_addrs = tx.get("input_addresses", [])
        out_addrs = tx.get("output_addresses", [])
        involved = in_addrs + out_addrs

        # Lookup real cluster from Module B
        matched_cluster = None
        for addr in involved:
            if addr in addr_to_cluster:
                matched_cluster = addr_to_cluster[addr]
                break

        cluster_id = matched_cluster.get("cluster_id") if matched_cluster else None
        cluster_risk = float(matched_cluster.get("avg_risk_score", 0.0)) if matched_cluster else 0.0
        member_cnt = int(matched_cluster.get("member_count", len(involved))) if matched_cluster else len(involved)

        # Lookup correlation edges & countries
        edges = txid_to_edges.get(txid, [])
        if edges:
            correlation_conf = max(float(e.get("confidence", 0.5)) for e in edges)
            c_list = []
            for e in edges:
                ev_id = e.get("network_event_id")
                if ev_id in event_by_id:
                    c_list.append(event_by_id[ev_id].get("src_geo_country", "US"))
                    c_list.append(event_by_id[ev_id].get("dst_geo_country", "US"))
            countries = list(dict.fromkeys(c_list)) if c_list else ["US"]
        else:
            correlation_conf = 0.50
            countries = ["US"]

        prop_risk = float(tx.get("propagated_risk_score", 0.0))
        pattern_type = tx.get("pattern_type") or "none"
        flags = list(tx.get("flags", []))

        # Hop and distance metadata for explainability reasoning
        hop_count = 5 if pattern_type == "peeling_chain" else max(1, len(involved))
        hop_dist = 1 if prop_risk >= 0.85 else 2 if prop_risk >= 0.50 else 3 if prop_risk > 0.20 else 4

        record = {
            "txid": txid,
            "involved_addresses": involved,
            "anomaly_score": round(anomaly_score, 4),
            "propagated_risk_score": round(prop_risk, 4),
            "correlation_confidence": round(correlation_conf, 4),
            "cluster_risk_signal": round(cluster_risk, 4),
            "pattern_type": pattern_type,
            "cluster_id": cluster_id,
            "flags": flags,
            "timestamp": tx.get("timestamp", ""),
            "countries": countries,
            "time_window_minutes": 30.0,
            "features": features,
            "hop_count": hop_count,
            "wallet_count": member_cnt,
            "hop_distance": hop_dist,
        }
        merged_records.append(record)

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(merged_records, f, indent=2)

    return merged_records
