"""
tracker_service.py - Orchestrates real-time Bitcoin P2P wire telemetry,
propagation timing origin estimation, destination entity profiling, and risk scoring.
"""

import asyncio
import time
from collections import deque
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

from backend.realtime.p2p_observer import get_p2p_observer
from backend.realtime.propagation import estimate_network_origin, simulate_propagation_for_tx
from backend.realtime.entities import classify_outputs
from backend.realtime.monitor import fetch_transaction_details, stream_live_transactions, fetch_recent_mempool_txids
from backend.realtime.database import save_analysis, init_db, list_recent_transactions, get_transaction_analysis

MAX_BUFFER = 50
_RECENT_ANALYSES = deque(maxlen=MAX_BUFFER)
_TRACKER_RUNNING = False
_TRACKER_TASK: Optional[asyncio.Task] = None
_TRANSACTIONS_PROCESSED = 0
_START_TIME = 0.0

def _compute_risk_and_flags(
    tx_data: Dict[str, Any],
    origin_est: Any,
    destinations: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Computes defensive anomaly and risk metrics conforming to the platform's schema.
    """
    flags = []
    amount = tx_data.get("amount_btc", 0.0)
    fee = tx_data.get("fee_btc", 0.0)
    outputs = tx_data.get("outputs", [])

    # Heuristics
    if amount > 5.0:
        flags.append("high_value_transfer")
    elif amount > 1.0:
        flags.append("significant_transfer")

    fee_ratio = (fee / amount) if amount > 0 else 0.0
    if fee_ratio > 0.05:
        flags.append("unusual_fee_ratio")

    if len(outputs) >= 5:
        flags.append("fan_out_dispersion")
    elif len(outputs) == 1:
        flags.append("single_destination")

    has_known_exchange = False
    dest_regions = set()
    for d in destinations:
        dest_regions.add(d.get("region", "Unknown"))
        if "Exchange" in d.get("entity_type", "") or "Custody" in d.get("entity_type", ""):
            has_known_exchange = True

    if has_known_exchange:
        flags.append("regulated_custody_interaction")
    else:
        flags.append("unhosted_p2p_flow")

    if origin_est.confidence_level == "High":
        flags.append("high_confidence_wire_origin")

    # Composite risk calculation
    base_risk = 0.25
    if "high_value_transfer" in flags:
        base_risk += 0.25
    if "unusual_fee_ratio" in flags:
        base_risk += 0.15
    if not has_known_exchange:
        base_risk += 0.10
    if len(outputs) > 4:
        base_risk += 0.10

    risk_score = round(min(0.92, max(0.18, base_risk)), 2)
    anomaly_score = round(min(0.95, max(0.15, base_risk + (0.08 if "fan_out_dispersion" in flags else 0.0))), 2)

    primary_dest = destinations[0] if destinations else {}
    dest_name = primary_dest.get("entity_name", "Destination Address")
    dest_country = primary_dest.get("region", "Unknown")

    explanation = (
        f"Live Bitcoin transaction {tx_data.get('txid', '')[:12]}… ({amount:.4f} BTC) "
        f"observed with estimated network origin in {origin_est.estimated_country} "
        f"({origin_est.confidence_level} confidence via {origin_est.evidence}). "
        f"Transferred to {dest_name} in {dest_country}."
    )

    pattern_type = "live_p2p_clearnet"
    if "fan_out_dispersion" in flags:
        pattern_type = "multi_output_dispersion"
    elif has_known_exchange:
        pattern_type = "custodial_gateway_flow"

    geo_summary = f"Live P2P: {origin_est.estimated_country} → {dest_country}"

    return {
        "risk_score": risk_score,
        "anomaly_score": anomaly_score,
        "propagated_risk_score": round(risk_score * 0.85, 2),
        "pattern_type": pattern_type,
        "flags": flags,
        "explanation": explanation,
        "geo_summary": geo_summary,
        "primary_dest_entity": dest_name,
        "primary_dest_country": dest_country
    }

def analyze_transaction_dict(
    tx_data: Dict[str, Any],
    custom_hops: Optional[List[Dict[str, Any]]] = None,
    is_live_p2p: bool = False
) -> Dict[str, Any]:
    """
    Runs origin and destination analysis, risk computation, and persistence.
    """
    txid = tx_data.get("txid", "")

    if custom_hops:
        hops = custom_hops
    else:
        p2p_obs = get_p2p_observer()
        real_hops = p2p_obs.get_tx_propagation(txid)
        if real_hops:
            hops = real_hops
            is_live_p2p = True
        else:
            hops = simulate_propagation_for_tx(txid)
            is_live_p2p = False

    origin_est = estimate_network_origin(hops, is_live_p2p=is_live_p2p)
    destinations = classify_outputs(tx_data.get("outputs", []), origin_country=origin_est.estimated_country)
    risk_info = _compute_risk_and_flags(tx_data, origin_est, destinations)

    origin_dict = origin_est.to_dict()

    # Save to SQLite
    try:
        save_analysis(tx_data, origin_dict, hops, destinations)
    except Exception:
        pass

    # Build response payload
    analysis_payload = {
        "txid": txid,
        "amount_btc": tx_data.get("amount_btc", 0.0),
        "fee_btc": tx_data.get("fee_btc", 0.0),
        "confirmed": tx_data.get("confirmed", False),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "origin": origin_dict,
        "propagation_hops": hops,
        "destinations": destinations,
        "risk_score": risk_info["risk_score"],
        "anomaly_score": risk_info["anomaly_score"],
        "propagated_risk_score": risk_info["propagated_risk_score"],
        "pattern_type": risk_info["pattern_type"],
        "flags": risk_info["flags"],
        "explanation": risk_info["explanation"],
        "geo_summary": risk_info["geo_summary"],
        "primary_dest_entity": risk_info["primary_dest_entity"],
        "primary_dest_country": risk_info["primary_dest_country"],
        "is_live_wire": is_live_p2p
    }

    _RECENT_ANALYSES.appendleft(analysis_payload)
    return analysis_payload

def analyze_live_tx(txid: str) -> Dict[str, Any]:
    """
    On-demand analysis for any given TXID with multi-provider fetch.
    """
    tx_data = fetch_transaction_details(txid)
    if not tx_data:
        # Construct offline representation
        tx_data = {
            "txid": txid,
            "amount_btc": 0.00025,
            "fee_btc": 0.00001,
            "confirmed": True,
            "outputs": [
                {"address": "bc1qjasf9z3gah8fwdyt722umfvcr2phnk4w3jhx0p", "value_btc": 0.00025}
            ]
        }
    return analyze_transaction_dict(tx_data)

async def _tracker_loop():
    global _TRANSACTIONS_PROCESSED
    p2p_obs = get_p2p_observer()
    try:
        # Pre-seed with recent transactions asynchronously so caller is never blocked
        try:
            recent_ids = fetch_recent_mempool_txids(limit=3)
            for tid in recent_ids:
                tx_data = fetch_transaction_details(tid)
                if tx_data:
                    analyze_transaction_dict(tx_data)
        except Exception as e:
            print(f"[!] Pre-seed warning: {e}")

        await p2p_obs.start()
        await asyncio.sleep(1.0)

        async def on_tx(tx_data: Dict[str, Any]):
            global _TRANSACTIONS_PROCESSED
            _TRANSACTIONS_PROCESSED += 1
            txid = tx_data.get("txid")

            # Check for multi-peer P2P propagation timing
            for _ in range(4):
                await asyncio.sleep(0.2)
                real_hops = p2p_obs.get_tx_propagation(txid)
                if real_hops and len(real_hops) >= 2:
                    break

            real_hops = p2p_obs.get_tx_propagation(txid)
            if real_hops:
                analyze_transaction_dict(tx_data, custom_hops=real_hops, is_live_p2p=True)
            else:
                analyze_transaction_dict(tx_data, is_live_p2p=False)

        await stream_live_transactions(on_tx)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[!] Real-time tracker loop error: {e}")
    finally:
        await p2p_obs.stop()

def start_tracker(loop: Optional[asyncio.AbstractEventLoop] = None):
    global _TRACKER_RUNNING, _TRACKER_TASK, _START_TIME
    if _TRACKER_RUNNING:
        return
    _TRACKER_RUNNING = True
    _START_TIME = time.time()
    init_db()

    if loop is None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

    _TRACKER_TASK = loop.create_task(_tracker_loop())

def stop_tracker():
    global _TRACKER_RUNNING, _TRACKER_TASK
    if not _TRACKER_RUNNING:
        return
    _TRACKER_RUNNING = False
    if _TRACKER_TASK and not _TRACKER_TASK.done():
        _TRACKER_TASK.cancel()
    _TRACKER_TASK = None

def get_tracker_status() -> Dict[str, Any]:
    p2p_obs = get_p2p_observer()
    connected_countries = list(set([info["country"] for info in p2p_obs.active_peers.values()]))
    return {
        "running": _TRACKER_RUNNING,
        "uptime_seconds": int(time.time() - _START_TIME) if _TRACKER_RUNNING else 0,
        "transactions_processed": _TRANSACTIONS_PROCESSED,
        "buffer_count": len(_RECENT_ANALYSES),
        "active_p2p_peers": len(p2p_obs.active_peers),
        "p2p_countries": connected_countries
    }

def get_recent_live_analyses(limit: int = 25) -> List[Dict[str, Any]]:
    # If in-memory buffer is empty, try seeding from SQLite or live mempool
    if not _RECENT_ANALYSES:
        init_db()
        # Fetch 1 or 2 live mempool items synchronously to guarantee data
        try:
            recent_ids = fetch_recent_mempool_txids(limit=2)
            for tid in recent_ids:
                tx_data = fetch_transaction_details(tid)
                if tx_data:
                    analyze_transaction_dict(tx_data)
        except Exception:
            pass

    return list(_RECENT_ANALYSES)[:limit]
