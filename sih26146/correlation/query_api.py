"""
Query API for SIH26146 Backend & Frontend Integration
Exposes reusable subgraph queries and cluster queries matching FastAPI / Next.js contract shapes.
"""
from typing import List, Dict, Any, Optional
from collections import deque
import networkx as nx

from sih26146.shared.schemas.records import Cluster


def get_subgraph(
    graph: nx.MultiDiGraph,
    node_id: str,
    depth: int = 2
) -> Dict[str, Any]:
    """
    Extracts an ego subgraph centered at `node_id` up to `depth` hops.
    Returns JSON-serializable dictionary:
    {
        "nodes": [{"id": ..., "type": ..., ...}],
        "edges": [{"id": ..., "source": ..., "target": ..., "type": ..., ...}]
    }
    """
    if not graph.has_node(node_id):
        return {"nodes": [], "edges": []}

    # Breadth-first search up to depth hops
    visited_nodes = {node_id}
    queue = deque([(node_id, 0)])

    # Use undirected view to traverse edges in both directions
    undirected_g = graph.to_undirected(as_view=True)

    while queue:
        curr, d = queue.popleft()
        if d < depth:
            for neighbor in undirected_g.neighbors(curr):
                if neighbor not in visited_nodes:
                    visited_nodes.add(neighbor)
                    queue.append((neighbor, d + 1))

    # Collect nodes
    nodes_payload = []
    for n in visited_nodes:
        attrs = dict(graph.nodes[n])
        node_entry = {
            "id": str(n),
            "type": attrs.get("node_type", "unknown")
        }
        for k, v in attrs.items():
            if k != "node_type":
                node_entry[k] = v if isinstance(v, (str, int, float, bool)) else str(v)
        nodes_payload.append(node_entry)

    # Collect edges connecting the visited nodes
    edges_payload = []
    seen_edge_keys = set()
    for u, v, k, data in graph.edges(keys=True, data=True):
        if u in visited_nodes and v in visited_nodes:
            edge_key = f"{u}_{v}_{k}"
            if edge_key not in seen_edge_keys:
                seen_edge_keys.add(edge_key)
                edge_entry = {
                    "id": str(k),
                    "source": str(u),
                    "target": str(v),
                    "type": data.get("edge_type", "RELATED_TO")
                }
                for key, val in data.items():
                    if key not in ("edge_type",):
                        edge_entry[key] = val if isinstance(val, (str, int, float, bool)) else str(val)
                edges_payload.append(edge_entry)

    return {
        "nodes": nodes_payload,
        "edges": edges_payload
    }


def get_clusters(clusters: List[Cluster]) -> List[Dict[str, Any]]:
    """
    Returns full list of Cluster records formatted as serializable dictionaries.
    """
    return [c.model_dump() for c in clusters]


def get_cluster_by_id(
    clusters: List[Cluster],
    cluster_id: str
) -> Optional[Dict[str, Any]]:
    """
    Looks up and returns a single Cluster record by cluster_id.
    """
    for c in clusters:
        if c.cluster_id == cluster_id:
            return c.model_dump()
    return None
