"""
semantic_search.py — Semantic Search Engine using Sentence Transformers.

Provides embedding-based similarity search over knowledge graph concepts.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from utils import get_logger

logger = get_logger(__name__)

DEFAULT_MODEL = "all-MiniLM-L6-v2"

# Module-level cache
_MODEL = None
_MODEL_NAME: str = ""


def load_model(model_name: str = DEFAULT_MODEL):
    """Lazy-load and cache the SentenceTransformer model."""
    global _MODEL, _MODEL_NAME
    if _MODEL is None or _MODEL_NAME != model_name:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading SentenceTransformer: {model_name}")
        _MODEL = SentenceTransformer(model_name)
        _MODEL_NAME = model_name
        logger.info("Model loaded successfully.")
    return _MODEL


def get_model():
    return load_model()


def encode_concepts(concepts: list[str], model_name: str = DEFAULT_MODEL) -> np.ndarray:
    """Encode concept strings into L2-normalised embedding vectors."""
    model = load_model(model_name)
    embeddings = model.encode(concepts, convert_to_numpy=True, normalize_embeddings=True)
    logger.info(f"Encoded {len(concepts)} concepts → shape {embeddings.shape}")
    return embeddings


def compute_similarity_matrix(concepts: list[str], model_name: str = DEFAULT_MODEL) -> np.ndarray:
    """Compute cosine similarity matrix for all concept pairs."""
    if not concepts:
        return np.array([])
    embeddings = encode_concepts(concepts, model_name)
    sim_matrix = cosine_similarity(embeddings)
    return sim_matrix


def top_k_similar(
    query: str,
    candidates: list[str],
    k: int = 5,
    model_name: str = DEFAULT_MODEL,
    exclude_self: bool = True,
) -> list[dict]:
    """Return top-k concepts most similar to `query` from `candidates`."""
    if not candidates:
        return []

    all_concepts = [query] + [c for c in candidates if c != query]
    embeddings = encode_concepts(all_concepts, model_name)

    query_vec = embeddings[0:1]
    cand_vecs = embeddings[1:]
    cand_labels = all_concepts[1:]

    if cand_vecs.shape[0] == 0:
        return []

    scores = cosine_similarity(query_vec, cand_vecs)[0]

    results = sorted(
        [
            {"concept": label, "similarity": float(score)}
            for label, score in zip(cand_labels, scores)
        ],
        key=lambda x: x["similarity"],
        reverse=True,
    )
    return results[:k]


def pairwise_score(a: str, b: str, model_name: str = DEFAULT_MODEL) -> float:
    """Return the cosine similarity between two concept strings."""
    embeddings = encode_concepts([a, b], model_name)
    score = float(cosine_similarity(embeddings[0:1], embeddings[1:2])[0][0])
    return score


def semantic_search(query: str, concepts: list[str], top_k: int = 10) -> list[dict]:
    """
    Full semantic search: find top-k concepts related to a natural language query.
    Returns list of dicts with concept, similarity score, and rank.
    """
    if not concepts:
        return []

    results = top_k_similar(query, concepts, k=top_k)
    for i, r in enumerate(results):
        r["rank"] = i + 1
    return results
