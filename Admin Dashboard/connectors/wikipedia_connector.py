"""
wikipedia_connector.py — Wikipedia Data Fetcher with Domain-Based Link Fetching

Connects to Wikipedia API to fetch domain-related articles for knowledge graph building.
Used by: Dataset selection UI to provide Wikipedia as a data source.

Features:
- Search for domain-related topics (Agriculture, Climate, AI, etc.)
- Fetch multiple related articles as links
- Combine articles into unified dataset
- Batch processing of domain articles
"""

import wikipedia
import streamlit as st
import os
from datetime import datetime
from typing import Tuple, Optional, List, Dict
from .file_uploader import save_dataset_file


# Domain-specific keywords for fetching related articles
DOMAIN_KEYWORDS = {
    "agriculture": [
        "Agriculture", "Farming", "Crop", "Soil", "Irrigation", 
        "Pesticide", "Herbicide", "Fertilizer", "Corn", "Wheat", 
        "Rice", "Livestock", "Animal husbandry", "Aquaculture", "Horticulture"
    ],
    "climate": [
        "Climate", "Climate change", "Global warming", "Weather", "Atmosphere",
        "Greenhouse gas", "Carbon cycle", "Ozone", "Precipitation", "Drought",
        "Flood", "Temperature", "Sea level", "Ice age", "Weather pattern"
    ],
    "ai_technology": [
        "Artificial intelligence", "Machine learning", "Deep learning", "Neural network",
        "Natural language processing", "Computer vision", "Data science", "Algorithm",
        "Python programming", "TensorFlow", "Transformer", "GPT", "BERT", "Automation"
    ],
    "data_science": [
        "Data science", "Statistics", "Data analysis", "Big data", "Data mining",
        "Machine learning", "Regression", "Classification", "Clustering", "Pandas",
        "NumPy", "Scikit-learn", "Data visualization", "Probability", "Database"
    ]
}


def fetch_wikipedia_article(query: str) -> Tuple[bool, str, Optional[str]]:
    """
    Fetch Wikipedia article summary and content.
    
    Args:
        query: Search query for Wikipedia
        
    Returns:
        Tuple of (success: bool, content: str, error_message: str or None)
    """
    try:
        # Search for article
        results = wikipedia.search(query, results=1)
        
        if not results:
            return False, "", f"No Wikipedia articles found for '{query}'"
        
        # Get article
        article_title = results[0]
        article = wikipedia.page(article_title)
        
        # Fetch full content
        content = f"Title: {article.title}\n\n"
        content += f"Summary:\n{article.summary}\n\n"
        content += f"Content:\n{article.content}"
        
        return True, content, None
        
    except wikipedia.exceptions.DisambiguationError as e:
        options = ", ".join(e.options[:5])  # Show first 5 options
        return False, "", f"Disambiguation: Did you mean: {options}?"
    
    except wikipedia.exceptions.PageError:
        return False, "", f"Page '{query}' not found on Wikipedia."
    
    except Exception as e:
        return False, "", f"Error fetching from Wikipedia: {str(e)}"


def search_wikipedia(query: str, results: int = 5) -> List[str]:
    """
    Search for Wikipedia articles.
    
    Args:
        query: Search query
        results: Number of results to return
        
    Returns:
        List of article titles
    """
    try:
        return wikipedia.search(query, results=results)
    except Exception:
        return []


def fetch_domain_articles(domain: str, num_articles: int = 5) -> Dict[str, Tuple[bool, str]]:
    """
    Fetch multiple Wikipedia articles related to a domain.
    
    Args:
        domain: Domain name (agriculture, climate, ai_technology, etc.)
        num_articles: Number of articles to fetch per keyword
        
    Returns:
        Dictionary: {article_title: (success, content)}
    """
    domain_lower = domain.lower().replace(" ", "_")
    keywords = DOMAIN_KEYWORDS.get(domain_lower, [domain])
    
    articles_data = {}
    
    for keyword in keywords:
        try:
            success, content, error = fetch_wikipedia_article(keyword)
            if success:
                articles_data[keyword] = (True, content)
                # Limit total articles
                if len(articles_data) >= num_articles:
                    break
        except Exception:
            continue
    
    return articles_data


