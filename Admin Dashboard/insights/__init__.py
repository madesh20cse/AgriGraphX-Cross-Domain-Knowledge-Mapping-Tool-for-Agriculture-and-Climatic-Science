"""AI Insight & Recommendation Engine package.

Provides a thin orchestration layer that wires together:
- query processing
- graph reasoning over the KnowledgeGraph
- insight text generation
- recommendation generation

This module is intentionally lightweight so it does not modify or
couple tightly to existing Modules 1–6; it only *consumes* the
already-built KnowledgeGraph and utilities.
"""

from __future__ import annotations

from typing import Any, Dict

from knowledge_graph import KnowledgeGraph

from .query_processor import process_query
from .graph_reasoning import find_related_subgraph
from .insight_engine import generate_insights
from .recommendation_engine import generate_recommendations


def run_insight_pipeline(query: str, kg: KnowledgeGraph) -> Dict[str, Any]:
    """End-to-end AI insight pipeline.

    Parameters
    ----------
    query:
        Natural language question from the user.
    kg:
        The shared :class:`KnowledgeGraph` instance (Module 3).

    Returns
    -------
    dict
        Dictionary with the original query, generated insight text,
        list of recommendations, and supporting relations extracted
        from the graph.
    """
    if not query or not isinstance(query, str):
        return {
            "query": query,
            "insights": "",
            "recommendations": [],
            "supporting_relations": [],
        }

    entities, domain = process_query(query, kg)

    subgraph_relations = find_related_subgraph(kg, entities)

    insight_text, relations = generate_insights(kg, entities, subgraph_relations)

    recommendations = generate_recommendations(
        insight_text,
        domain=domain,
        entities=entities,
    )

    return {
        "query": query,
        "insights": insight_text,
        "recommendations": recommendations,
        "supporting_relations": relations,
    }
