"""
Feature Engineering for Module C (AI/ML Detection).
Extracts transaction, wallet-relative, temporal, graph, cluster, geo,
and pattern features from transaction and pipeline data.

Strictly unsupervised: NO ground-truth labels are ever accessed or used here.
"""
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple, Set
import numpy as np
import pandas as pd
import networkx as nx


# Fixed numeric mapping for pattern types detected by Module B
PATTERN_TYPE_MAP = {
    "none": 0.0,
    "coinjoin_mixing": 1.0,
    "peeling_chain": 2.0,
}

SCRIPT_TYPE_MAP = {
    "P2PKH": 1.0,
    "P2SH": 2.0,
    "P2WPKH": 3.0,
    "P2TR": 4.0,
    "other": 0.0,
}

FEATURE_COLUMNS = [
    # 1. Amount & Value distribution features
    "total_input_btc",
    "total_output_btc",
    "fee_btc",
    "fee_ratio",
    "output_amount_mean",
    "output_amount_std",
    "output_amount_cv",
    "input_count",
    "output_count",
    "output_to_input_ratio",
    "max_output_fraction",
    "amount_deviation_from_wallet_mean",
    # 2. Temporal & Frequency features
    "hour_of_day",
    "is_night_hour",
    "tx_burst_1h_count",
    # 3. Graph topological features
    "max_addr_degree",
    "mean_addr_degree",
    "max_addr_betweenness",
    # 4. Cluster signals
    "in_cluster",
    "cluster_avg_risk",
    "cluster_member_count",
    # 5. Network & Geographic signals
    "src_country_count",
    "src_asn_count",
    "is_cross_border",
    # 6. Module B pattern & propagation signals
    "pattern_type_code",
    "flag_count",
    "propagated_risk_score",
    "script_type_code",
    # 7. Port-based network signals (PS minimum field: src_port, dst_port)
    "dst_port_is_standard_bitcoin",
    "dst_port_is_tor_proxy",
]


