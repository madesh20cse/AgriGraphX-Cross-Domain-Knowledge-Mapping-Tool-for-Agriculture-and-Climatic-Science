"""Insight generation from graph relations.

Takes a small set of entities and their surrounding relations and
turns them into human-readable explanatory text.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from knowledge_graph import KnowledgeGraph
from .graph_reasoning import find_related_subgraph


_RELATION_VERBS = {
    "IS_A": "is a",
    "SUBCLASS_OF": "is a subclass of",
    "RELATED_TO": "is related to",
    "PART_OF": "is part of",
    "USES": "uses",
    "INCLUDES": "includes",
    "DEVELOPED": "is developed using",
}


def _as_nx_graph(graph: Any):
    if isinstance(graph, KnowledgeGraph):
        return graph.graph
    return graph


def _format_relation_sentence(rel: Dict[str, Any]) -> str:
    src = rel.get("source", "?")
    tgt = rel.get("target", "?")
    rel_type = rel.get("relation", "RELATED_TO")
    conf = rel.get("confidence", 0.0)

    verb = _RELATION_VERBS.get(rel_type, "is related to")
    return f"{src} {verb} {tgt} (confidence {conf:.2f})."


def generate_insights(
    graph: Any,
    entities: Iterable[str],
    relations: List[Dict[str, Any]] | None = None,
) -> Tuple[str, List[Dict[str, Any]]]:
    """Convert graph relationships into a concise explanation.

    Parameters
    ----------
    graph:
        KnowledgeGraph or raw NetworkX graph. Currently only used if
        `relations` is None.
    entities:
        Seed concept labels derived from the query.
    relations:
        Pre-computed relations from :func:`find_related_subgraph`. If
        omitted, this function will call it internally.
    """

    entities = [e for e in entities if e]
    if not entities:
        return "No entities could be extracted from the query.", []

    if relations is None:
        relations = find_related_subgraph(graph, entities)

    if not relations:
        return (
            "No strong relationships for these concepts were found in the current knowledge graph.",
            [],
        )

    # Build a short narrative from relations
    sentences = [_format_relation_sentence(r) for r in relations]

    unique_entities = sorted(set(entities))
    entity_list = ", ".join(unique_entities)

    header = (
        f"For the concepts {entity_list}, the knowledge graph encodes the "
        "following key relationships:\n\n"
    )

    bullet_lines = [f"- {s}" for s in sentences]
    insight_text = header + "\n".join(bullet_lines)

    return insight_text, relations