def combine_articles_content(articles_dict: Dict[str, str]) -> str:
    """
    Combine multiple Wikipedia articles into unified text format.
    
    Args:
        articles_dict: Dictionary of {title: content}
        
    Returns:
        Combined content as unified text
    """
    combined = f"{'='*80}\n"
    combined += f"DOMAIN DATASET - {len(articles_dict)} ARTICLES COMBINED\n"
    combined += f"{'='*80}\n\n"
    
    for i, (title, content) in enumerate(articles_dict.items(), 1):
        combined += f"\n{'─'*80}\n"
        combined += f"ARTICLE {i}/{len(articles_dict)}: {title}\n"
        combined += f"{'─'*80}\n"
        combined += f"{content}\n"
    
    return combined


def render_wikipedia_connector():
    """
    Render Streamlit UI for Wikipedia connector with domain-based article fetching.
    
    Returns:
        Tuple of (success: bool, content: str or None)
    """
    st.markdown("### 📖 Wikipedia Data Source - Domain Articles")
    st.markdown("🔍 Fetch multiple domain-related Wikipedia articles to build rich datasets.")
    
    # Tab selection: Search or Domain
    tab1, tab2 = st.tabs(["🔍 📄 Search Articles", "📚 🎯 Domain Articles"])
    
    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 1: CUSTOM SEARCH
    # ─────────────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("#### 🔍 Search for Specific Articles")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_query = st.text_input(
                "Wikipedia Search Query",
                placeholder="e.g., Agriculture, Machine Learning, Climate Change",
                help="Enter a topic to search",
                key="wiki_search"
            )
        
        with col2:
            max_results = st.number_input(
                "Max Results",
                min_value=1,
                max_value=10,
                value=5,
                help="Number of search results to display",
                key="wiki_max_results"
            )
        
        if search_query:
            with st.spinner("🔍 Searching Wikipedia..."):
                results = search_wikipedia(search_query, max_results)
            
            if results:
                st.markdown(f"**Found {len(results)} results:**")
                
                # Multi-select articles
                selected_articles = st.multiselect(
                    "Select Articles (can choose multiple)",
                    results,
                    key="wiki_multiselect",
                    help="Choose one or multiple articles"
                )
                
                if selected_articles:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("📥 Fetch Selected Articles", type="primary", key="wiki_fetch_selected"):
                            with st.spinner(f"📥 Fetching {len(selected_articles)} article(s)..."):
                                articles_dict = {}
                                for article_title in selected_articles:
                                    success, content, error = fetch_wikipedia_article(article_title)
                                    if success:
                                        articles_dict[article_title] = content
                                
                                if articles_dict:
                                    combined_content = combine_articles_content(articles_dict)
                                    st.success(f"✅ Successfully fetched {len(articles_dict)} article(s)!")
                                    
                                    # Save dataset file
                                    dataset_name = f"Wikipedia_{search_query.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                                    success_save, file_path, error = save_dataset_file(
                                        combined_content, 
                                        dataset_name, 
                                        "Wikipedia",
                                        metadata={"search_query": search_query, "articles_count": len(articles_dict)}
                                    )
                                    
                                    # Show file link if saved successfully
                                    if success_save:
                                        st.info(f"✅ Dataset saved to: `data/datasets/{os.path.basename(file_path)}`")
                                    else:
                                        st.warning(f"⚠️ Could not save file: {error}")
                                    
                                    with st.expander("Preview Combined Content", expanded=False):
                                        preview_text = combined_content[:1500] + "..." if len(combined_content) > 1500 else combined_content
                                        st.code(preview_text, language="markdown")
                                    
                                    return True, combined_content
                                else:
                                    st.error("❌ Failed to fetch any articles.")
                    
                    with col2:
                        if st.button("ℹ️ Show Metadata", key="wiki_metadata"):
                            st.info("📊 Fetching metadata for selected articles...")
                            for article in selected_articles:
                                metadata = get_wikipedia_metadata(article)
                                if metadata:
                                    st.json(metadata)
            else:
                st.info("No results found. Try a different search query.")
    
    # ─────────────────────────────────────────────────────────────────────────
    #  TAB 2: DOMAIN-BASED ARTICLES
    # ─────────────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("#### Fetch Domain-Related Articles")
        st.markdown("Select a domain to automatically fetch related Wikipedia articles.")
        
        # Domain selector
        available_domains = list(DOMAIN_KEYWORDS.keys())
        selected_domain = st.selectbox(
            "Select Domain",
            available_domains,
            format_func=lambda x: x.replace("_", " ").title(),
            key="wiki_domain_select",
            help="Choose a domain to fetch related articles"
        )
        
        # Number of articles
        num_articles = st.slider(
            "Number of Articles to Fetch",
            min_value=2,
            max_value=15,
            value=5,
            step=1,
            help="How many related articles to combine"
        )
        
        # Display domain keywords
        domain_keys = DOMAIN_KEYWORDS.get(selected_domain, [])
        with st.expander(f"📋 Keywords for '{selected_domain.replace('_', ' ').title()}'"):
            st.write(", ".join(domain_keys[:10]))
            if len(domain_keys) > 10:
                st.caption(f"... and {len(domain_keys) - 10} more keywords")
        
        # Fetch button
        if st.button("🚀 Fetch Domain Articles", type="primary", key="wiki_fetch_domain"):
            with st.spinner(f"📥 Fetching {num_articles} articles for {selected_domain}..."):
                articles_dict = {}
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Fetch articles
                keywords = DOMAIN_KEYWORDS.get(selected_domain, [selected_domain])
                for idx, keyword in enumerate(keywords):
                    if len(articles_dict) >= num_articles:
                        break
                    
                    try:
                        success, content, error = fetch_wikipedia_article(keyword)
                        if success:
                            articles_dict[keyword] = content
                            progress = min((idx + 1) / num_articles, 1.0)
                            progress_bar.progress(progress)
                            status_text.text(f"✅ Fetched {len(articles_dict)}/{num_articles} articles")
                    except Exception as e:
                        status_text.text(f"⏭️ Skipping '{keyword}'...")
                        continue
                
                if articles_dict:
                    combined_content = combine_articles_content(articles_dict)
                    st.success(f"✅ Successfully fetched {len(articles_dict)} article(s) for '{selected_domain}'!")
                    
                    # Save dataset file
                    dataset_name = f"Wikipedia_{selected_domain.replace('_', ' ').title()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    success_save, file_path, error = save_dataset_file(
                        combined_content, 
                        dataset_name, 
                        "Wikipedia",
                        metadata={"domain": selected_domain, "articles_count": len(articles_dict)}
                    )
                    
                    # Statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Articles Combined", len(articles_dict))
                    with col2:
                        st.metric("Total Characters", f"{len(combined_content):,}")
                    with col3:
                        words = len(combined_content.split())
                        st.metric("Estimated Words", f"{words:,}")
                    
                    # Show file link if saved successfully
                    if success_save:
                        st.info(f"✅ Dataset saved to: `data/datasets/{os.path.basename(file_path)}`")
                        with st.expander("📁 View File Information"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.write(f"**File:** {os.path.basename(file_path)}")
                                st.write(f"**Size:** {len(combined_content.encode('utf-8')) / 1024:.2f} KB")
                            with col2:
                                st.write(f"**Metadata:** {os.path.basename(file_path.replace('.txt', '_meta.json'))}")
                    else:
                        st.warning(f"⚠️ Could not save file: {error}")
                    
                    # Preview
                    with st.expander("Preview Combined Content", expanded=True):
                        preview_text = combined_content[:2000] + "..." if len(combined_content) > 2000 else combined_content
                        st.code(preview_text, language="markdown")
                    
                    # Articles list
                    with st.expander("📄 Articles Included"):
                        for i, article_title in enumerate(articles_dict.keys(), 1):
                            st.write(f"{i}. **{article_title}**")
                    
                    return True, combined_content
                else:
                    st.error(f"❌ Failed to fetch articles for domain: {selected_domain}")
    
    return False, None


def get_wikipedia_metadata(title: str) -> dict:
    """
    Get metadata about a Wikipedia article.
    
    Returns:
        Dictionary with article metadata
    """
    try:
        article = wikipedia.page(title)
        return {
            "title": article.title,
            "url": article.url,
            "length": len(article.content),
            "links_count": len(article.links),
            "references_count": len(article.references)
        }
    except Exception:
        return {}
