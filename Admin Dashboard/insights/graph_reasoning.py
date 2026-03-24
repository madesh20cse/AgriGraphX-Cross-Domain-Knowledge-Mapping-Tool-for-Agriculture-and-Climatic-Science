"""Graph reasoning utilities for AI Insights.

These helpers operate on the existing KnowledgeGraph (Module 3) to
pull a small, human-scale subgraph relevant to a set of entities.
"""

from __future__ import annotations

from collections import deque
from typing import Any, Dict, Iterable, List, Tuple

from knowledge_graph import KnowledgeGraph


def _as_nx_graph(graph: Any):
    """Return the underlying NetworkX graph from either KnowledgeGraph or raw graph."""
    if isinstance(graph, KnowledgeGraph):
        return graph.graph
    return graph


def find_related_subgraph(
    graph: Any,
    entities: Iterable[str],
    max_hops: int = 2,
    max_relations: int = 40,
) -> List[Dict[str, Any]]:
    """Traverse the graph around the given entities and collect edges.

    Parameters
    ----------
    graph:
        Either a :class:`KnowledgeGraph` instance or a raw NetworkX
        DiGraph.
    entities:
        Seed concept labels.
    max_hops:
        Maximum BFS depth from each seed.
    max_relations:
        Hard cap on the number of relations returned to keep the
        explanation compact.

    Returns
    -------
    list of dict
        Each dict describes a relation: source, target, relation type,
        confidence and whether it is inferred.
    """

    g = _as_nx_graph(graph)
    if g is None:
        return []

    seeds = [e for e in entities if g.has_node(e)]
    if not seeds:
        return []

    relations: List[Dict[str, Any]] = []
    seen_edges: set[Tuple[str, str, str]] = set()

    queue = deque([(s, 0) for s in seeds])
    visited_nodes = set(seeds)

    while queue and len(relations) < max_relations:
        node, depth = queue.popleft()
        if depth >= max_hops:
            continue

        # Look at both outgoing and incoming neighbours for richer context
        neighbours = set(g.successors(node)) | set(g.predecessors(node))

        for nbr in neighbours:
            if len(relations) >= max_relations:
                break

            edge_data = None
            src, tgt = node, nbr
            if g.has_edge(node, nbr):
                edge_data = g.get_edge_data(node, nbr)
            elif g.has_edge(nbr, node):
                edge_data = g.get_edge_data(nbr, node)
                src, tgt = nbr, node

            if not edge_data:
                continue

            rel_type = edge_data.get("relation", "RELATED_TO")
            key = (src, tgt, rel_type)
            if key in seen_edges:
                continue

            seen_edges.add(key)
            relations.append(
                {
                    "source": src,
                    "target": tgt,
                    "relation": rel_type,
                    "confidence": float(edge_data.get("confidence", 0.0)),
                    "inferred": bool(edge_data.get("inferred", False)),
                }
            )

            if nbr not in visited_nodes:
                visited_nodes.add(nbr)
                queue.append((nbr, depth + 1))

    return relations
