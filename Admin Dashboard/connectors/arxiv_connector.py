"""
arxiv_connector.py — ArXiv Research Papers Data Connector

Provides a thin wrapper around the `arxiv` Python library and a
Streamlit UI block for fetching research paper abstracts as plain text.

Design goals:
- Keep output as a single cleaned text block (for NLP pipeline)
- Mirror patterns from wikipedia_connector / news_connector
- Save generated datasets under data/datasets with metadata
"""

from __future__ import annotations

from typing import Tuple, Optional
from datetime import datetime
import os

import streamlit as st

try:  # Optional dependency; handled gracefully in the UI
    import arxiv  # type: ignore
    _ARXIV_AVAILABLE = True
except Exception:  # pragma: no cover - runtime import guard
    arxiv = None  # type: ignore
    _ARXIV_AVAILABLE = False

from .file_uploader import save_dataset_file


def _detect_domain_from_query(query: str) -> str:
    """Infer a coarse domain label from the user query.

    Returns one of: "Agriculture", "Climate", "Data Science", "General".
    """
    q = (query or "").lower()

    if any(k in q for k in ["crop", "agriculture", "farmer", "soil", "irrigation"]):
        return "Agriculture"
    if any(k in q for k in ["climate", "weather", "rainfall", "temperature"]):
        return "Climate"
    if any(k in q for k in ["machine learning", "ml ", "ai", "artificial intelligence", "deep learning"]):
        return "Data Science"
    return "General"


def fetch_arxiv_papers(query: str, max_results: int) -> str:
    """Fetch ArXiv papers and return a single combined text block.

    Args:
        query: Free-text search query (e.g., "climate change agriculture").
        max_results: Maximum number of papers to fetch (1–10 recommended).

    Returns:
        Combined plain-text string containing titles and abstracts, e.g.::

            "Title: ... Abstract: ... Title: ... Abstract: ..."

    Notes:
        - Uses `arxiv.Search` sorted by relevance.
        - If the ArXiv library is not installed or an error occurs, this
          function returns an empty string; the UI layer is responsible
          for surfacing the error to the user.
    """
    if not query or not isinstance(max_results, int) or max_results <= 0:
        return ""

    if not _ARXIV_AVAILABLE:
        # Caller (UI) will typically show a helpful error message.
        return ""

    try:
        search = arxiv.Search(  # type: ignore[attr-defined]
            query=query,
            max_results=max_results,
            sort_by=getattr(arxiv, "SortCriterion", None).Relevance  # type: ignore
            if hasattr(arxiv, "SortCriterion")
            else None,
        )

        blocks = []
        # The API exposes an iterator via `.results()` for v1/v2.
        for i, result in enumerate(search.results()):  # type: ignore[call-arg]
            if i >= max_results:
                break
            title = getattr(result, "title", "").replace("\n", " ").strip()
            summary = getattr(result, "summary", "").replace("\n", " ").strip()
            if not title and not summary:
                continue
            # Each paper on its own block with line breaks
            blocks.append(f"Title: {title}\nAbstract: {summary}\n")

        return "\n".join(blocks).strip()
    except Exception:
        # Fail gracefully; UI will handle empty string as failure.
        return ""


def render_arxiv_connector() -> Tuple[bool, Optional[str]]:
    """Render Streamlit UI for the ArXiv research papers connector.

    Returns:
        Tuple of (success: bool, content: str or None)
    """
    st.markdown("### 📚 ArXiv Research Papers")
    st.markdown(
        """
        Search and fetch research paper abstracts from **ArXiv**.
        The results are combined into a single text block ready for
        NLP processing and knowledge graph extraction.
        """
    )

    if not _ARXIV_AVAILABLE:
        st.error(
            "The `arxiv` Python package is not installed. "
            "Please add `arxiv` to requirements.txt and reinstall dependencies."
        )
        return False, None

    col1, col2 = st.columns([3, 1])

    with col1:
        query = st.text_input(
            "Search Query",
            value="climate change agriculture",
            help="Enter a topic or combination of keywords",
            key="arxiv_query",
        )

    with col2:
        max_results = st.number_input(
            "# Papers",
            min_value=1,
            max_value=10,
            value=3,
            step=1,
            help="Number of ArXiv papers to fetch (1–10)",
            key="arxiv_max_results",
        )

    fetched_content: Optional[str] = None

    if st.button("📥 Fetch ArXiv Data", type="primary", key="arxiv_fetch_btn"):
        if not query.strip():
            st.warning("Please enter a search query for ArXiv.")
            return False, None

        with st.spinner("Querying ArXiv and collecting abstracts..."):
            text = fetch_arxiv_papers(query.strip(), int(max_results))

        if not text:
            st.error("No results returned from ArXiv or an error occurred.")
            return False, None

        fetched_content = text
        domain = _detect_domain_from_query(query)
        num_papers = text.count("Title:") or int(max_results)
        num_chars = len(text)
        num_words = len(text.split())

        # Standardised metadata payload for this dataset
        dataset_payload = {
            "source": "arxiv",  # canonical source id
            "domain": domain.lower(),
            "content": text,
        }

        st.success(
            f"✅ Fetched approximately {num_papers} paper(s) from ArXiv "
            f"for domain **{domain}**."
        )

        # Show basic stats
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Papers Fetched", num_papers)
        with c2:
            st.metric("Characters", f"{num_chars:,}")
        with c3:
            st.metric("Words", f"{num_words:,}")

        # Preview combined content
        with st.expander("Preview Combined ArXiv Content", expanded=False):
            preview = text[:2000] + ("..." if len(text) > 2000 else "")
            st.code(preview, language="markdown")

        # Save to datasets directory so it participates in the normal pipeline.
        dataset_name = f"Arxiv_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        success_save, file_path, error = save_dataset_file(
            text,
            dataset_name,
            source="Arxiv",
            metadata={
                "source_id": "arxiv",
                "domain": domain,
                "query": query,
                "papers_requested": int(max_results),
                "papers_estimated": num_papers,
                "payload_schema": "{source:str, domain:str, content:str}",
                "payload_example": dataset_payload,
            },
        )

        if success_save:
            rel_name = os.path.basename(file_path)
            st.info(f"✅ Dataset saved to: data/datasets/{rel_name}")
        else:
            st.warning(f"⚠️ Could not save ArXiv dataset: {error}")

        return True, text

    return False, None
