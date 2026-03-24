"""
dataset_selection_ui.py — Module 1: Dataset Selection & Ingestion Interface

Implements the dataset ingestion system as per Module 1 requirements:
- Support for multiple data sources (uploads, Wikipedia, News)
- Dataset categorization (Agriculture, Climate, Data Science)
- Preprocessing and validation
- Dataset storage for NLP processing

Architecture:
    Streamlit UI → Dataset Selection → Preprocessing → Storage → Ready for Module 2
"""

import streamlit as st
import os
import json
from typing import Tuple, Optional, List, Dict
from connectors import (
    render_file_uploader,
    render_wikipedia_connector,
    render_news_connector,
    render_arxiv_connector,
)
from dataset_manager import SAMPLE_DATASETS
from dataset_preprocessor import DATASET_CATEGORIES, get_category_info


def get_available_dataset_files() -> List[Dict[str, str]]:
    """
    List all generated dataset files (Wikipedia/News) from the data/datasets directory.
    Excludes pre-loaded sample datasets.
    
    Returns:
        List of dictionaries with file information {filename, filepath, metadata_path, size}
    """
    try:
        datasets_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "datasets")
        
        if not os.path.exists(datasets_dir):
            return []
        
        datasets = []
        for file in os.listdir(datasets_dir):
            if file.endswith('.txt') and not file.endswith('_meta.txt'):
                filepath = os.path.join(datasets_dir, file)
                meta_file = filepath.replace('.txt', '_meta.json')
                
                # Only include files with metadata indicating they're generated (Wikipedia/News)
                try:
                    if os.path.exists(meta_file):
                        with open(meta_file, 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        
                        # Only include if source is Wikipedia, News, or Arxiv
                        if meta.get("source") in ["Wikipedia", "News", "Arxiv"]:
                            size = os.path.getsize(filepath)
                            datasets.append({
                                "filename": file,
                                "filepath": filepath,
                                "metadata_path": meta_file,
                                "size": f"{size / 1024:.2f} KB" if size < 1024*1024 else f"{size / 1024 / 1024:.2f} MB"
                            })
                except Exception:
                    # Skip files without valid metadata
                    continue
        
        return sorted(datasets, key=lambda x: x["filename"], reverse=True)
    
    except Exception:
        return []


def render_available_datasets():
    """Display available generated dataset files (Wikipedia/News) with their links and metadata."""
    datasets = get_available_dataset_files()
    
    if datasets:
        st.markdown("### 📁 Available Generated Datasets")
        st.markdown("🔖 Previously generated Wikipedia and News datasets:")
        
        for i, dataset in enumerate(datasets):
            with st.expander(f"📄 {dataset['filename']} ({dataset['size']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.code(f"data/datasets/{dataset['filename']}", language="")
                
                # Load and display metadata if available
                try:
                    if os.path.exists(dataset['metadata_path']):
                        with open(dataset['metadata_path'], 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        
                        st.markdown("**File Information:**")
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Source", meta.get("source", "Unknown"))
                        with col2:
                            st.metric("Size", f"{meta.get('size_chars', 0):,} chars")
                        with col3:
                            st.metric("Words", f"{meta.get('size_words', 0):,}")
                        with col4:
                            st.metric("Created", meta.get("created_at", "Unknown")[:10])
                
                except Exception:
                    pass
    
    else:
        st.info("📭 No generated datasets yet. Create datasets from Wikipedia or News sources first!")


def render_dataset_selection() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Render Module 1 dataset selection & ingestion interface.
    
    Implements dataset ingestion system supporting:
    - File uploads (Agriculture, Climate, Data Science focused)
    - Wikipedia dumps (domain-specific)
    - News sources (domain-specific)
    - Sample datasets (for testing)
    - Previously generated datasets (ready for NLP processing)
    
    Returns:
        Tuple of (success: bool, content: str or None, source: str or None)
    """
    # Header with Module 1 context
    st.markdown("## 📦 Module 1: Dataset Ingestion & Selection")
    st.markdown("✨ **Upload and prepare datasets for cross-domain knowledge mapping** ✨")
    st.markdown("🌾 Agriculture | 🌍 Climate | 📊 Data Science | 🤖 AI Technology")
    st.markdown("---")
    
    # Show available dataset files first
    render_available_datasets()
    st.markdown("---")
    
    # Create categorized tabs
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📤 🌾 Upload Files",
        "🔍 📖 Wikipedia Data",
        "📰 📡 News Sources",
        "📚 ArXiv Research Papers",
        "📚 📑 Samples",
        "✅ 🔄 Load Existing"
    ])
    
    # ────────────────────────────────────────────────────────────────────────
    #  TAB 1: FILE UPLOADER - Direct Dataset Upload
    # ────────────────────────────────────────────────────────────────────────
    with tab1:
        st.markdown("### 📤 🌾 Direct Dataset Upload")
        st.markdown("""
        Upload your own datasets for knowledge extraction:
        - 🌱 **Agricultural data:** Research articles, farming datasets, crop yields
        - 🌍 **Climate data:** Weather reports, climate research, environmental studies
        - 📊 **Data Science:** Analytical datasets, statistical reports
        
        ✅ Supported formats: **CSV, TXT, JSON, JSONL**
        📏 Maximum size: **50MB**
        🤖 Auto-categorization: Dataset type detected automatically
        """)
        
        success, content = render_file_uploader()
        
        if success and content:
            st.session_state.dataset_content = content
            st.session_state.dataset_source = "File Upload"
    
    # ────────────────────────────────────────────────────────────────────────
    #  TAB 2: WIKIPEDIA - Wikipedia Dump Downloads
    # ────────────────────────────────────────────────────────────────────────
    with tab2:
        st.markdown("### � 📖 Wikipedia Data Source")
        st.markdown("""
        Fetch domain-specific Wikipedia articles and dumps:
        - 🔎 Search for specific topics
        - 📚 Fetch domain-related article collections
        - 🔗 Combine multiple articles into unified datasets
        
        ✨ **Supported Domains:** 🌾 Agriculture | 🌍 Climate | 🤖 AI Technology | 📊 Data Science
        """)
        
        success, content = render_wikipedia_connector()
        
        if success and content:
            st.session_state.dataset_content = content
            st.session_state.dataset_source = "Wikipedia"
    
    # ────────────────────────────────────────────────────────────────────────
    #  TAB 3: NEWS - News Archive Integration
    # ────────────────────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### 📰 📡 News Archive Integration")
        st.markdown("""
        Fetch news articles and archives by domain:
        - 🌾 Agriculture news and research updates
        - 🌍 Climate and environmental news
        - 🤖 AI and Data Science breakthroughs
        
        ⚡ **Ready for:** Real-time knowledge integration and trend analysis
        """)
        
        success, content = render_news_connector()
        
        if success and content:
            st.session_state.dataset_content = content
            st.session_state.dataset_source = "News"

    # ────────────────────────────────────────────────────────────────────────
    #  TAB 4: ARXIV - Research Papers from ArXiv
    # ────────────────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("### 📚 ArXiv Research Papers")
        st.markdown(
            """
            Fetch research paper abstracts from **ArXiv** and combine them
            into a unified text dataset for downstream NLP and graph
            construction.
            """
        )

        success, content = render_arxiv_connector()

        if success and content:
            st.session_state.dataset_content = content
            st.session_state.dataset_source = "Arxiv"
    
    # ────────────────────────────────────────────────────────────────────────
    #  TAB 5: SAMPLE DATASETS - Pre-loaded Test Data
    # ────────────────────────────────────────────────────────────────────────
    with tab5:
        st.markdown("### 📚 📑 Sample Datasets")
        st.markdown("🎯 Pre-loaded datasets for testing and demonstration:")
        
        if SAMPLE_DATASETS:
            dataset_names = list(SAMPLE_DATASETS.keys())
            selected_dataset = st.selectbox(
                "🎁 Select Sample Dataset",
                dataset_names,
                help="Choose a pre-loaded sample dataset",
                key="sample_select"
            )
            
            if selected_dataset:
                dataset_data = SAMPLE_DATASETS[selected_dataset]
                
                st.markdown(f"📂 **Domain:** {dataset_data.get('domain', 'N/A')}")
                st.markdown(f"📄 **Documents:** {len(dataset_data.get('documents', []))}")
                
                # Show sample documents
                documents = dataset_data.get('documents', [])
                with st.expander(f"Preview ({len(documents)} items)", expanded=False):
                    for i, doc in enumerate(documents[:5], 1):
                        st.text(f"{i}. {doc}")
                    if len(documents) > 5:
                        st.info(f"... and {len(documents) - 5} more items")
                
                # Use dataset button
                if st.button("📥 Use This Dataset", type="primary", key="sample_dataset_btn"):
                    content = "\n".join(documents)
                    st.session_state.dataset_content = content
                    st.session_state.dataset_source = selected_dataset
                    st.success(f"✅ Dataset '{selected_dataset}' selected!")
        else:
            st.warning("⚠️ No sample datasets available.")
    
    # ────────────────────────────────────────────────────────────────────────
    #  TAB 6: LOAD EXISTING - Previously Generated Datasets
    # ────────────────────────────────────────────────────────────────────────
    with tab6:
        st.markdown("### ✅ 🔄 Load Previously Generated Datasets")
        st.markdown("♻️ Reload datasets you've previously created from Wikipedia or News sources.")
        
        datasets = get_available_dataset_files()
        
        if datasets:
            dataset_files = {f['filename']: f for f in datasets}
            selected_file = st.selectbox(
                "🗂️ Select Dataset",
                list(dataset_files.keys()),
                help="Choose a previously generated dataset",
                key="existing_select"
            )
            
            if selected_file:
                dataset_info = dataset_files[selected_file]
                
                # Read metadata
                try:
                    if os.path.exists(dataset_info['metadata_path']):
                        with open(dataset_info['metadata_path'], 'r', encoding='utf-8') as f:
                            meta = json.load(f)
                        
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.metric("Source", meta.get("source", "Unknown"))
                        with col2:
                            st.metric("Size", f"{meta.get('size_chars', 0):,} chars")
                        with col3:
                            st.metric("Words", f"{meta.get('size_words', 0):,}")
                        with col4:
                            st.metric("Created", meta.get("created_at", "Unknown")[:10])
                except Exception:
                    st.metric("Path", dataset_info['filepath'])
                
                # Preview button
                if st.button("📥 Load This Dataset", type="primary", key="load_existing_btn"):
                    try:
                        with open(dataset_info['filepath'], 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        st.session_state.dataset_content = content
                        st.session_state.dataset_source = f"Loaded from {selected_file}"
                        st.success(f"✅ Dataset loaded successfully!")
                    except Exception as e:
                        st.error(f"❌ Error loading dataset: {str(e)}")
        else:
            st.info("📭 No previously generated datasets found. Create some datasets from Wikipedia or News first!")
    
    # Return based on session state
    if "dataset_content" in st.session_state and st.session_state.dataset_content:
        return True, st.session_state.dataset_content, st.session_state.get("dataset_source", "Unknown")
    
    return False, None, None


def render_dataset_summary():
    """
    Render summary of selected dataset.
    
    Returns:
        bool: True if dataset is selected, False otherwise
    """
    if "dataset_content" in st.session_state and st.session_state.dataset_content:
        st.markdown("---")
        st.markdown("### 📋 Selected Dataset Summary")
        
        content = st.session_state.dataset_content
        source = st.session_state.get("dataset_source", "Unknown")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Source", source)
        
        with col2:
            st.metric("Content Length", f"{len(content):,} chars")
        
        with col3:
            words = len(content.split())
            st.metric("Estimated Words", f"{words:,}")
        
        # Preview button
        with st.expander("View Content Preview"):
            preview_length = min(2000, len(content))
            preview_text = content[:preview_length] + ("..." if len(content) > preview_length else "")
            st.code(preview_text, language="markdown")
        
        return True
    
    return False


def get_selected_dataset() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Get the currently selected dataset.
    
    Returns:
        Tuple of (has_dataset: bool, content: str or None, source: str or None)
    """
    if "dataset_content" in st.session_state and st.session_state.dataset_content:
        return (
            True,
            st.session_state.dataset_content,
            st.session_state.get("dataset_source", "Unknown")
        )
    
    return False, None, None


def initialize_dataset_state():
    """Initialize dataset-related session state variables."""
    if "dataset_content" not in st.session_state:
        st.session_state.dataset_content = None
    if "dataset_source" not in st.session_state:
        st.session_state.dataset_source = None


def reset_dataset_selection():
    """Reset the selected dataset."""
    st.session_state.dataset_content = None
    st.session_state.dataset_source = None
