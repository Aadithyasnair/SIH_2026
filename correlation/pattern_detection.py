"""
Pattern Detection Module for SIH26146 (Focus Area: Peeling-Chain / Mixing Detection)
Detects classic cryptocurrency laundering topologies:
1. Peeling-Chains: Multi-hop transaction sequences where a large fund amount is sequentially
   transferred forward while a small fraction is peeled off at each hop (>= 3-4 consecutive hops).
2. CoinJoin-like / Mixing: Single transactions with multiple roughly equal-value inputs and outputs
   originating from and going to distinct addresses.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Set, Optional, Union, Any, Tuple
from collections import defaultdict
import networkx as nx
import numpy as np

from shared.schemas.records import BlockchainTxn


def parse_iso8601(ts: str) -> datetime:
    """Parses ISO8601 string to UTC datetime."""
    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


@dataclass
class PatternResult:
    txid: str
    pattern_type: str  # "peeling_chain", "coinjoin_mixing", "none"
    flags: List[str] = field(default_factory=list)
    confidence: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


def detect_coinjoin_transactions(
    txns: List[BlockchainTxn],
    min_inputs: int = 3,
    min_outputs: int = 3,
    max_cv: float = 0.20
) -> Dict[str, PatternResult]:
    """
    Detects CoinJoin / mixing transactions:
    - High number of distinct inputs and outputs
    - Low coefficient of variation (std / mean) among output amounts (roughly equal values)
    """
    results = {}

    for tx in txns:
        unique_inputs = set(tx.input_addresses)
        unique_outputs = set(tx.output_addresses)

        # Criteria: multiple distinct inputs and outputs with roughly equal denominations on both sides
        if len(unique_inputs) >= min_inputs and len(unique_outputs) >= min_outputs:
            in_amts = np.array(tx.input_amounts, dtype=float)
            out_amts = np.array(tx.output_amounts, dtype=float)
            if len(in_amts) > 0 and len(out_amts) > 0 and np.mean(in_amts) > 0 and np.mean(out_amts) > 0:
                cv_in = float(np.std(in_amts) / np.mean(in_amts))
                cv_out = float(np.std(out_amts) / np.mean(out_amts))
                if cv_in <= max_cv and cv_out <= max_cv:
                    cv_avg = (cv_in + cv_out) / 2.0
                    results[tx.txid] = PatternResult(
                        txid=tx.txid,
                        pattern_type="coinjoin_mixing",
                        flags=[
                            "coinjoin_mixing_structure",
                            f"equal_denomination_inputs_{len(unique_inputs)}",
                            f"equal_denomination_outputs_{len(unique_outputs)}",
                            f"multi_party_participants_{len(unique_inputs)}"
                        ],
                        confidence=round(max(0.70, 1.0 - cv_avg), 3),
                        details={
                            "input_count": len(unique_inputs),
                            "output_count": len(unique_outputs),
                            "mean_input_btc": float(np.mean(in_amts)),
                            "mean_output_btc": float(np.mean(out_amts)),
                            "cv_inputs": float(cv_in),
                            "cv_outputs": float(cv_out)
                        }
                    )

    return results


def detect_peeling_chains(
    txns: List[BlockchainTxn],
    min_hops: int = 3,
    forward_ratio_min: float = 0.65,
    peel_ratio_max: float = 0.35
) -> Dict[str, PatternResult]:
    """
    Detects peeling chain sequences:
    Walks sequential transactions where:
    - A transaction has 1 primary input and 2 outputs (forward output + peel output)
    - Forward output carries >= 65% of the total amount
    - Peel output carries <= 35% of the total amount
    - The forward output address becomes the single input for the next transaction in sequence
    - Sequence persists for >= min_hops (default 3 hops)
    """
    # Index transactions by input address
    tx_by_input = defaultdict(list)
    tx_by_id = {}

    for tx in txns:
        tx_by_id[tx.txid] = tx
        for in_addr in tx.input_addresses:
            tx_by_input[in_addr].append(tx)

    # Find candidate peeling hops (1 input -> 2 outputs with asymmetric amounts)
    def is_peel_hop(tx: BlockchainTxn) -> Optional[Tuple[str, float, str, float]]:
        """Returns (forward_addr, forward_amt, peel_addr, peel_amt) if tx looks like a peel hop."""
        if len(tx.input_addresses) == 1 and len(tx.output_addresses) == 2:
            out_0, out_1 = tx.output_addresses[0], tx.output_addresses[1]
            amt_0, amt_1 = tx.output_amounts[0], tx.output_amounts[1]
            total_out = amt_0 + amt_1
            if total_out <= 0:
                return None

            # Case A: output 0 is forward, output 1 is peel
            if (amt_0 / total_out) >= forward_ratio_min and (amt_1 / total_out) <= peel_ratio_max:
                return (out_0, amt_0, out_1, amt_1)

            # Case B: output 1 is forward, output 0 is peel
            if (amt_1 / total_out) >= forward_ratio_min and (amt_0 / total_out) <= peel_ratio_max:
                return (out_1, amt_1, out_0, amt_0)

        return None

    # Trace chains
    chains = []  # List of [txid_0, txid_1, ...]
    visited_txids = set()

    for tx in txns:
        if tx.txid in visited_txids:
            continue

        hop_info = is_peel_hop(tx)
        if hop_info is not None:
            current_chain = [tx.txid]
            curr_tx = tx
            fwd_addr = hop_info[0]

            while True:
                next_candidates = tx_by_input.get(fwd_addr, [])
                curr_time = parse_iso8601(curr_tx.timestamp)

                # Filter to unused candidates occurring strictly AFTER current hop
                valid_candidates = [
                    cand for cand in next_candidates
                    if cand.txid not in current_chain and parse_iso8601(cand.timestamp) > curr_time
                ]
                # Sort chronologically ascending to pick the immediate chronological next hop
                valid_candidates.sort(key=lambda cand: parse_iso8601(cand.timestamp))

                found_next = False
                for next_tx in valid_candidates:
                    next_hop_info = is_peel_hop(next_tx)
                    if next_hop_info is not None:
                        current_chain.append(next_tx.txid)
                        curr_tx = next_tx
                        fwd_addr = next_hop_info[0]
                        found_next = True
                        break
                if not found_next:
                    break

            if len(current_chain) >= min_hops:
                chains.append(current_chain)
                for t_id in current_chain:
                    visited_txids.add(t_id)

    # Compile results for all transactions in peeling chains
    results = {}
    for chain in chains:
        chain_len = len(chain)
        for hop_idx, t_id in enumerate(chain):
            results[t_id] = PatternResult(
                txid=t_id,
                pattern_type="peeling_chain",
                flags=[
                    f"peeling_chain_hop_{hop_idx + 1}_of_{chain_len}",
                    "rapid_layering_structure"
                ],
                confidence=round(min(0.95, 0.70 + 0.05 * chain_len), 2),
                details={
                    "chain_length": chain_len,
                    "hop_index": hop_idx + 1,
                    "chain_txids": chain
                }
            )

    return results


def detect_patterns(
    graph: nx.MultiDiGraph,
    txns: List[Union[BlockchainTxn, Dict[str, Any]]]
) -> Dict[str, PatternResult]:
    """
    Runs all pattern detection routines across transactions.
    Returns mapping from txid -> PatternResult.
    """
    typed_txns: List[BlockchainTxn] = [
        tx if isinstance(tx, BlockchainTxn) else BlockchainTxn(**tx) for tx in txns
    ]

    all_results: Dict[str, PatternResult] = {}

    # 1. Detect CoinJoin mixing transactions
    cj_results = detect_coinjoin_transactions(typed_txns)
    all_results.update(cj_results)

    # 2. Detect Peeling chain sequences
    peel_results = detect_peeling_chains(typed_txns)
    all_results.update(peel_results)

    # 3. For any txns not flagged, populate default "none" result
    for tx in typed_txns:
        if tx.txid not in all_results:
            all_results[tx.txid] = PatternResult(
                txid=tx.txid,
                pattern_type="none",
                flags=[],
                confidence=0.0,
                details={}
            )

    return all_results
