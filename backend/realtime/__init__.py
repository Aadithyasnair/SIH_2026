"""
backend.realtime - Live Bitcoin P2P wire telemetry, network propagation origin estimation,
and destination address entity intelligence.
"""
from backend.realtime.geolocation import resolve_ip
from backend.realtime.propagation import estimate_network_origin, simulate_propagation_for_tx
from backend.realtime.entities import identify_address, classify_outputs
from backend.realtime.p2p_observer import get_p2p_observer, P2PObserver
from backend.realtime.monitor import fetch_transaction_details, fetch_recent_mempool_txids, stream_live_transactions

__all__ = [
    "resolve_ip",
    "estimate_network_origin",
    "simulate_propagation_for_tx",
    "identify_address",
    "classify_outputs",
    "get_p2p_observer",
    "P2PObserver",
    "fetch_transaction_details",
    "fetch_recent_mempool_txids",
    "stream_live_transactions",
]
