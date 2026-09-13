"""
Correlation Rules & Engine for SIH26146
Correlates network-layer events (IP/port/timing) with blockchain-layer transactions.

Confidence Scoring Formula:
---------------------------
confidence = (w_time * time_score) + (w_reuse * reuse_score) + (w_session * session_score)
Where:
- w_time = 0.50 (Time proximity weight)
- w_reuse = 0.30 (IP/Wallet co-occurrence / reuse weight)
- w_session = 0.20 (Session burst / activity continuity weight)

Detailed Component Scores:
1. time_score:
   delta_t = abs(event_time - txn_time) in seconds.
   If delta_t <= time_window_seconds:
       time_score = max(0.0, 1.0 - (delta_t / time_window_seconds))
   Else: 0.0

2. reuse_score:
   Fraction of times this IP has been observed participating in transactions
   co-occurring with this wallet / address set, normalized across IP observations:
       reuse_score = min(1.0, 0.4 + 0.2 * prior_occurrences)

3. session_score:
   1.0 if event belongs to an active network session (consecutive packets from src_ip
   with inter-arrival gap < session_gap_seconds, default 300s / 5 min), else 0.5.

All final confidence scores are strictly clamped to the range [0.0, 1.0].
"""
import uuid
from datetime import datetime, timezone
from collections import defaultdict
from typing import List, Dict, Set, Union, Any, Tuple

from sih26146.shared.schemas.records import NetworkEvent, BlockchainTxn, CorrelationEdge


def parse_iso8601(ts: str) -> datetime:
    """Parses ISO8601 string to UTC datetime object."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def cluster_network_sessions(
    events: List[NetworkEvent],
    session_gap_seconds: float = 300.0
) -> Dict[str, str]:
    """
    Groups network events by src_ip where gap between consecutive events is < session_gap_seconds.
    Returns mapping from event_id -> session_id.
    """
    events_by_ip = defaultdict(list)
    for ev in events:
        events_by_ip[ev.src_ip].append(ev)

    event_to_session = {}
    for ip, ev_list in events_by_ip.items():
        # Sort by timestamp
        sorted_evs = sorted(ev_list, key=lambda x: parse_iso8601(x.timestamp))
        current_session_id = str(uuid.uuid4())
        last_time = None

        for ev in sorted_evs:
            ev_time = parse_iso8601(ev.timestamp)
            if last_time is not None:
                gap = (ev_time - last_time).total_seconds()
                if gap >= session_gap_seconds:
                    current_session_id = str(uuid.uuid4())
            event_to_session[ev.event_id] = current_session_id
            last_time = ev_time

    return event_to_session


def correlate_network_and_blockchain(
    events: List[Union[NetworkEvent, Dict[str, Any]]],
    txns: List[Union[BlockchainTxn, Dict[str, Any]]],
    time_window_seconds: float = 30.0,
    session_gap_seconds: float = 300.0,
    w_time: float = 0.50,
    w_reuse: float = 0.30,
    w_session: float = 0.20,
    min_confidence: float = 0.20
) -> List[CorrelationEdge]:
    """
    Correlates network events with blockchain transactions based on temporal proximity,
    IP-wallet reuse frequency, and session clustering.
    """
    # Standardize records
    typed_events: List[NetworkEvent] = [
        ev if isinstance(ev, NetworkEvent) else NetworkEvent(**ev) for ev in events
    ]
    typed_txns: List[BlockchainTxn] = [
        tx if isinstance(tx, BlockchainTxn) else BlockchainTxn(**tx) for tx in txns
    ]

    # Pre-parse timestamps
    event_times = {ev.event_id: parse_iso8601(ev.timestamp) for ev in typed_events}
    txn_times = {tx.txid: parse_iso8601(tx.timestamp) for tx in typed_txns}

    # Session clustering
    event_to_session = cluster_network_sessions(typed_events, session_gap_seconds)
    session_sizes = defaultdict(int)
    for sess_id in event_to_session.values():
        session_sizes[sess_id] += 1

    # Pass 1: Build real IP-to-wallet co-occurrence and multi-wallet association mapping
    # For every event/transaction pair within the time window, associate src_ip with tx wallet addresses
    ip_wallets: Dict[str, Set[str]] = defaultdict(set)
    ip_wallet_pair_counts: Dict[Tuple[str, str], int] = defaultdict(int)

    for ev in typed_events:
        ev_dt = event_times[ev.event_id]
        for tx in typed_txns:
            tx_dt = txn_times[tx.txid]
            delta = abs((ev_dt - tx_dt).total_seconds())
            if delta <= time_window_seconds:
                for w in tx.input_addresses:
                    ip_wallets[ev.src_ip].add(w)
                    ip_wallet_pair_counts[(ev.src_ip, w)] += 1

    correlation_edges: List[CorrelationEdge] = []

    for ev in typed_events:
        ev_dt = event_times[ev.event_id]
        sess_id = event_to_session.get(ev.event_id)
        is_multi_packet_session = session_sizes[sess_id] > 1

        for tx in typed_txns:
            tx_dt = txn_times[tx.txid]
            delta_t = abs((ev_dt - tx_dt).total_seconds())

            if delta_t <= time_window_seconds:
                # 1. Time proximity score
                time_score = max(0.0, 1.0 - (delta_t / time_window_seconds))

                # 2. Real IP-to-wallet reuse score
                # - Check if this IP is associated with multiple distinct wallets (IP reuse)
                # - Check how frequently this specific (IP, wallet) pair co-occurs
                unique_wallets_for_ip = len(ip_wallets[ev.src_ip])
                max_cooccurrence_freq = max(
                    [ip_wallet_pair_counts.get((ev.src_ip, w), 0) for w in tx.input_addresses],
                    default=0
                )

                # Base score for valid temporal match
                base_reuse = 0.30
                # If the same IP touches multiple distinct wallets across transactions (IP reuse)
                reuse_bonus = 0.35 if unique_wallets_for_ip >= 2 else 0.0
                # If this specific IP-wallet pair co-occurs repeatedly
                cooccurrence_bonus = min(0.35, 0.15 * max(0, max_cooccurrence_freq - 1))
                reuse_score = min(1.0, base_reuse + reuse_bonus + cooccurrence_bonus)

                # 3. Session continuity score
                session_score = 1.0 if is_multi_packet_session else 0.5

                # Combined confidence formula
                raw_confidence = (
                    (w_time * time_score) +
                    (w_reuse * reuse_score) +
                    (w_session * session_score)
                )
                confidence = max(0.0, min(1.0, round(raw_confidence, 4)))

                if confidence >= min_confidence:
                    # Label based on the dominant evidence signal
                    if unique_wallets_for_ip >= 2:
                        corr_type = "ip_reuse"
                    elif delta_t <= 5.0 and is_multi_packet_session:
                        corr_type = "session_burst"
                    else:
                        corr_type = "time_window"

                    edge = CorrelationEdge(
                        edge_id=str(uuid.uuid4()),
                        network_event_id=ev.event_id,
                        txid=tx.txid,
                        confidence=confidence,
                        correlation_type=corr_type
                    )
                    correlation_edges.append(edge)

    return correlation_edges
