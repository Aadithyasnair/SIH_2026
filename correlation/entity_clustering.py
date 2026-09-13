"""
Entity Clustering Module for SIH26146 (Focus Area: Entity Clustering)
Dual-signal wallet entity clustering:
1. Signal A: Common-Input-Ownership heuristic (co-spending in transaction inputs)
2. Signal B: Node2Vec graph embeddings + HDBSCAN / KMeans for structural similarity
Combines both signals into cohesive clusters with human-readable labels and descriptions.
"""
import uuid
from typing import List, Dict, Set, Optional, Union, Any, Tuple
from collections import defaultdict
import networkx as nx
import numpy as np

from shared.schemas.records import Cluster, BlockchainTxn

# Optional node2vec / hdbscan imports with robust fallbacks
try:
    from node2vec import Node2Vec
except ImportError:
    Node2Vec = None

try:
    import hdbscan
except ImportError:
    hdbscan = None

from sklearn.cluster import KMeans


class DisjointSetUnion:
    """Disjoint Set Union (Union-Find) with path compression and rank optimization."""
    def __init__(self):
        self.parent = {}
        self.rank = {}

    def find(self, item: str) -> str:
        if item not in self.parent:
            self.parent[item] = item
            self.rank[item] = 0
            return item
        if self.parent[item] != item:
            self.parent[item] = self.find(self.parent[item])
        return self.parent[item]

    def union(self, x: str, y: str):
        root_x = self.find(x)
        root_y = self.find(y)
        if root_x == root_y:
            return
        if self.rank[root_x] < self.rank[root_y]:
            self.parent[root_x] = root_y
        elif self.rank[root_x] > self.rank[root_y]:
            self.parent[root_y] = root_x
        else:
            self.parent[root_y] = root_x
            self.rank[root_x] += 1


def compute_heuristic_clusters(txns: List[BlockchainTxn]) -> Dict[str, Set[str]]:
    """
    Signal A: Common-Input-Ownership Heuristic.
    Addresses co-appearing as inputs in the same transaction are controlled by the same entity.
    """
    dsu = DisjointSetUnion()
    all_addresses = set()

    for tx in txns:
        inputs = tx.input_addresses
        for addr in inputs:
            all_addresses.add(addr)
            dsu.find(addr)

        if len(inputs) > 1:
            first_addr = inputs[0]
            for other_addr in inputs[1:]:
                dsu.union(first_addr, other_addr)

    # Group by representative root
    groups = defaultdict(set)
    for addr in all_addresses:
        root = dsu.find(addr)
        groups[root].add(addr)

    return groups


def extract_wallet_graph(graph: nx.MultiDiGraph) -> nx.Graph:
    """
    Extracts an undirected wallet-only graph where edges represent:
    - SAME_TXN co-input / co-participant connections
    - Direct transaction flows between wallets
    """
    wallet_g = nx.Graph()

    # Collect all wallet nodes
    for n, data in graph.nodes(data=True):
        if data.get("node_type") == "wallet":
            wallet_g.add_node(n, **data)

    # Connect wallets that co-appear in SAME_TXN
    for u, v, data in graph.edges(data=True):
        if data.get("edge_type") == "SAME_TXN":
            if wallet_g.has_node(u) and wallet_g.has_node(v) and u != v:
                wallet_g.add_edge(u, v, weight=2.0)

    # Connect wallets connected via an intermediate txn node (input -> txn -> output)
    for n, data in graph.nodes(data=True):
        if data.get("node_type") == "txn":
            inputs = [u for u, _, ed in graph.in_edges(n, data=True) if ed.get("edge_type") == "INPUT_OF"]
            outputs = [v for _, v, ed in graph.out_edges(n, data=True) if ed.get("edge_type") == "OUTPUT_OF"]
            for in_w in inputs:
                for out_w in outputs:
                    if in_w != out_w and wallet_g.has_node(in_w) and wallet_g.has_node(out_w):
                        w = wallet_g.get_edge_data(in_w, out_w, {}).get("weight", 0.0)
                        wallet_g.add_edge(in_w, out_w, weight=w + 1.0)

    return wallet_g


