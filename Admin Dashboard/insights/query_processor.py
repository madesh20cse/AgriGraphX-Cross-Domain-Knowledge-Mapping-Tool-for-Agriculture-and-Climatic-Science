"""Query processing utilities for the AI Insight Engine.

This module reuses existing NLP utilities (Module 2) to turn a
natural-language question into a small set of key entities plus a
coarse domain label (Agriculture / Climate / DataScience / General).
"""

from __future__ import annotations

from typing import List, Tuple, Optional

from knowledge_graph import KnowledgeGraph
from admin_dashboard import extract_triples_simple
from semantic_search import semantic_search
from utils import clean_text


_DOMAIN_KEYWORDS = {
    "Agriculture": ["crop", "yield", "soil", "fertilizer", "pest", "irrigation", "agriculture", "farmer", "harvest"],
    "Climate": ["climate", "rainfall", "temperature", "humidity", "drought", "flood", "monsoon", "weather"],
    "Data Science": ["model", "dataset", "data", "algorithm", "prediction", "regression", "classification", "machine learning"],
}


def _detect_domain(query: str, entities: List[str]) -> str:
    """Very lightweight domain detection based on keywords.

    This deliberately stays heuristic to avoid coupling to any
    external models; it is only used to slightly tailor the wording of
    recommendations.
    """

    text = (query or "").lower()
    text += " " + " ".join(e.lower() for e in entities)

    scores: dict[str, int] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for kw in keywords if kw in text)

    # Pick the best-scoring domain, fallback to General
    best_domain = max(scores, key=lambda d: scores[d]) if scores else "General"
    return best_domain if scores.get(best_domain, 0) > 0 else "General"


def _entities_from_triples(query: str) -> List[str]:
    """Extract candidate entities from regex-based triples.

    This reuses the same simple triple extractor used elsewhere in the
    application (Module 2) to stay consistent with how concepts are
    detected from text.
    """

    triples = extract_triples_simple(query)
    entities: List[str] = []
    seen = set()
    for t in triples:
        for key in ("subject", "object"):
            ent = t.get(key)
            if ent and ent not in seen:
                seen.add(ent)
                entities.append(ent)
    return entities


def _entities_from_semantic_search(query: str, kg: Optional[KnowledgeGraph]) -> List[str]:
    """Fallback entity extraction by semantic search over KG nodes.

    When the regex-based triple extraction yields nothing (for very
    short or free-form questions), we query the existing semantic
    search engine over the current KnowledgeGraph node labels.
    """

    if kg is None:
        return []

    concepts = kg.nodes()
    if not concepts:
        return []

    # Use a small top-k to keep reasoning compact
    results = semantic_search(query, concepts, top_k=5)
    return [r["concept"] for r in results]


def process_query(query: str, kg: Optional[KnowledgeGraph] = None) -> Tuple[List[str], str]:
    """Extract key entities and a coarse domain from the user query.

    Parameters
    ----------
    query:
        Natural language question from the user.
    kg:
        Optional shared KnowledgeGraph instance; when provided we may
        use semantic search over its nodes as a fallback for entity
        extraction.

    Returns
    -------
    (entities, domain)
        entities: ordered list of distinct concept labels
        domain:  simple string label used by the recommendation engine
    """

    query_clean = clean_text(query or "").strip()
    if not query_clean:
        return [], "General"

    entities = _entities_from_triples(query_clean)

    if not entities:
        entities = _entities_from_semantic_search(query_clean, kg)

    # Always deduplicate while preserving order
    seen = set()
    final_entities: List[str] = []
    for e in entities:
        if e and e not in seen:
            seen.add(e)
            final_entities.append(e)

    domain = _detect_domain(query_clean, final_entities)
    return final_entities, domain
