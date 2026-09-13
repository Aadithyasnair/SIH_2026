"""
Graph Builder for SIH26146
Constructs a unified multi-entity NetworkX graph connecting:
- IP nodes
- Wallet address nodes
- Transaction nodes (txid)
Edges:
- CONNECTS_TO: IP-to-IP network flows
- INPUT_OF: wallet address -> transaction input
- OUTPUT_OF: transaction -> wallet address output
- SAME_TXN: linking addresses that co-appear in the same transaction
- CORRELATES_WITH: network event <-> blockchain transaction
"""
from typing import List, Union, Dict, Any
import networkx as nx

from shared.schemas.records import NetworkEvent, BlockchainTxn, CorrelationEdge


def build_graph(
    events: List[Union[NetworkEvent, Dict[str, Any]]],
    txns: List[Union[BlockchainTxn, Dict[str, Any]]]
) -> nx.MultiDiGraph:
    """
    Builds a unified multi-entity graph from network events and blockchain transactions.
    """
    G = nx.MultiDiGraph()

    # 1. Process Network Events (IP nodes & CONNECTS_TO edges)
    for event in events:
        if isinstance(event, dict):
            event = NetworkEvent(**event)

        # IP Nodes
        if not G.has_node(event.src_ip):
            G.add_node(
                event.src_ip,
                node_type="ip",
                geo_country=event.src_geo_country,
                asn=event.src_asn
            )
        if not G.has_node(event.dst_ip):
            G.add_node(
                event.dst_ip,
                node_type="ip",
                geo_country=event.dst_geo_country,
                asn=event.dst_asn
            )

        # CONNECTS_TO Edge (Network flow)
        G.add_edge(
            event.src_ip,
            event.dst_ip,
            key=f"net_{event.event_id}",
            edge_type="CONNECTS_TO",
            event_id=event.event_id,
            timestamp=event.timestamp,
            src_port=event.src_port,
            dst_port=event.dst_port,
            protocol=event.protocol,
            packet_size=event.packet_size
        )

    # 2. Process Blockchain Transactions (Txn nodes, Wallet nodes, Flow & SAME_TXN edges)
    for txn in txns:
        if isinstance(txn, dict):
            txn = BlockchainTxn(**txn)

        txid = txn.txid
        # Txn Node
        total_in = sum(txn.input_amounts) if txn.input_amounts else 0.0
        total_out = sum(txn.output_amounts) if txn.output_amounts else 0.0
        G.add_node(
            txid,
            node_type="txn",
            timestamp=txn.timestamp,
            fee=txn.fee,
            script_type=txn.script_type,
            total_input_btc=total_in,
            total_output_btc=total_out
        )

        # Wallet Nodes & Input Edges
        for idx, in_addr in enumerate(txn.input_addresses):
            amt = txn.input_amounts[idx] if idx < len(txn.input_amounts) else 0.0
            if not G.has_node(in_addr):
                G.add_node(in_addr, node_type="wallet", address=in_addr)
            G.add_edge(
                in_addr,
                txid,
                key=f"in_{in_addr}_{txid}_{idx}",
                edge_type="INPUT_OF",
                amount=amt,
                timestamp=txn.timestamp
            )

        # Wallet Nodes & Output Edges
        for idx, out_addr in enumerate(txn.output_addresses):
            amt = txn.output_amounts[idx] if idx < len(txn.output_amounts) else 0.0
            if not G.has_node(out_addr):
                G.add_node(out_addr, node_type="wallet", address=out_addr)
            G.add_edge(
                txid,
                out_addr,
                key=f"out_{txid}_{out_addr}_{idx}",
                edge_type="OUTPUT_OF",
                amount=amt,
                timestamp=txn.timestamp
            )

        # SAME_TXN Edges linking all co-appearing input addresses (common-input ownership)
        in_addrs = list(dict.fromkeys(txn.input_addresses))  # deduplicate preserving order
        for i in range(len(in_addrs)):
            for j in range(i + 1, len(in_addrs)):
                addr1, addr2 = in_addrs[i], in_addrs[j]
                # Undirected semantic in MultiDiGraph represented bidirectionally
                G.add_edge(
                    addr1,
                    addr2,
                    key=f"same_in_{txid}_{i}_{j}",
                    edge_type="SAME_TXN",
                    txid=txid,
                    relation="co_input"
                )
                G.add_edge(
                    addr2,
                    addr1,
                    key=f"same_in_{txid}_{j}_{i}",
                    edge_type="SAME_TXN",
                    txid=txid,
                    relation="co_input"
                )

        # Also link inputs to outputs under SAME_TXN flow
        all_addrs = list(dict.fromkeys(txn.input_addresses + txn.output_addresses))
        for i in range(len(all_addrs)):
            for j in range(i + 1, len(all_addrs)):
                a1, a2 = all_addrs[i], all_addrs[j]
                if not G.has_edge(a1, a2, key=f"same_txn_{txid}_{i}_{j}"):
                    G.add_edge(
                        a1,
                        a2,
                        key=f"same_txn_{txid}_{i}_{j}",
                        edge_type="SAME_TXN",
                        txid=txid,
                        relation="co_participant"
                    )
                    G.add_edge(
                        a2,
                        a1,
                        key=f"same_txn_{txid}_{j}_{i}",
                        edge_type="SAME_TXN",
                        txid=txid,
                        relation="co_participant"
                    )

    return G


def add_correlation_edges(
    graph: nx.MultiDiGraph,
    correlation_edges: List[Union[CorrelationEdge, Dict[str, Any]]]
) -> None:
    """
    Augments the graph with CORRELATES_WITH edges between network events / IPs and transactions.
    """
    for edge in correlation_edges:
        if isinstance(edge, dict):
            edge = CorrelationEdge(**edge)

        # Find the src_ip associated with this network event
        ev_id = edge.network_event_id
        txid = edge.txid

        # Find network event edge in graph to get endpoints if present
        matching_ip = None
        for u, v, k, data in graph.edges(keys=True, data=True):
            if data.get("edge_type") == "CONNECTS_TO" and data.get("event_id") == ev_id:
                matching_ip = u  # src_ip
                break

        endpoint = matching_ip if matching_ip else f"event_{ev_id}"
        if not graph.has_node(endpoint):
            graph.add_node(endpoint, node_type="event", event_id=ev_id)

        if graph.has_node(txid):
            graph.add_edge(
                endpoint,
                txid,
                key=f"corr_{edge.edge_id}",
                edge_type="CORRELATES_WITH",
                edge_id=edge.edge_id,
                network_event_id=ev_id,
                confidence=edge.confidence,
                correlation_type=edge.correlation_type
            )


def export_graphml(graph: nx.MultiDiGraph, path: str) -> None:
    """
    Exports the NetworkX graph to GraphML format for persistence or Neo4j import.
    Cleans non-scalar attributes if necessary.
    """
    exportable = nx.MultiDiGraph()
    for n, data in graph.nodes(data=True):
        clean_data = {k: str(v) if isinstance(v, (list, dict)) else v for k, v in data.items()}
        exportable.add_node(n, **clean_data)

    for u, v, k, data in graph.edges(keys=True, data=True):
        clean_data = {key: str(val) if isinstance(val, (list, dict)) else val for key, val in data.items()}
        exportable.add_edge(u, v, key=str(k), **clean_data)

    nx.write_graphml(exportable, path)