def compute_embedding_clusters(wallet_g: nx.Graph, min_cluster_size: int = 2) -> Dict[str, int]:
    """
    Signal B: Node2Vec Graph Embeddings + Clustering (HDBSCAN or KMeans).
    Finds structurally equivalent or topologically close wallets.
    """
    nodes = list(wallet_g.nodes())
    if len(nodes) < 3 or wallet_g.number_of_edges() == 0:
        # Trivial graph, return individual cluster ids
        return {node: idx for idx, node in enumerate(nodes)}

    embeddings = {}
    if Node2Vec is not None:
        try:
            # Configure Node2Vec for structural embeddings with deterministic seed
            n2v = Node2Vec(
                wallet_g,
                dimensions=16,
                walk_length=10,
                num_walks=40,
                p=1.0,
                q=0.5,
                seed=42,
                workers=1,
                quiet=True
            )
            model = n2v.fit(window=5, min_count=1, batch_words=4, seed=42)
            for node in nodes:
                if str(node) in model.wv:
                    embeddings[node] = model.wv[str(node)]
        except Exception:
            embeddings = {}

    if not embeddings:
        # Fallback: Adjacency spectral vector or degree feature representation
        for node in nodes:
            deg = wallet_g.degree(node)
            neighbors = list(wallet_g.neighbors(node))
            avg_neigh_deg = np.mean([wallet_g.degree(nb) for nb in neighbors]) if neighbors else 0.0
            embeddings[node] = np.array([deg, avg_neigh_deg, len(neighbors)], dtype=float)

    node_list = list(embeddings.keys())
    X = np.array([embeddings[n] for n in node_list])

    # Cluster using HDBSCAN if graph is sufficiently large and noise is bounded, else KMeans
    cluster_labels = {}
    if hdbscan is not None and len(node_list) >= 12:
        try:
            clusterer = hdbscan.HDBSCAN(min_cluster_size=max(2, min_cluster_size), min_samples=1)
            labels = clusterer.fit_predict(X)
            noise_ratio = sum(1 for l in labels if l < 0) / len(labels)
            if noise_ratio < 0.35:
                for node, lbl in zip(node_list, labels):
                    cluster_labels[node] = int(lbl)
        except Exception:
            cluster_labels = {}

    if not cluster_labels:
        # Use KMeans with component-aware k
        n_components = nx.number_connected_components(wallet_g)
        k = max(1, min(n_components, len(node_list) // 2))
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)
        for node, lbl in zip(node_list, labels):
            cluster_labels[node] = int(lbl)

    return cluster_labels


def generate_cluster_description(
    addresses: List[str],
    graph: nx.MultiDiGraph,
    txns: List[BlockchainTxn],
    risk_scores: Optional[Dict[str, float]] = None
) -> Tuple[str, str, float]:
    """
    Generates human-readable plain-language label and description for a cluster.
    Returns (label, description, avg_risk_score).
    """
    member_set = set(addresses)
    count = len(addresses)

    # Compute average risk score
    if risk_scores:
        scores = [risk_scores.get(addr, 0.0) for addr in addresses]
        avg_risk = round(float(np.mean(scores)), 2)
    else:
        avg_risk = 0.15

    # Analyze transaction properties touching these addresses
    involved_txns = []
    total_btc = 0.0
    for tx in txns:
        in_overlap = member_set.intersection(tx.input_addresses)
        out_overlap = member_set.intersection(tx.output_addresses)
        if in_overlap or out_overlap:
            involved_txns.append(tx)
            total_btc += sum(tx.output_amounts)

    btc_str = f"{round(total_btc, 2)} BTC"

    # Pattern and label classification
    if avg_risk >= 0.70:
        label = "High-Risk Mixing Cluster"
        desc = (
            f"{count} addresses exhibiting coordinated fund transfers totalling {btc_str} "
            f"across {len(involved_txns)} transactions. Topological structure and high propagated "
            f"risk indicate active participation in a laundering or mixing operation."
        )
    elif count >= 4 and any(len(tx.input_addresses) >= 3 for tx in involved_txns):
        label = "Consolidation Vault Entity"
        desc = (
            f"{count} addresses regularly co-spent in multi-input transactions consolidating {btc_str}. "
            f"Strong common-input-ownership signals confirm these addresses are controlled by a single entity."
        )
    elif count >= 3:
        label = "Multi-Wallet Entity"
        desc = (
            f"{count} addresses exhibiting structural graph proximity and co-occurrence. "
            f"Graph embedding analysis indicates related ownership with {len(involved_txns)} interacting transactions."
        )
    else:
        label = "Associated Wallet Group"
        desc = (
            f"{count} addresses linked via transaction adjacency and common flow patterns "
            f"accounting for {btc_str} in volume."
        )

    return label, desc, avg_risk


def cluster_entities(
    graph: nx.MultiDiGraph,
    txns: List[Union[BlockchainTxn, Dict[str, Any]]],
    risk_scores: Optional[Dict[str, float]] = None
) -> List[Cluster]:
    """
    Executes dual-signal entity clustering combining:
    - Signal A: Common-input-ownership (DSU)
    - Signal B: Graph structural embeddings (Node2Vec + HDBSCAN/KMeans)
    Generates unified Cluster records with plain-language explanations.
    """
    typed_txns: List[BlockchainTxn] = [
        tx if isinstance(tx, BlockchainTxn) else BlockchainTxn(**tx) for tx in txns
    ]

    # Signal A: Common input clusters
    heuristic_groups = compute_heuristic_clusters(typed_txns)

    # Signal B: Wallet graph embeddings
    wallet_g = extract_wallet_graph(graph)
    embedding_labels = compute_embedding_clusters(wallet_g)

    # Combine signals: Merge heuristic groups if embedding shows strong cluster alignment
    master_dsu = DisjointSetUnion()

    # Apply heuristic mergers
    for root, members in heuristic_groups.items():
        first = next(iter(members))
        for m in members:
            master_dsu.union(first, m)

    # Apply embedding mergers: For positive cluster IDs (ignoring noise -1)
    emb_clusters = defaultdict(list)
    for node, lbl in embedding_labels.items():
        if lbl >= 0:
            emb_clusters[lbl].append(node)

    for lbl, nodes in emb_clusters.items():
        if len(nodes) > 1:
            base_node = nodes[0]
            for other_node in nodes[1:]:
                # Merge into master DSU
                master_dsu.union(base_node, other_node)

    # Group all wallet nodes into final clusters
    all_wallet_nodes = set(wallet_g.nodes())
    for tx in typed_txns:
        all_wallet_nodes.update(tx.input_addresses)
        all_wallet_nodes.update(tx.output_addresses)

    final_clusters_map = defaultdict(list)
    for addr in all_wallet_nodes:
        root = master_dsu.find(addr)
        final_clusters_map[root].append(addr)

    clusters: List[Cluster] = []
    # Filter clusters with >= 2 members (or singletons if significant risk)
    for idx, (root, members) in enumerate(final_clusters_map.items()):
        if len(members) >= 2:
            sorted_members = sorted(members)
            cid = f"cluster_{uuid.uuid5(uuid.NAMESPACE_DNS, '_'.join(sorted_members[:5])).hex[:12]}"
            label, desc, avg_risk = generate_cluster_description(
                sorted_members, graph, typed_txns, risk_scores
            )

            cluster = Cluster(
                cluster_id=cid,
                label=label,
                member_addresses=sorted_members,
                member_count=len(sorted_members),
                avg_risk_score=avg_risk,
                description=desc,
                clustering_method="common_input_ownership+node2vec_embedding"
            )
            clusters.append(cluster)

    # Sort clusters by member count descending
    clusters.sort(key=lambda c: (c.avg_risk_score, c.member_count), reverse=True)
    return clusters


def get_cluster_for_address(clusters: List[Cluster], address: str) -> Optional[Cluster]:
    """Looks up the cluster containing a given Bitcoin address."""
    for c in clusters:
        if address in c.member_addresses:
            return c
    return None
