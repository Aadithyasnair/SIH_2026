"""
Risk Propagation Module for SIH26146 (Focus Area: Risk Scoring)
Propagates risk scores outward from seed illicit wallets across the transaction graph
using algorithmic diffusion (Personalized PageRank & Hop-decay diffusion).

Properties:
- Seed illicit wallets: Initial risk = 1.0
- Algorithmic diffusion decays with graph distance (hops)
- Meaningfully higher risk for 1-hop neighbors compared to 4+ hop nodes
- Scores strictly bounded within [0.0, 1.0]
"""
from typing import List, Dict, Set, Optional, Union, Any
import networkx as nx
import numpy as np


def build_wallet_transition_graph(graph: nx.MultiDiGraph) -> nx.DiGraph:
    """
    Constructs a directed flow graph between wallets for risk diffusion.
    If wallet A sends funds to wallet B via transaction T, directed edge A -> B is created
    weighted by transfer amount or transaction frequency.
    """
    wallet_flow = nx.DiGraph()

    for n, data in graph.nodes(data=True):
        if data.get("node_type") == "wallet":
            wallet_flow.add_node(n)

    # Walk input -> txn -> output to link source wallet to destination wallet
    for n, data in graph.nodes(data=True):
        if data.get("node_type") == "txn":
            inputs = [
                (u, ed.get("amount", 1.0))
                for u, _, ed in graph.in_edges(n, data=True)
                if ed.get("edge_type") == "INPUT_OF"
            ]
            outputs = [
                (v, ed.get("amount", 1.0))
                for _, v, ed in graph.out_edges(n, data=True)
                if ed.get("edge_type") == "OUTPUT_OF"
            ]

            for in_w, in_amt in inputs:
                for out_w, out_amt in outputs:
                    if in_w != out_w:
                        w = wallet_flow.get_edge_data(in_w, out_w, {}).get("weight", 0.0)
                        # Weight proportional to flow
                        flow_weight = max(0.1, min(out_amt, in_amt) if in_amt > 0 and out_amt > 0 else 1.0)
                        wallet_flow.add_edge(in_w, out_w, weight=w + flow_weight)

    # Also add SAME_TXN bidirectional co-input edges with high transmission weight
    for u, v, data in graph.edges(data=True):
        if data.get("edge_type") == "SAME_TXN" and data.get("relation") == "co_input":
            if wallet_flow.has_node(u) and wallet_flow.has_node(v):
                w_uv = wallet_flow.get_edge_data(u, v, {}).get("weight", 0.0)
                wallet_flow.add_edge(u, v, weight=w_uv + 2.0)
                w_vu = wallet_flow.get_edge_data(v, u, {}).get("weight", 0.0)
                wallet_flow.add_edge(v, u, weight=w_vu + 2.0)

    return wallet_flow


def propagate_risk_pagerank(
    flow_graph: nx.DiGraph,
    seed_wallets: List[str],
    alpha: float = 0.85
) -> Dict[str, float]:
    """
    Computes Personalized PageRank starting from seed illicit wallets.
    """
    nodes = list(flow_graph.nodes())
    if not nodes:
        return {}

    valid_seeds = [s for s in seed_wallets if s in flow_graph]
    if not valid_seeds:
        # If no seeds present in graph, return baseline 0.0
        return {n: 0.0 for n in nodes}

    # Build personalization vector: equal weight on seed illicit wallets
    personalization = {n: (1.0 / len(valid_seeds) if n in valid_seeds else 0.0) for n in nodes}

    try:
        raw_scores = nx.pagerank(
            flow_graph,
            alpha=alpha,
            personalization=personalization,
            weight="weight",
            max_iter=200
        )
    except Exception:
        # Fallback to unweighted or standard power iteration
        raw_scores = nx.pagerank(flow_graph, alpha=alpha, personalization=personalization)

    # Normalize scores: seed wallets should be near 1.0, and decay relative to maximum
    max_score = max(raw_scores.values()) if raw_scores else 1.0
    if max_score <= 0:
        return {n: 0.0 for n in nodes}

    normalized = {}
    for n, s in raw_scores.items():
        # Min-max scale relative to top score
        score_ratio = s / max_score
        if n in valid_seeds:
            normalized[n] = 1.0
        else:
            # Power scaling to ensure sharp contrast across hops
            val = round(float(np.clip(score_ratio ** 0.6, 0.0, 0.99)), 4)
            normalized[n] = val

    return normalized


def propagate_risk_hop_decay(
    flow_graph: nx.DiGraph,
    seed_wallets: List[str],
    decay_factor: float = 0.50,
    max_hops: int = 5
) -> Dict[str, float]:
    """
    Iterative multi-hop decay diffusion:
    - Seeds start at risk = 1.0
    - Each hop multiplies incoming risk by decay_factor (e.g. 0.50)
    - Meaning hop 1 ~ 0.50, hop 2 ~ 0.25, hop 3 ~ 0.125, hop 4+ ~ <= 0.06
    """
    nodes = list(flow_graph.nodes())
    risk_scores = {n: 0.0 for n in nodes}

    valid_seeds = [s for s in seed_wallets if s in flow_graph]
    for s in valid_seeds:
        risk_scores[s] = 1.0

    if not valid_seeds:
        return risk_scores

    # Directed breadth-first shortest path hop decay (outward propagation)
    for seed in valid_seeds:
        # Traverse directed graph along fund transfers (co-inputs are already bidirectional)
        lengths = nx.single_source_shortest_path_length(flow_graph, seed, cutoff=max_hops)
        for target, hops in lengths.items():
            if hops == 0:
                hop_risk = 1.0
            else:
                hop_risk = decay_factor ** hops

            # Accumulate risk without exceeding 1.0
            risk_scores[target] = max(risk_scores[target], hop_risk)

    return {n: round(float(v), 4) for n, v in risk_scores.items()}


def propagate_risk(
    graph: nx.MultiDiGraph,
    labels: Union[Dict[str, Any], List[str]],
    method: str = "hybrid"
) -> Dict[str, float]:
    """
    Main risk propagation entrypoint:
    Extracts seed illicit wallets from labels and propagates risk scores across the graph.

    Returns:
        Dict[wallet_address, propagated_risk_score in [0.0, 1.0]]
    """
    # Extract seed wallets
    seed_wallets = []
    if isinstance(labels, dict):
        seed_wallets = labels.get("seed_illicit_wallets", [])
        # Also check anomalous_transactions if addresses tagged
        for anom in labels.get("anomalous_transactions", []):
            if "seed_wallet" in anom:
                seed_wallets.append(anom["seed_wallet"])
    elif isinstance(labels, list):
        seed_wallets = labels

    flow_graph = build_wallet_transition_graph(graph)

    if method == "pagerank":
        return propagate_risk_pagerank(flow_graph, seed_wallets)
    elif method == "hop_decay":
        return propagate_risk_hop_decay(flow_graph, seed_wallets)
    else:  # hybrid
        # Combine Personalized PageRank with Hop Decay guarantee
        pr_scores = propagate_risk_pagerank(flow_graph, seed_wallets)
        hop_scores = propagate_risk_hop_decay(flow_graph, seed_wallets)

        combined = {}
        for node in flow_graph.nodes():
            pr_val = pr_scores.get(node, 0.0)
            hop_val = hop_scores.get(node, 0.0)
            if node in seed_wallets:
                combined[node] = 1.0
            else:
                combined[node] = round(float(0.5 * pr_val + 0.5 * hop_val), 4)

        return combined