def _parse_timestamp(ts: Any) -> Optional[datetime]:
    """Safely parse ISO8601 timestamp string or datetime object."""
    if isinstance(ts, datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception:
            return None
    return None


def compute_wallet_amount_histories(
    transactions: List[Dict[str, Any]],
) -> Dict[str, Tuple[float, float]]:
    """
    Compute mean and std of transaction output amounts per input wallet address.
    Returns: dict mapping wallet_address -> (mean_amount, std_amount)
    """
    wallet_amounts: Dict[str, List[float]] = {}
    for tx in transactions:
        in_addrs = tx.get("input_addresses") or []
        out_amounts = tx.get("output_amounts") or [0.0]
        total_out = float(sum(out_amounts))
        for addr in in_addrs:
            wallet_amounts.setdefault(addr, []).append(total_out)

    history: Dict[str, Tuple[float, float]] = {}
    for addr, amounts in wallet_amounts.items():
        arr = np.array(amounts, dtype=float)
        mean_val = float(np.mean(arr))
        std_val = float(np.std(arr)) if len(arr) > 1 else 0.0
        history[addr] = (mean_val, std_val)
    return history


def compute_address_bursts(
    transactions: List[Dict[str, Any]],
    window_seconds: float = 3600.0,
) -> Dict[str, int]:
    """
    Compute max transaction count within window_seconds per transaction
    based on participating input addresses.
    """
    # Parse timestamps and sort
    parsed_txs: List[Tuple[datetime, str, Set[str]]] = []
    for tx in transactions:
        ts = _parse_timestamp(tx.get("timestamp"))
        if ts is None:
            ts = datetime.fromtimestamp(0, tz=timezone.utc)
        txid = tx.get("txid", "")
        in_addrs = set(tx.get("input_addresses") or [])
        parsed_txs.append((ts, txid, in_addrs))

    burst_counts: Dict[str, int] = {}
    n = len(parsed_txs)
    for i in range(n):
        ts_i, txid_i, addrs_i = parsed_txs[i]
        count = 1
        for j in range(n):
            if i == j:
                continue
            ts_j, _, addrs_j = parsed_txs[j]
            diff = abs((ts_i - ts_j).total_seconds())
            if diff <= window_seconds and (addrs_i & addrs_j):
                count += 1
        burst_counts[txid_i] = count

    return burst_counts


def compute_graph_metrics(
    graph: Optional[nx.Graph],
) -> Tuple[Dict[str, float], Dict[str, float]]:
    """
    Compute degree centrality and betweenness centrality for graph nodes.
    Returns: (degree_centrality, betweenness_centrality)
    """
    if graph is None or len(graph) == 0:
        return {}, {}
    try:
        # If multi-graph or directed, convert to simple undirected for centrality
        simple_g = nx.Graph(graph)
        deg_cent = nx.degree_centrality(simple_g)
        # For betweenness, compute or approximate if large
        if len(simple_g) <= 1000:
            bet_cent = nx.betweenness_centrality(simple_g)
        else:
            bet_cent = nx.betweenness_centrality(simple_g, k=min(100, len(simple_g)))
        return deg_cent, bet_cent
    except Exception:
        return {}, {}


def build_cluster_lookup(
    clusters: List[Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    """
    Build address -> cluster metadata lookup.
    """
    addr_to_cluster: Dict[str, Dict[str, Any]] = {}
    for c in clusters:
        members = c.get("member_addresses") or []
        info = {
            "cluster_id": c.get("cluster_id", ""),
            "avg_risk_score": float(c.get("avg_risk_score", 0.0)),
            "member_count": int(c.get("member_count", len(members))),
        }
        for m in members:
            addr_to_cluster[m] = info
    return addr_to_cluster


def extract_features_for_txn(
    tx: Dict[str, Any],
    wallet_histories: Optional[Dict[str, Tuple[float, float]]] = None,
    burst_count: int = 1,
    deg_cent: Optional[Dict[str, float]] = None,
    bet_cent: Optional[Dict[str, float]] = None,
    cluster_lookup: Optional[Dict[str, Dict[str, Any]]] = None,
    associated_events: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, float]:
    """
    Extract single transaction feature vector as a dictionary.
    """
    wallet_histories = wallet_histories or {}
    deg_cent = deg_cent or {}
    bet_cent = bet_cent or {}
    cluster_lookup = cluster_lookup or {}
    associated_events = associated_events or []

    # 1. Amount & Value features
    in_amounts = [float(x) for x in (tx.get("input_amounts") or [0.0])]
    out_amounts = [float(x) for x in (tx.get("output_amounts") or [0.0])]
    in_addrs = tx.get("input_addresses") or []
    out_addrs = tx.get("output_addresses") or []

    total_in = float(sum(in_amounts))
    total_out = float(sum(out_amounts))
    fee = float(tx.get("fee", 0.0))
    fee_ratio = fee / (total_in + 1e-7)

    out_arr = np.array(out_amounts, dtype=float)
    out_mean = float(np.mean(out_arr)) if len(out_arr) > 0 else 0.0
    out_std = float(np.std(out_arr)) if len(out_arr) > 1 else 0.0
    out_cv = out_std / (out_mean + 1e-7)

    in_cnt = max(len(in_addrs), len(in_amounts), 1)
    out_cnt = max(len(out_addrs), len(out_amounts), 1)
    out_in_ratio = float(out_cnt) / float(in_cnt)

    max_out = float(np.max(out_arr)) if len(out_arr) > 0 else 0.0
    max_out_fraction = max_out / (total_out + 1e-7)

    # Wallet-relative amount deviation
    deviations: List[float] = []
    for addr in in_addrs:
        if addr in wallet_histories:
            mean_h, std_h = wallet_histories[addr]
            if std_h > 1e-6:
                deviations.append(abs(total_out - mean_h) / std_h)
            else:
                deviations.append(abs(total_out - mean_h) / (mean_h + 1e-7))
    wallet_dev = float(np.mean(deviations)) if deviations else 0.0

    # 2. Temporal features
    dt = _parse_timestamp(tx.get("timestamp"))
    if dt:
        hour = float(dt.hour)
        is_night = 1.0 if hour in [0, 1, 2, 3, 4, 5] else 0.0
    else:
        hour = 12.0
        is_night = 0.0

    # 3. Graph topological features
    all_addrs = set(in_addrs + out_addrs)
    degrees = [deg_cent.get(a, 0.0) for a in all_addrs] if all_addrs else [0.0]
    betweennesses = [bet_cent.get(a, 0.0) for a in all_addrs] if all_addrs else [0.0]

    max_deg = float(np.max(degrees)) if degrees else 0.0
    mean_deg = float(np.mean(degrees)) if degrees else 0.0
    max_bet = float(np.max(betweennesses)) if betweennesses else 0.0

    # 4. Cluster signals
    in_clust = 0.0
    clust_risk = 0.0
    clust_size = 0.0
    for a in all_addrs:
        if a in cluster_lookup:
            in_clust = 1.0
            clust_risk = max(clust_risk, cluster_lookup[a]["avg_risk_score"])
            clust_size = max(clust_size, float(cluster_lookup[a]["member_count"]))

    # 5. Network & Geographic signals
    src_countries: Set[str] = set()
    src_asns: Set[str] = set()
    for ev in associated_events:
        sc = ev.get("src_geo_country")
        sa = ev.get("src_asn")
        if sc:
            src_countries.add(sc)
        if sa:
            src_asns.add(sa)

    src_country_cnt = float(len(src_countries))
    src_asn_cnt = float(len(src_asns))
    is_cross_border = 1.0 if src_country_cnt > 1.0 else 0.0

    # 7. Port-based network signals (PS minimum fields: src_port, dst_port)
    # Bitcoin P2P standard ports: 8333 (mainnet), 18333 (testnet), 18444 (regtest)
    # Tor SOCKS proxy ports: 9050 (default), 9001 (ORPort), 9150 (Tor Browser)
    BITCOIN_PORTS = {8333, 18333, 18444}
    TOR_PORTS = {9050, 9001, 9150}

    dst_port_is_bitcoin = 0.0
    dst_port_is_tor = 0.0
    for ev in associated_events:
        dp = ev.get("dst_port")
        sp = ev.get("src_port")
        if isinstance(dp, int):
            if dp in BITCOIN_PORTS or (isinstance(sp, int) and sp in BITCOIN_PORTS):
                dst_port_is_bitcoin = 1.0
            if dp in TOR_PORTS or (isinstance(sp, int) and sp in TOR_PORTS):
                dst_port_is_tor = 1.0

    # 6. Module B pattern & propagation signals
    pat_raw = str(tx.get("pattern_type", "none")).lower()
    pat_code = PATTERN_TYPE_MAP.get(pat_raw, 0.0)

    flags = tx.get("flags") or []
    flag_cnt = float(len(flags))

    prop_risk = float(tx.get("propagated_risk_score", 0.0))

    script_raw = str(tx.get("script_type", "P2PKH")).upper()
    script_code = SCRIPT_TYPE_MAP.get(script_raw, 0.0)

    features = {
        "total_input_btc": total_in,
        "total_output_btc": total_out,
        "fee_btc": fee,
        "fee_ratio": fee_ratio,
        "output_amount_mean": out_mean,
        "output_amount_std": out_std,
        "output_amount_cv": out_cv,
        "input_count": float(in_cnt),
        "output_count": float(out_cnt),
        "output_to_input_ratio": out_in_ratio,
        "max_output_fraction": max_out_fraction,
        "amount_deviation_from_wallet_mean": wallet_dev,
        "hour_of_day": hour,
        "is_night_hour": is_night,
        "tx_burst_1h_count": float(burst_count),
        "max_addr_degree": max_deg,
        "mean_addr_degree": mean_deg,
        "max_addr_betweenness": max_bet,
        "in_cluster": in_clust,
        "cluster_avg_risk": clust_risk,
        "cluster_member_count": clust_size,
        "src_country_count": src_country_cnt,
        "src_asn_count": src_asn_cnt,
        "is_cross_border": is_cross_border,
        "pattern_type_code": pat_code,
        "flag_count": flag_cnt,
        "propagated_risk_score": prop_risk,
        "script_type_code": script_code,
        "dst_port_is_standard_bitcoin": dst_port_is_bitcoin,
        "dst_port_is_tor_proxy": dst_port_is_tor,
    }
    return features


def engineer_features(
    transactions: List[Dict[str, Any]],
    network_events: Optional[List[Dict[str, Any]]] = None,
    correlation_edges: Optional[List[Dict[str, Any]]] = None,
    clusters: Optional[List[Dict[str, Any]]] = None,
    graph: Optional[nx.Graph] = None,
) -> pd.DataFrame:
    """
    Extract full feature DataFrame for a list of transactions.
    Index will be txid.
    """
    from ml_detection.data_loader import build_txid_to_network_events

    network_events = network_events or []
    correlation_edges = correlation_edges or []
    clusters = clusters or []

    txid_events_map = build_txid_to_network_events(correlation_edges, network_events)
    wallet_histories = compute_wallet_amount_histories(transactions)
    burst_counts = compute_address_bursts(transactions)
    deg_cent, bet_cent = compute_graph_metrics(graph)
    cluster_lookup = build_cluster_lookup(clusters)

    rows: List[Dict[str, float]] = []
    txids: List[str] = []

    for tx in transactions:
        txid = tx.get("txid", f"unknown_tx_{len(txids)}")
        txids.append(txid)
        evs = txid_events_map.get(txid, [])
        burst = burst_counts.get(txid, 1)

        feat = extract_features_for_txn(
            tx=tx,
            wallet_histories=wallet_histories,
            burst_count=burst,
            deg_cent=deg_cent,
            bet_cent=bet_cent,
            cluster_lookup=cluster_lookup,
            associated_events=evs,
        )
        rows.append(feat)

    df = pd.DataFrame(rows, index=txids)
    # Ensure all declared feature columns exist
    for col in FEATURE_COLUMNS:
        if col not in df.columns:
            df[col] = 0.0
    df = df[FEATURE_COLUMNS]
    return df


def clean_features(
    df: pd.DataFrame,
    expected_cols: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, List[str]]:
    """
    Clean and validate feature DataFrame.
    - Fills NaN/inf with column medians or zeros.
    - Enforces expected column set and order.
    Returns: (cleaned_df, feature_column_names)
    """
    cols = expected_cols if expected_cols is not None else FEATURE_COLUMNS
    cleaned = df.copy()

    # Reindex columns to match expected
    for c in cols:
        if c not in cleaned.columns:
            cleaned[c] = 0.0
    cleaned = cleaned[cols]

    # Replace inf and -inf with NaN
    cleaned = cleaned.replace([np.inf, -np.inf], np.nan)

    # Fill NaN with median, or 0.0 if all values are NaN
    for c in cols:
        median_val = cleaned[c].median()
        if pd.isna(median_val):
            median_val = 0.0
        cleaned[c] = cleaned[c].fillna(median_val)

    # Cast to float64
    cleaned = cleaned.astype(np.float64)
    return cleaned, list(cols)
