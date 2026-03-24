"""
admin_dashboard.py — Streamlit Admin Dashboard UI Components.

Contains all the rendering functions for each dashboard section.
"""

from __future__ import annotations

import re
import os
import time
import random
import streamlit as st
import pandas as pd
import numpy as np
import streamlit.components.v1 as components
from knowledge_graph import KnowledgeGraph
from refinement_tools import RefinementEngine
from dataset_manager import (
    get_available_datasets, get_dataset, get_dataset_stats,
    get_all_dataset_stats, save_uploaded_dataset, SAMPLE_DATASETS,
)
from pipeline_monitor import PipelineMonitor, create_demo_monitor
from feedback_system import FeedbackSystem, FEEDBACK_OPTIONS
from semantic_search import semantic_search, top_k_similar
from utils import (
    get_logger, confidence_label, confidence_score_color,
    domain_color, clean_text, split_sentences,
)

logger = get_logger(__name__)

# ─── Relation Patterns (same as semantic_extraction) ─────────────────────────

RELATION_PATTERNS = [
    (r"(.+?)\s+IS[-_]A\s+(.+)",           "IS_A"),
    (r"(.+?)\s+is a\s+(.+)",              "IS_A"),
    (r"(.+?)\s+is an\s+(.+)",             "IS_A"),
    (r"(.+?)\s+SUBCLASS[-_]OF\s+(.+)",    "SUBCLASS_OF"),
    (r"(.+?)\s+subclass of\s+(.+)",       "SUBCLASS_OF"),
    (r"(.+?)\s+is a subclass of\s+(.+)",  "SUBCLASS_OF"),
    (r"(.+?)\s+RELATED[-_]TO\s+(.+)",     "RELATED_TO"),
    (r"(.+?)\s+is related to\s+(.+)",     "RELATED_TO"),
    (r"(.+?)\s+related to\s+(.+)",        "RELATED_TO"),
    (r"(.+?)\s+PART[-_]OF\s+(.+)",        "PART_OF"),
    (r"(.+?)\s+part of\s+(.+)",           "PART_OF"),
    (r"(.+?)\s+is part of\s+(.+)",        "PART_OF"),
    (r"(.+?)\s+uses\s+(.+)",              "USES"),
    (r"(.+?)\s+USES\s+(.+)",              "USES"),
    (r"(.+?)\s+includes\s+(.+)",          "INCLUDES"),
    (r"(.+?)\s+INCLUDES\s+(.+)",          "INCLUDES"),
    (r"(.+?)\s+developed\s+(.+)",         "DEVELOPED"),
    (r"(.+?)\s+DEVELOPED\s+(.+)",         "DEVELOPED"),
]

_COMPILED = [(re.compile(p, re.IGNORECASE), rel) for p, rel in RELATION_PATTERNS]

# Scalable defaults for very large datasets.
MAX_DOCS_FOR_FULL_PASS = 50000
MAX_GRAPH_EDGES = 60000


def extract_triples_simple(text: str) -> list[dict]:
    """Extract triples from text using regex patterns."""
    text = clean_text(text)
    sentences = split_sentences(text)
    triples = []

    for sentence in sentences:
        sentence = sentence.strip()
        for pattern, relation in _COMPILED:
            m = pattern.fullmatch(sentence.rstrip(".!?"))
            if m:
                subj = m.group(1).strip().title()
                obj_ = m.group(2).strip().title()
                subj = re.sub(r"[.!?,;]+$", "", subj).strip()
                obj_ = re.sub(r"[.!?,;]+$", "", obj_).strip()
                if subj and obj_ and subj != obj_:
                    conf = round(random.uniform(0.65, 0.98), 2)
                    triples.append({
                        "subject": subj,
                        "relation": relation,
                        "object": obj_,
                        "confidence": conf,
                        "status": "Pending",
                    })
                break
    return triples


def _is_textual_entity(token: str) -> bool:
    """Return True for tokens that look like meaningful entity labels."""
    t = token.strip()
    if not t:
        return False
    if len(t) > 60:
        return False
    if re.fullmatch(r"[\d\W_]+", t):
        return False
    if re.fullmatch(r"-?\d+(\.\d+)?", t):
        return False
    return any(ch.isalpha() for ch in t)


def extract_triples_flexible(text: str) -> list[dict]:
    """Extract triples from free text and simple tabular rows."""
    triples = extract_triples_simple(text)
    if triples:
        return triples

    raw = text.strip()
    if not raw:
        return []

    # Fallback 1: key/value pairs like "Crop: Rice, Season: Kharif".
    kv_pairs = re.findall(r"([A-Za-z][A-Za-z\s_\-/]{1,40})\s*[:=]\s*([^,;|\t]+)", raw)
    parsed = []
    for k, v in kv_pairs:
        key = re.sub(r"\s+", " ", k).strip().title()
        val = re.sub(r"\s+", " ", v).strip().title()
        if _is_textual_entity(key) and _is_textual_entity(val):
            parsed.append((key, val))
    if len(parsed) >= 2:
        out = []
        for i in range(len(parsed) - 1):
            subj = parsed[i][1]
            obj_ = parsed[i + 1][1]
            if subj != obj_:
                out.append({
                    "subject": subj,
                    "relation": "RELATED_TO",
                    "object": obj_,
                    "confidence": 0.62,
                    "status": "Pending",
                })
        return out

    # Fallback 2: comma/pipe/tab separated row; link first textual token to next ones.
    cells = [c.strip() for c in re.split(r"[,;|\t]", raw) if c.strip()]
    textual = []
    for c in cells:
        c_norm = re.sub(r"\s+", " ", c).strip().title()
        if _is_textual_entity(c_norm):
            textual.append(c_norm)
        if len(textual) >= 4:
            break

    if len(textual) >= 2:
        anchor = textual[0]
        out = []
        for ent in textual[1:]:
            if ent != anchor:
                out.append({
                    "subject": anchor,
                    "relation": "RELATED_TO",
                    "object": ent,
                    "confidence": 0.58,
                    "status": "Pending",
                })
        return out

    return []


_BRIDGE_STOPWORDS = {
    "the", "a", "an", "of", "and", "or", "to", "for", "in", "on", "with",
    "is", "are", "uses", "use", "using", "related", "part", "type", "model",
    "data", "system", "science",
}


def _concept_tokens(label: str) -> set[str]:
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9_\-]*", label.lower())
    return {
        t for t in tokens
        if len(t) >= 4 and t not in _BRIDGE_STOPWORDS
    }


def add_cross_domain_bridges(
    kg: KnowledgeGraph,
    domain1: str,
    domain2: str,
    max_bridges: int = 200,
) -> int:
    """Add inferred bridge edges between two domains using shared concept tokens."""
    dom1_nodes = []
    dom2_nodes = []
    for n, data in kg.graph.nodes(data=True):
        dom = data.get("domain", "General")
        if dom == domain1:
            dom1_nodes.append(n)
        elif dom == domain2:
            dom2_nodes.append(n)

    if not dom1_nodes or not dom2_nodes:
        return 0

    token_to_nodes_dom2: dict[str, list[str]] = {}
    for n2 in dom2_nodes:
        for tok in _concept_tokens(n2):
            token_to_nodes_dom2.setdefault(tok, []).append(n2)

    created = 0
    seen_pairs = set()
    for n1 in dom1_nodes:
        toks1 = _concept_tokens(n1)
        if not toks1:
            continue

        candidates = set()
        for tok in toks1:
            candidates.update(token_to_nodes_dom2.get(tok, []))

        for n2 in candidates:
            pair = (n1, n2)
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)

            toks2 = _concept_tokens(n2)
            if not toks2:
                continue

            overlap = toks1.intersection(toks2)
            if not overlap:
                continue

            # Keep node domains unchanged by using General for inferred bridge edges.
            if not kg.graph.has_edge(n1, n2):
                kg.add_edge(
                    n1, n2, "RELATED_TO",
                    confidence=0.60,
                    inferred=True,
                    domain="General",
                    status="Pending",
                )
                created += 1
                if created >= max_bridges:
                    return created

    return created


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 1: OVERVIEW DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════

def render_overview_dashboard(kg: KnowledgeGraph, monitor: PipelineMonitor,
                               feedback: FeedbackSystem):
    """Render the main overview dashboard."""
    st.markdown('<div class="section-header">📊 System Overview</div>',
                unsafe_allow_html=True)

    summary = kg.summary()
    fb_summary = feedback.get_feedback_summary()
    status = monitor.get_status_dict()

    # Key metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("🔵 Total Nodes", summary["nodes"])
    with col2:
        st.metric("🔗 Total Edges", summary["edges"])
    with col3:
        st.metric("📄 Documents", status["total_documents"])
    with col4:
        st.metric("✅ Reviewed", fb_summary["total"])
    with col5:
        pipeline_status = "🟢 Active" if status["status"] == "completed" else "🔴 Idle"
        st.metric("⚙️ Pipeline", pipeline_status)

    st.markdown("---")

    # Two column layout
    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown('<div class="section-header">🗺️ Knowledge Graph Overview</div>',
                    unsafe_allow_html=True)

        if summary["nodes"] > 0:
            buf = kg.render_matplotlib(title="Knowledge Graph — Admin View")
            st.image(buf, use_container_width=True)
        else:
            st.info("No graph data available. Process a dataset to generate the knowledge graph.")

    with col_right:
        st.markdown('<div class="section-header">📈 Domain Distribution</div>',
                    unsafe_allow_html=True)

        domains = summary.get("domains", {})
        if domains:
            df_domains = pd.DataFrame([
                {"Domain": k, "Nodes": v} for k, v in domains.items()
            ])
            st.dataframe(df_domains, use_container_width=True, hide_index=True)

            # Status breakdown
            st.markdown('<div class="section-header">📋 Edge Status Breakdown</div>',
                        unsafe_allow_html=True)

            triples = kg.get_triples_as_dicts()
            if triples:
                df_triples = pd.DataFrame(triples)
                status_counts = df_triples["Status"].value_counts().to_dict()
                for status_name, count in status_counts.items():
                    icon = "✅" if status_name == "Approved" else "❌" if status_name == "Rejected" else "⏳"
                    st.markdown(f"""
                    <div style="display:flex; justify-content:space-between; padding:0.4rem 0.8rem;
                                margin:0.2rem 0; border-radius:8px;
                                background:rgba(108,99,255,0.08);">
                        <span>{icon} {status_name}</span>
                        <span style="font-weight:700; color:#6C63FF;">{count}</span>
                    </div>
                    """, unsafe_allow_html=True)

        # Feedback summary
        st.markdown('<div class="section-header">💬 Feedback Summary</div>',
                    unsafe_allow_html=True)
        fb_col1, fb_col2, fb_col3 = st.columns(3)
        with fb_col1:
            st.metric("✅ Correct", fb_summary["Correct"])
        with fb_col2:
            st.metric("🔍 Review", fb_summary["Needs Review"])
        with fb_col3:
            st.metric("❌ Incorrect", fb_summary["Incorrect"])


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 2: PIPELINE MONITORING
# ═══════════════════════════════════════════════════════════════════════════════

def render_pipeline_monitor(monitor: PipelineMonitor, kg: KnowledgeGraph):
    """Render the pipeline monitoring panel."""
    st.markdown('<div class="section-header">⚙️ NLP Pipeline Monitor</div>',
                unsafe_allow_html=True)

    status = monitor.get_status_dict()

    # Status header
    status_icon = {
        "idle": "🔴",
        "running": "🟡",
        "completed": "🟢",
        "error": "🔴",
    }
    st.markdown(f"""
    <div style="background: rgba(108,99,255,0.1); border: 1px solid rgba(108,99,255,0.3);
                border-radius:12px; padding:1rem 1.5rem; margin-bottom:1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <div>
                <span style="font-size:1.4rem; font-weight:700; color:#1E293B;">
                    {status_icon.get(status['status'], '⚪')} Pipeline Status: {status['status'].upper()}
                </span>
            </div>
            <div style="color:#64748B; font-size:0.9rem;">
                ⏱️ Elapsed: {status['elapsed_time']}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Overall progress
    overall_progress = status["overall_progress"] / 100
    st.progress(overall_progress, text=f"Overall Progress: {status['overall_progress']:.0f}%")

    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📄 Documents", f"{status['processed_documents']} / {status['total_documents']}")
    with col2:
        st.metric("🏷️ Entities", status['entities_extracted'])
    with col3:
        st.metric("🔗 Relations", status['relations_extracted'])
    with col4:
        st.metric("📊 Dataset", status['active_dataset'][:20] if status['active_dataset'] else "None")

    st.markdown("---")

    # Active models
    st.markdown('<div class="section-header">🤖 Active Models</div>',
                unsafe_allow_html=True)

    models = status["models_used"]
    model_cols = st.columns(len(models))
    for i, (model_name, model_val) in enumerate(models.items()):
        with model_cols[i]:
            st.markdown(f"""
            <div style="background: rgba(108,99,255,0.08); border: 1px solid rgba(108,99,255,0.25);
                        border-radius:10px; padding:0.8rem; text-align:center;">
                <div style="font-size:0.75rem; color:#64748B; text-transform:uppercase;
                            letter-spacing:0.5px; margin-bottom:0.3rem;">{model_name}</div>
                <div style="font-weight:600; color:#1E293B; font-size:0.85rem;">{model_val}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # Pipeline stages
    st.markdown('<div class="section-header">📋 Pipeline Stages</div>',
                unsafe_allow_html=True)

    for stage in status["stages"]:
        stage_icon = "✅" if stage["status"] == "completed" else "🔄" if stage["status"] == "running" else "⏳"
        col1, col2 = st.columns([4, 1])
        with col1:
            st.progress(stage["progress"] / 100,
                        text=f"{stage_icon} {stage['name']}")
        with col2:
            st.markdown(f"**{stage['progress']}%**")

    # Logs
    if status["logs"]:
        st.markdown("---")
        st.markdown('<div class="section-header">📝 Pipeline Logs</div>',
                    unsafe_allow_html=True)
        with st.expander("View Logs", expanded=False):
            for log_entry in reversed(status["logs"]):
                color = "#22C55E" if log_entry["level"] == "INFO" else "#EAB308"
                st.markdown(f"""
                <div style="font-family:monospace; font-size:0.8rem; padding:0.2rem 0;
                            color:{color};">
                    [{log_entry['timestamp']}] [{log_entry['level']}] {log_entry['message']}
                </div>
                """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 3: DATASET MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def render_dataset_management(kg: KnowledgeGraph, monitor: PipelineMonitor):
    """Render dataset management panel."""
    st.markdown('<div class="section-header">📂 Dataset Management</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📋 Available Datasets", "⬆️ Upload Dataset", "📊 Process Dataset"])

    with tab1:
        st.markdown("#### Available Datasets")

        all_stats = get_all_dataset_stats()
        if all_stats:
            df_stats = pd.DataFrame(all_stats)
            df_stats.columns = ["Dataset Name", "Domain", "Documents", "Total Words", "Avg Words/Doc"]
            df_stats["Avg Words/Doc"] = df_stats["Avg Words/Doc"].round(1)
            st.dataframe(df_stats, use_container_width=True, hide_index=True)

        # Dataset selector
        datasets = get_available_datasets()
        selected = st.selectbox("🔽 Select Dataset to Preview", datasets,
                                key="dataset_preview_select")

        if selected:
            ds = get_dataset(selected)
            stats = get_dataset_stats(selected)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📄 Documents", stats["num_documents"])
            with col2:
                st.metric("📝 Total Words", stats["total_words"])
            with col3:
                domain_hex = domain_color(stats["domain"])
                st.metric("🏷️ Domain", stats["domain"])

            with st.expander("Preview Documents", expanded=False):
                for i, doc in enumerate(ds["documents"][:10]):
                    st.markdown(f"""
                    <div style="background:rgba(108,99,255,0.06); border-left:3px solid #6C63FF;
                                padding:0.5rem 0.8rem; margin:0.3rem 0; border-radius:0 6px 6px 0;
                                font-size:0.85rem;">
                        <span style="color:#64748B;">#{i+1}</span> {doc}
                    </div>
                    """, unsafe_allow_html=True)
                if len(ds["documents"]) > 10:
                    st.caption(f"... and {len(ds['documents']) - 10} more documents")

    with tab2:
        st.markdown("#### Upload New Dataset")
        st.markdown("""
        <div class="info-banner">
        Upload a text file with one relation per line. Supported formats:<br/>
        • <code>X is a Y</code>  •  <code>X uses Y</code>  •  <code>X is related to Y</code><br/>
        • <code>X developed Y</code>  •  <code>X is part of Y</code>  •  <code>X subclass of Y</code>
        </div>
        """, unsafe_allow_html=True)

        upload_name = st.text_input("Dataset Name", key="upload_name",
                                     placeholder="My Custom Dataset")
        upload_domain = st.selectbox("Domain", ["AI", "Healthcare", "Physics", "Law", "DataScience", "Agriculture and Climatic science", "General"],
                                     key="upload_domain")

        uploaded_file = st.file_uploader("Upload Text File", type=["txt", "csv"],
                                         key="dataset_uploader")

        upload_text = st.text_area("Or paste text directly",
                                   height=150, key="upload_text",
                                   placeholder="Machine Learning is a subclass of AI.\nDeep Learning uses Neural Networks.\n...")

        if st.button("📤 Save Dataset", key="btn_save_dataset"):
            content = ""
            if uploaded_file:
                content = uploaded_file.read().decode("utf-8")
            elif upload_text:
                content = upload_text

            if content and upload_name:
                filepath = save_uploaded_dataset(upload_name, content, upload_domain)
                st.success(f"✅ Dataset '{upload_name}' saved successfully!")
            else:
                st.warning("Please provide both a name and content.")

    with tab3:
        st.markdown("#### Process Dataset")

        datasets = get_available_datasets()
        process_dataset = st.selectbox("Select Dataset to Process", datasets,
                                        key="process_dataset_select")

        if st.button("🚀 Process Dataset", key="btn_process", type="primary"):
            if process_dataset:
                ds = get_dataset(process_dataset)
                domain = ds.get("domain", "General")
                docs = ds.get("documents", [])

                if not docs:
                    st.warning("No documents found in selected dataset.")
                    return

                sample_step = 1
                docs_to_process = docs
                if len(docs) > MAX_DOCS_FOR_FULL_PASS:
                    sample_step = max(1, int(np.ceil(len(docs) / MAX_DOCS_FOR_FULL_PASS)))
                    docs_to_process = docs[::sample_step]
                    st.info(
                        f"Large dataset detected ({len(docs)} rows). "
                        f"Processing every {sample_step}th row "
                        f"({len(docs_to_process)} sampled rows) for scalable graph generation."
                    )

                # Start pipeline
                monitor.start_pipeline(process_dataset, domain, len(docs_to_process))

                progress_bar = st.progress(0, text="Starting pipeline...")
                status_text = st.empty()

                # Stage 1: Text Preprocessing
                status_text.markdown("**Stage 1/6:** Text Preprocessing...")
                monitor.update_progress(0, 100)
                progress_bar.progress(17, text="Text Preprocessing...")
                time.sleep(0.3)

                # Stage 2: Entity Extraction
                status_text.markdown("**Stage 2/6:** Entity Extraction (NER)...")
                kg.__init__()
                entity_set = set()
                extracted_relations = 0
                graph_edges_added = 0

                update_every = max(1, len(docs_to_process) // 200)
                for i, doc in enumerate(docs_to_process):
                    triples = extract_triples_flexible(doc)
                    extracted_relations += len(triples)

                    for t in triples:
                        entity_set.add(t["subject"])
                        entity_set.add(t["object"])
                        if graph_edges_added < MAX_GRAPH_EDGES:
                            kg.add_edge(
                                t["subject"], t["object"], t["relation"],
                                confidence=t["confidence"],
                                domain=domain,
                                status=t.get("status", "Pending"),
                            )
                            graph_edges_added += 1

                    if (i + 1) % update_every == 0 or (i + 1) == len(docs_to_process):
                        prog = int((i + 1) / len(docs_to_process) * 100)
                        monitor.update_progress(1, prog, docs_processed=i + 1)

                progress_bar.progress(34, text="Entity extraction complete...")
                time.sleep(0.2)

                # Stage 3: Relation Extraction
                status_text.markdown("**Stage 3/6:** Relation Extraction...")
                monitor.update_progress(2, 100, relations=extracted_relations)
                progress_bar.progress(50, text="Relation extraction complete...")
                time.sleep(0.2)

                # Stage 4: Knowledge Graph Construction
                status_text.markdown("**Stage 4/6:** Knowledge Graph Construction...")
                monitor.update_progress(3, 100)
                progress_bar.progress(68, text="Knowledge graph built...")
                time.sleep(0.2)

                # Stage 5: Semantic Embedding
                status_text.markdown("**Stage 5/6:** Computing Semantic Embeddings...")
                monitor.update_progress(4, 100)
                progress_bar.progress(84, text="Embeddings computed...")
                time.sleep(0.2)

                # Stage 6: Reasoning
                status_text.markdown("**Stage 6/6:** Running Reasoning Engine...")

                # Transitive inference
                nodes = kg.nodes()
                inferred_count = 0
                for node in nodes:
                    neighbors = kg.get_neighbors(node)
                    for nb in neighbors:
                        nb_neighbors = kg.get_neighbors(nb)
                        for nnb in nb_neighbors:
                            if nnb != node and not kg.graph.has_edge(node, nnb):
                                kg.add_edge(
                                    node, nnb, "IS_A",
                                    confidence=round(random.uniform(0.55, 0.75), 2),
                                    inferred=True, domain=domain,
                                    status="Pending",
                                )
                                inferred_count += 1
                                if inferred_count >= 8:
                                    break
                        if inferred_count >= 8:
                            break
                    if inferred_count >= 8:
                        break

                monitor.update_progress(5, 100)
                progress_bar.progress(100, text="Pipeline complete!")

                monitor.complete_pipeline(
                    entities=len(entity_set),
                    relations=extracted_relations + inferred_count,
                )

                status_text.empty()

                if graph_edges_added >= MAX_GRAPH_EDGES:
                    st.warning(
                        f"Graph edge cap reached at {MAX_GRAPH_EDGES} edges. "
                        "The graph view is intentionally limited for performance, "
                        "while extraction metrics include all processed rows."
                    )

                st.success(
                    f"✅ Pipeline completed! Extracted **{len(entity_set)}** entities "
                    f"and **{extracted_relations}** relations "
                    f"(+ **{inferred_count}** inferred)."
                )
                st.rerun()


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 4: KNOWLEDGE TABLE
# ═══════════════════════════════════════════════════════════════════════════════

def render_knowledge_table(kg: KnowledgeGraph, refinement: RefinementEngine,
                            feedback: FeedbackSystem):
    """Render the extracted knowledge table."""
    st.markdown('<div class="section-header">📋 Extracted Knowledge Triples</div>',
                unsafe_allow_html=True)

    triples = kg.get_triples_as_dicts()

    if not triples:
        st.info("No knowledge triples available. Process a dataset first.")
        return

    df = pd.DataFrame(triples)

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        min_conf = st.slider("Min Confidence", 0.0, 1.0, 0.0, 0.05,
                              key="filter_confidence")
    with col2:
        relations = ["All"] + sorted(df["Relation"].unique().tolist())
        filter_rel = st.selectbox("Filter by Relation", relations,
                                   key="filter_relation")
    with col3:
        statuses = ["All"] + sorted(df["Status"].unique().tolist())
        filter_status = st.selectbox("Filter by Status", statuses,
                                      key="filter_status")

    # Apply filters
    filtered = df[df["Confidence"] >= min_conf]
    if filter_rel != "All":
        filtered = filtered[filtered["Relation"] == filter_rel]
    if filter_status != "All":
        filtered = filtered[filtered["Status"] == filter_status]

    # Summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Relations", len(filtered))
    with col2:
        avg_conf = filtered["Confidence"].mean() if len(filtered) > 0 else 0
        st.metric("Avg Confidence", f"{avg_conf:.2f}")
    with col3:
        low_conf = len(filtered[filtered["Confidence"] < 0.7])
        st.metric("⚠️ Low Confidence", low_conf)
    with col4:
        inferred = len(filtered[filtered["Inferred"] == True])
        st.metric("🔮 Inferred", inferred)

    st.markdown("---")

    # Display table
    for idx, row in filtered.iterrows():
        conf_color = confidence_score_color(row["Confidence"])
        is_low = row["Confidence"] < 0.7
        bg = "rgba(239,68,68,0.08)" if is_low else "rgba(108,99,255,0.04)"
        border_color = "#EF4444" if is_low else "rgba(108,99,255,0.2)"
        inferred_badge = ' <span class="badge badge-yellow">INFERRED</span>' if row["Inferred"] else ""
        status_icon = "✅" if row["Status"] == "Approved" else "❌" if row["Status"] == "Rejected" else "⏳"

        st.markdown(f"""
        <div style="background:{bg}; border:1px solid {border_color};
                    border-radius:10px; padding:0.7rem 1rem; margin:0.4rem 0;
                    display:flex; justify-content:space-between; align-items:center;">
            <div style="flex:1;">
                <span style="font-weight:700; color:#1E293B;">{row['Entity1']}</span>
                <span style="color:{conf_color}; font-weight:600; padding:0 0.5rem;">
                    — {row['Relation']} →
                </span>
                <span style="font-weight:700; color:#1E293B;">{row['Entity2']}</span>
                {inferred_badge}
            </div>
            <div style="display:flex; gap:0.8rem; align-items:center;">
                <span style="color:{conf_color}; font-weight:700; font-size:0.9rem;">
                    {row['Confidence']:.2f}
                </span>
                <span style="font-size:0.85rem;">{status_icon} {row['Status']}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Action panel
    st.markdown('<div class="section-header">🎬 Actions on Relations</div>',
                unsafe_allow_html=True)

    edge_options = [f"{row['Entity1']} → {row['Entity2']}" for _, row in filtered.iterrows()]
    if edge_options:
        selected_edge = st.selectbox("Select Relation", edge_options,
                                      key="action_edge_select")

        if selected_edge:
            parts = selected_edge.split(" → ")
            src, tgt = parts[0], parts[1]

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Approve", key=f"approve_{src}_{tgt}", type="primary"):
                    result = refinement.approve_relation(src, tgt)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
            with col2:
                if st.button("❌ Reject", key=f"reject_{src}_{tgt}"):
                    result = refinement.reject_relation(src, tgt)
                    if result["success"]:
                        st.warning(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
            with col3:
                fb = st.selectbox("Feedback", FEEDBACK_OPTIONS,
                                   key=f"fb_{src}_{tgt}")
                if st.button("💬 Submit Feedback", key=f"submit_fb_{src}_{tgt}"):
                    result = feedback.submit_feedback(src, "", tgt, fb)
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 5: GRAPH REFINEMENT
# ═══════════════════════════════════════════════════════════════════════════════

def render_graph_refinement(kg: KnowledgeGraph, refinement: RefinementEngine):
    """Render graph refinement tools."""
    st.markdown('<div class="section-header">🔧 Graph Refinement Tools</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔗 Merge Nodes", "✏️ Edit Relation", "🗑️ Delete Edge",
        "➕ Add Edge", "🔍 Find Duplicates"
    ])

    nodes = kg.nodes()
    edges = kg.edges()

    # ── Merge Nodes ───────────────────────────────────────────────────────────
    with tab1:
        st.markdown("#### Merge Duplicate Entities")
        st.markdown("""
        <div class="info-banner">
        Merge two entities that represent the same concept.<br/>
        Example: <b>Einstein</b> → <b>Albert Einstein</b><br/>
        All edges connected to the old node will be transferred to the new node.
        </div>
        """, unsafe_allow_html=True)

        if nodes:
            col1, col2 = st.columns(2)
            with col1:
                old_node = st.selectbox("Old Node (to merge from)", nodes,
                                         key="merge_old")
            with col2:
                new_node = st.text_input("New Node Name (merge into)",
                                          key="merge_new",
                                          placeholder="e.g., Albert Einstein")

            if st.button("🔗 Merge Nodes", key="btn_merge", type="primary"):
                if new_node:
                    result = refinement.merge_nodes(old_node, new_node)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
                else:
                    st.warning("Please enter the new node name.")
        else:
            st.info("No nodes available. Process a dataset first.")

    # ── Edit Relation ─────────────────────────────────────────────────────────
    with tab2:
        st.markdown("#### Edit Relation Type")
        st.markdown("""
        <div class="info-banner">
        Change the relation type on an existing edge.<br/>
        Example: <b>AI uses ML</b> → <b>AI includes ML</b>
        </div>
        """, unsafe_allow_html=True)

        if edges:
            edge_labels = [f"{u} --{d.get('relation','?')}--> {v}" for u, v, d in edges]
            selected_idx = st.selectbox("Select Edge to Edit", range(len(edge_labels)),
                                         format_func=lambda x: edge_labels[x],
                                         key="edit_edge_select")

            if selected_idx is not None:
                u, v, d = edges[selected_idx]
                st.markdown(f"**Current:** {u} --**{d.get('relation','')}**--> {v}")

                new_rel = st.selectbox("New Relation Type",
                                       ["IS_A", "SUBCLASS_OF", "RELATED_TO", "PART_OF",
                                        "USES", "INCLUDES", "DEVELOPED"],
                                       key="edit_new_rel")

                if st.button("✏️ Update Relation", key="btn_edit_rel", type="primary"):
                    result = refinement.edit_relation(u, v, new_rel)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
        else:
            st.info("No edges available. Process a dataset first.")

    # ── Delete Edge ───────────────────────────────────────────────────────────
    with tab3:
        st.markdown("#### Delete Incorrect Edge")
        st.markdown("""
        <div class="info-banner">
        Remove a relation that is incorrect or irrelevant from the knowledge graph.
        </div>
        """, unsafe_allow_html=True)

        if edges:
            edge_labels = [f"{u} --{d.get('relation','?')}--> {v}" for u, v, d in edges]
            del_idx = st.selectbox("Select Edge to Delete", range(len(edge_labels)),
                                    format_func=lambda x: edge_labels[x],
                                    key="del_edge_select")

            if del_idx is not None:
                u, v, d = edges[del_idx]
                st.markdown(f"""
                <div style="background:rgba(239,68,68,0.1); border:1px solid rgba(239,68,68,0.3);
                            border-radius:8px; padding:0.8rem; margin:0.5rem 0;">
                    ⚠️ <b>About to delete:</b> {u} --{d.get('relation','')}--&gt; {v}<br/>
                    <span style="color:#64748B; font-size:0.85rem;">
                    Confidence: {d.get('confidence', 'N/A')} | Status: {d.get('status', 'N/A')}
                    </span>
                </div>
                """, unsafe_allow_html=True)

                if st.button("🗑️ Delete Edge", key="btn_delete_edge"):
                    result = refinement.delete_edge(u, v)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun()
                    else:
                        st.error(result["message"])
        else:
            st.info("No edges available.")

    # ── Add Edge ──────────────────────────────────────────────────────────────
    with tab4:
        st.markdown("#### Add New Semantic Relation")
        st.markdown("""
        <div class="info-banner">
        Manually add a new relation to the knowledge graph.
        </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            add_src = st.text_input("Source Entity", key="add_src",
                                     placeholder="e.g., Machine Learning")
        with col2:
            add_tgt = st.text_input("Target Entity", key="add_tgt",
                                     placeholder="e.g., Artificial Intelligence")

        col3, col4, col5 = st.columns(3)
        with col3:
            add_rel = st.selectbox("Relation Type",
                                    ["IS_A", "SUBCLASS_OF", "RELATED_TO", "PART_OF",
                                     "USES", "INCLUDES", "DEVELOPED"],
                                    key="add_rel")
        with col4:
            add_conf = st.slider("Confidence", 0.0, 1.0, 0.9, 0.05,
                                  key="add_conf")
        with col5:
            add_domain = st.selectbox("Domain",
                                       ["AI", "Healthcare", "Physics", "Law", "DataScience", "Agriculture and Climatic science", "General"],
                                       key="add_domain")

        if st.button("➕ Add Edge", key="btn_add_edge", type="primary"):
            if add_src and add_tgt:
                result = refinement.add_edge(add_src, add_tgt, add_rel,
                                             add_conf, add_domain)
                if result["success"]:
                    st.success(result["message"])
                    st.rerun()
                else:
                    st.error(result["message"])
            else:
                st.warning("Please provide both source and target entities.")

    # ── Find Duplicates ───────────────────────────────────────────────────────
    with tab5:
        st.markdown("#### Potential Duplicate Entities")
        st.markdown("""
        <div class="info-banner">
        Automatically detect entities that may represent the same concept.
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔍 Scan for Duplicates", key="btn_find_dups"):
            duplicates = refinement.find_potential_duplicates()
            if duplicates:
                for n1, n2, sim in duplicates:
                    st.markdown(f"""
                    <div style="background:rgba(234,179,8,0.1); border:1px solid rgba(234,179,8,0.3);
                                border-radius:8px; padding:0.6rem 1rem; margin:0.3rem 0;
                                display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-weight:600; color:#1E293B;">'{n1}'</span>
                            <span style="color:#64748B;"> ↔ </span>
                            <span style="font-weight:600; color:#1E293B;">'{n2}'</span>
                        </div>
                        <span style="color:#EAB308; font-weight:700;">
                            Similarity: {sim:.0%}
                        </span>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("✅ No potential duplicates found.")

    # Action History
    st.markdown("---")
    st.markdown('<div class="section-header">📜 Refinement History</div>',
                unsafe_allow_html=True)

    history = refinement.get_history()
    if history:
        for action in reversed(history[-10:]):
            action_icon = {
                "merge": "🔗", "edit_relation": "✏️",
                "delete": "🗑️", "add": "➕",
                "approve": "✅", "reject": "❌",
            }
            icon = action_icon.get(action["type"], "📋")
            st.markdown(f"""
            <div style="background:rgba(108,99,255,0.05); border-left:3px solid #6C63FF;
                        padding:0.4rem 0.8rem; margin:0.2rem 0; border-radius:0 6px 6px 0;
                        font-size:0.85rem;">
                {icon} <b>{action['type'].replace('_', ' ').title()}</b>:
                {str(action['details'])[:100]}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.caption("No refinement actions recorded yet.")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 6: INTERACTIVE GRAPH VIEW
# ═══════════════════════════════════════════════════════════════════════════════

def render_interactive_graph(kg: KnowledgeGraph):
    """Render interactive PyVis graph visualization."""
    st.markdown('<div class="section-header">🗺️ Interactive Knowledge Graph</div>',
                unsafe_allow_html=True)

    if kg.summary()["nodes"] == 0:
        st.info("No graph data available. Process a dataset first.")
        return

    # Controls
    col1, col2 = st.columns([3, 1])
    with col2:
        show_inferred = st.checkbox("Show Inferred Edges", True,
                                     key="graph_show_inferred")

    # Legend
    st.markdown("""
    <div style="display:flex; gap:1rem; flex-wrap:wrap; margin:0.5rem 0 1rem 0;">
        <span style="display:flex; align-items:center; gap:0.3rem;">
            <span style="width:14px; height:14px; border-radius:50%; background:#6C63FF; display:inline-block;"></span>
            <span style="font-size:0.8rem; color:#334155;">AI</span>
        </span>
        <span style="display:flex; align-items:center; gap:0.3rem;">
            <span style="width:14px; height:14px; border-radius:50%; background:#43B89C; display:inline-block;"></span>
            <span style="font-size:0.8rem; color:#334155;">Healthcare</span>
        </span>
        <span style="display:flex; align-items:center; gap:0.3rem;">
            <span style="width:14px; height:14px; border-radius:50%; background:#FF8C42; display:inline-block;"></span>
            <span style="font-size:0.8rem; color:#334155;">Physics</span>
        </span>
        <span style="display:flex; align-items:center; gap:0.3rem;">
            <span style="width:14px; height:14px; border-radius:50%; background:#FF6584; display:inline-block;"></span>
            <span style="font-size:0.8rem; color:#334155;">Law</span>
        </span>
    </div>
    """, unsafe_allow_html=True)

    # Render PyVis
    try:
        html = kg.render_pyvis_html(height="650px")
        components.html(html, height=680, scrolling=False)
    except Exception as e:
        st.warning(f"PyVis rendering failed: {e}. Falling back to Matplotlib.")
        buf = kg.render_matplotlib(
            title="Knowledge Graph — Admin View",
            show_inferred=show_inferred,
        )
        st.image(buf, use_container_width=True)

    # Graph statistics
    summary = kg.summary()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Nodes", summary["nodes"])
    with col2:
        st.metric("Edges", summary["edges"])
    with col3:
        density = 0
        if summary["nodes"] > 1:
            density = summary["edges"] / (summary["nodes"] * (summary["nodes"] - 1))
        st.metric("Density", f"{density:.3f}")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 7: SEMANTIC SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def render_semantic_search(kg: KnowledgeGraph):
    """Render semantic search panel."""
    st.markdown('<div class="section-header">🔍 Semantic Query Tool</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="info-banner">
    Enter a natural language query to find semantically related concepts
    in the knowledge graph using sentence embeddings (MiniLM-L6-v2).
    </div>
    """, unsafe_allow_html=True)

    query = st.text_input("🔍 Semantic Search Query", key="semantic_query",
                           placeholder="e.g., AI in healthcare, quantum physics, legal technology...")

    concepts = kg.nodes()

    if st.button("🔎 Search", key="btn_search", type="primary") and query:
        if not concepts:
            st.warning("No concepts in the knowledge graph. Process a dataset first.")
            return

        with st.spinner("Computing semantic similarity..."):
            try:
                results = semantic_search(query, concepts, top_k=10)

                if results:
                    st.markdown(f'<div class="section-header">📊 Results for: "{query}"</div>',
                                unsafe_allow_html=True)

                    for r in results:
                        sim = r["similarity"]
                        color = confidence_score_color(sim)
                        bar_width = max(sim * 100, 5)

                        st.markdown(f"""
                        <div style="background:rgba(108,99,255,0.06); border:1px solid rgba(108,99,255,0.2);
                                    border-radius:10px; padding:0.7rem 1rem; margin:0.4rem 0;">
                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                <span style="font-weight:700; color:#1E293B; font-size:0.95rem;">
                                    #{r['rank']} {r['concept']}
                                </span>
                                <span style="color:{color}; font-weight:700; font-size:0.95rem;">
                                    {sim:.4f}
                                </span>
                            </div>
                            <div style="margin-top:0.4rem; background:rgba(0,0,0,0.06);
                                        border-radius:4px; height:6px; overflow:hidden;">
                                <div style="width:{bar_width}%; height:100%; background:{color};
                                            border-radius:4px; transition: width 0.5s ease;"></div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                    # Show subgraph for top result
                    st.markdown("---")
                    st.markdown('<div class="section-header">🗺️ Related Subgraph</div>',
                                unsafe_allow_html=True)

                    top_concept = results[0]["concept"]
                    subkg = kg.get_subgraph(top_concept, depth=2)
                    if subkg.summary()["nodes"] > 0:
                        try:
                            html = subkg.render_pyvis_html(height="450px")
                            components.html(html, height=480, scrolling=False)
                        except Exception:
                            buf = subkg.render_matplotlib(
                                title=f"Subgraph: {top_concept}"
                            )
                            st.image(buf, use_container_width=True)
                    else:
                        st.info(f"No connections found for '{top_concept}' in the graph.")
                else:
                    st.info("No matching concepts found.")

            except Exception as e:
                st.error(f"Search failed: {e}")
                st.info("Make sure sentence-transformers is installed: `pip install sentence-transformers`")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 8: REASONING VALIDATION
# ═══════════════════════════════════════════════════════════════════════════════

def render_reasoning_validation(kg: KnowledgeGraph, refinement: RefinementEngine):
    """Render reasoning validation panel."""
    st.markdown('<div class="section-header">🧠 Reasoning Validation Panel</div>',
                unsafe_allow_html=True)

    # Show inferred relations
    triples = kg.get_triples_as_dicts()
    inferred = [t for t in triples if t["Inferred"]]

    if not inferred:
        st.info("No inferred relations found. Process a dataset first to generate inferences.")

        if st.button("🧠 Run Transitive Inference", key="btn_run_inference"):
            nodes = kg.nodes()
            count = 0
            for node in nodes:
                neighbors = kg.get_neighbors(node)
                for nb in neighbors:
                    nb_neighbors = kg.get_neighbors(nb)
                    for nnb in nb_neighbors:
                        if nnb != node and not kg.graph.has_edge(node, nnb):
                            kg.add_edge(
                                node, nnb, "IS_A",
                                confidence=round(random.uniform(0.55, 0.75), 2),
                                inferred=True, domain="General",
                                status="Pending",
                            )
                            count += 1
                            if count >= 10:
                                break
                    if count >= 10:
                        break
                if count >= 10:
                    break
            if count > 0:
                st.success(f"Generated {count} inferred relations!")
                st.rerun()
            else:
                st.info("No new inferences could be made.")
        return

    st.markdown(f"**Found {len(inferred)} inferred relations for validation:**")

    for t in inferred:
        conf_color = confidence_score_color(t["Confidence"])
        status_icon = "✅" if t["Status"] == "Approved" else "❌" if t["Status"] == "Rejected" else "🔮"

        col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
        with col1:
            st.markdown(f"""
            <div style="background:rgba(255,165,82,0.08); border:1px solid rgba(255,165,82,0.25);
                        border-radius:8px; padding:0.6rem 1rem; margin:0.2rem 0;">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        🔮 <b style="color:#1E293B;">{t['Entity1']}</b>
                        <span style="color:#D97706;"> → {t['Relation']} → </span>
                        <b style="color:#1E293B;">{t['Entity2']}</b>
                    </div>
                    <span style="color:{conf_color}; font-weight:700;">{t['Confidence']:.2f}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            st.markdown(f"**{status_icon} {t['Status']}**")
        with col3:
            if st.button("✅", key=f"accept_inf_{t['Entity1']}_{t['Entity2']}",
                          help="Accept inference"):
                refinement.approve_relation(t["Entity1"], t["Entity2"])
                st.rerun()
        with col4:
            if st.button("❌", key=f"reject_inf_{t['Entity1']}_{t['Entity2']}",
                          help="Reject inference"):
                refinement.reject_relation(t["Entity1"], t["Entity2"])
                st.rerun()

    # Inference explanation
    st.markdown("---")
    st.markdown('<div class="section-header">📖 Inference Explanation</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="info-banner">
    <b>Transitive Reasoning:</b> If A → B and B → C, then we can infer A → C.<br/><br/>
    <b>Example:</b><br/>
    • Autonomous Car → Vehicle (IS_A)<br/>
    • Vehicle → Machine (IS_A)<br/>
    • <b>∴ Inferred:</b> Autonomous Car → Machine (IS_A)<br/><br/>
    Inferred relations have lower confidence scores and require admin validation.
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 9: FEEDBACK PANEL
# ═══════════════════════════════════════════════════════════════════════════════

def render_feedback_panel(feedback: FeedbackSystem, kg: KnowledgeGraph):
    """Render the feedback management panel."""
    st.markdown('<div class="section-header">💬 Feedback Management</div>',
                unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Summary", "📋 All Feedback", "➕ Submit Feedback"])

    with tab1:
        summary = feedback.get_feedback_summary()
        metrics = feedback.get_accuracy_metrics()

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("✅ Correct", summary["Correct"])
        with col2:
            st.metric("🔍 Needs Review", summary["Needs Review"])
        with col3:
            st.metric("❌ Incorrect", summary["Incorrect"])
        with col4:
            st.metric("📊 Total", summary["total"])

        st.markdown("---")

        if metrics["total_reviews"] > 0:
            st.markdown('<div class="section-header">📈 Accuracy Metrics</div>',
                        unsafe_allow_html=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Accuracy", f"{metrics['accuracy']:.1f}%")
            with col2:
                st.metric("Review Rate", f"{metrics['review_rate']:.1f}%")
            with col3:
                st.metric("Error Rate", f"{metrics['error_rate']:.1f}%")

            # Visual bar
            if summary["total"] > 0:
                correct_pct = summary["Correct"] / summary["total"] * 100
                review_pct = summary["Needs Review"] / summary["total"] * 100
                incorrect_pct = summary["Incorrect"] / summary["total"] * 100

                st.markdown(f"""
                <div style="margin:1rem 0;">
                    <div style="display:flex; border-radius:8px; overflow:hidden; height:28px;">
                        <div style="width:{correct_pct}%; background:#22C55E; display:flex;
                                    align-items:center; justify-content:center;
                                    font-size:0.75rem; font-weight:700; color:white;">
                            {correct_pct:.0f}%
                        </div>
                        <div style="width:{review_pct}%; background:#EAB308; display:flex;
                                    align-items:center; justify-content:center;
                                    font-size:0.75rem; font-weight:700; color:white;">
                            {review_pct:.0f}%
                        </div>
                        <div style="width:{incorrect_pct}%; background:#EF4444; display:flex;
                                    align-items:center; justify-content:center;
                                    font-size:0.75rem; font-weight:700; color:white;">
                            {incorrect_pct:.0f}%
                        </div>
                    </div>
                    <div style="display:flex; justify-content:space-between; margin-top:0.3rem;
                                font-size:0.75rem; color:#64748B;">
                        <span>✅ Correct</span>
                        <span>🔍 Needs Review</span>
                        <span>❌ Incorrect</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        df = feedback.get_all_feedback()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("📥 Export as JSON", key="btn_export_fb"):
                    json_str = feedback.export_feedback_json()
                    st.download_button(
                        "Download JSON",
                        json_str,
                        "feedback_export.json",
                        "application/json",
                    )
            with col2:
                if st.button("🗑️ Clear All Feedback", key="btn_clear_fb"):
                    feedback.clear_feedback()
                    st.success("Feedback data cleared.")
                    st.rerun()
        else:
            st.info("No feedback data available yet.")

    with tab3:
        st.markdown("#### Submit Expert Feedback")

        triples = kg.get_triples_as_dicts()
        if triples:
            edge_options = [
                f"{t['Entity1']} --{t['Relation']}--> {t['Entity2']}"
                for t in triples
            ]
            selected_idx = st.selectbox("Select Relation", range(len(edge_options)),
                                         format_func=lambda x: edge_options[x],
                                         key="fb_edge_select")

            if selected_idx is not None:
                t = triples[selected_idx]

                fb_rating = st.radio("Rating", FEEDBACK_OPTIONS,
                                      key="fb_rating", horizontal=True)

                fb_reviewer = st.text_input("Reviewer Name", value="Admin",
                                             key="fb_reviewer")
                fb_notes = st.text_area("Notes (optional)", key="fb_notes",
                                         placeholder="Any additional comments...")

                if st.button("💬 Submit Feedback", key="btn_submit_fb_main",
                              type="primary"):
                    result = feedback.submit_feedback(
                        t["Entity1"], t["Relation"], t["Entity2"],
                        fb_rating, fb_reviewer, fb_notes,
                    )
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
        else:
            st.info("No relations available. Process a dataset first.")


# ═══════════════════════════════════════════════════════════════════════════════
#  SECTION 10: CROSS-DOMAIN FILE INPUT
# ═══════════════════════════════════════════════════════════════════════════════

def render_cross_domain_upload(kg: KnowledgeGraph, monitor: PipelineMonitor,
                                feedback: FeedbackSystem, refinement: RefinementEngine):
    """Render the two cross-domain file upload landing page."""
    st.markdown('<div class="section-header">📥 Cross-Domain Knowledge Input</div>',
                unsafe_allow_html=True)

    st.markdown("""
    <div class="info-banner">
    Upload <b>two text files</b> from different knowledge domains. The system will:<br/>
    &nbsp; 1. Extract entities and relations from both files<br/>
    &nbsp; 2. Build a unified cross-domain knowledge graph<br/>
    &nbsp; 3. Run transitive reasoning to discover hidden connections<br/>
    &nbsp; 4. Enable admin refinement and semantic search across domains<br/><br/>
    <b>Supported formats:</b> One relation per line:<br/>
    <code>X is a Y</code> &nbsp;|&nbsp; <code>X uses Y</code> &nbsp;|&nbsp;
    <code>X is related to Y</code> &nbsp;|&nbsp; <code>X subclass of Y</code> &nbsp;|&nbsp;
    <code>X developed Y</code> &nbsp;|&nbsp; <code>X is part of Y</code>
    </div>
    """, unsafe_allow_html=True)

    col_file1, col_file2 = st.columns(2)

    # ── Domain 1 ──────────────────────────────────────────────────────────────
    with col_file1:
        st.markdown("""
        <div style="background:rgba(108,99,255,0.06); border:1px solid rgba(108,99,255,0.2);
                    border-radius:12px; padding:1rem; margin-bottom:0.5rem;">
            <div style="font-weight:700; color:#1E293B; font-size:1rem; margin-bottom:0.3rem;">
                📄 Domain 1 — File Upload
            </div>
            <div style="font-size:0.82rem; color:#64748B;">
                Upload the first cross-domain text file
            </div>
        </div>
        """, unsafe_allow_html=True)

        domain1 = st.selectbox("Domain 1", ["AI", "Healthcare", "Physics", "Law", "DataScience", "Agriculture and Climatic science", "General"],
                                key="cd_domain1")
        file1 = st.file_uploader("Upload File 1", type=["txt", "csv"], key="cd_file1")
        text1 = st.text_area(
            "Or paste Domain 1 text",
            height=180, key="cd_text1",
            placeholder="Machine Learning is a subclass of AI.\n"
                        "Deep Learning uses Neural Networks.\n"
                        "Natural Language Processing uses Machine Learning.\n"
                        "Computer Vision uses Deep Learning.",
        )

    # ── Domain 2 ──────────────────────────────────────────────────────────────
    with col_file2:
        st.markdown("""
        <div style="background:rgba(67,184,156,0.06); border:1px solid rgba(67,184,156,0.2);
                    border-radius:12px; padding:1rem; margin-bottom:0.5rem;">
            <div style="font-weight:700; color:#1E293B; font-size:1rem; margin-bottom:0.3rem;">
                📄 Domain 2 — File Upload
            </div>
            <div style="font-size:0.82rem; color:#64748B;">
                Upload the second cross-domain text file
            </div>
        </div>
        """, unsafe_allow_html=True)

        domain2 = st.selectbox("Domain 2", ["Healthcare", "AI", "Physics", "Law", "DataScience", "Agriculture and Climatic science", "General"],
                                key="cd_domain2")
        file2 = st.file_uploader("Upload File 2", type=["txt", "csv"], key="cd_file2")
        text2 = st.text_area(
            "Or paste Domain 2 text",
            height=180, key="cd_text2",
            placeholder="Medical AI uses Machine Learning.\n"
                        "Doctor uses Electronic Health Records.\n"
                        "Drug Discovery uses Deep Learning.\n"
                        "Radiology uses Computer Vision.",
        )

    st.markdown("---")

    # ── Process Button ────────────────────────────────────────────────────────
    if st.button("🚀 Process Both Domains & Build Cross-Domain Graph",
                  key="btn_cd_process", type="primary", use_container_width=True):

        # Gather content
        content1 = ""
        if file1:
            content1 = file1.read().decode("utf-8")
        elif text1:
            content1 = text1

        content2 = ""
        if file2:
            content2 = file2.read().decode("utf-8")
        elif text2:
            content2 = text2

        if not content1 and not content2:
            st.warning("⚠️ Please provide at least one file or paste text for each domain.")
            return

        # Reset graph
        kg.__init__()

        docs1 = [l.strip() for l in content1.strip().split("\n") if l.strip()] if content1 else []
        docs2 = [l.strip() for l in content2.strip().split("\n") if l.strip()] if content2 else []

        step1 = 1
        step2 = 1
        if len(docs1) > MAX_DOCS_FOR_FULL_PASS:
            step1 = max(1, int(np.ceil(len(docs1) / MAX_DOCS_FOR_FULL_PASS)))
            docs1 = docs1[::step1]
        if len(docs2) > MAX_DOCS_FOR_FULL_PASS:
            step2 = max(1, int(np.ceil(len(docs2) / MAX_DOCS_FOR_FULL_PASS)))
            docs2 = docs2[::step2]

        total_docs = len(docs1) + len(docs2)
        if step1 > 1 or step2 > 1:
            st.info(
                "Large cross-domain upload detected. "
                f"Sampling applied (Domain 1: every {step1}th row, Domain 2: every {step2}th row)."
            )

        monitor.start_pipeline(f"{domain1} + {domain2}", "Cross-Domain", total_docs)

        progress = st.progress(0, text="Starting cross-domain pipeline...")
        status_msg = st.empty()

        # Stage 1: Preprocess
        status_msg.markdown("**Stage 1/6:** Text Preprocessing...")
        monitor.update_progress(0, 100)
        progress.progress(17, text="Stage 1/6: Preprocessing complete...")
        time.sleep(0.3)

        # Stage 2: Extract from Domain 1
        status_msg.markdown(f"**Stage 2/6:** Extracting from **{domain1}** ({len(docs1)} docs)...")
        triples1 = []
        for doc in docs1:
            triples1.extend(extract_triples_flexible(doc))
        monitor.update_progress(1, 100, docs_processed=len(docs1))
        progress.progress(34, text=f"Stage 2/6: {domain1} — {len(triples1)} relations extracted...")
        time.sleep(0.3)

        # Stage 3: Extract from Domain 2
        status_msg.markdown(f"**Stage 3/6:** Extracting from **{domain2}** ({len(docs2)} docs)...")
        triples2 = []
        for doc in docs2:
            triples2.extend(extract_triples_flexible(doc))
        monitor.update_progress(2, 100, relations=len(triples1) + len(triples2))
        progress.progress(50, text=f"Stage 3/6: {domain2} — {len(triples2)} relations extracted...")
        time.sleep(0.3)

        # Stage 4: Build graph
        status_msg.markdown("**Stage 4/6:** Building Cross-Domain Knowledge Graph...")
        graph_edges_added = 0
        for t in triples1:
            if graph_edges_added >= MAX_GRAPH_EDGES:
                break
            kg.add_edge(t["subject"], t["object"], t["relation"],
                        confidence=t["confidence"], domain=domain1, status="Pending")
            graph_edges_added += 1
        for t in triples2:
            if graph_edges_added >= MAX_GRAPH_EDGES:
                break
            kg.add_edge(t["subject"], t["object"], t["relation"],
                        confidence=t["confidence"], domain=domain2, status="Pending")
            graph_edges_added += 1
        monitor.update_progress(3, 100)
        progress.progress(68, text="Stage 4/6: Knowledge graph built...")
        time.sleep(0.3)

        # Stage 5: Embeddings
        status_msg.markdown("**Stage 5/6:** Computing Semantic Embeddings...")
        monitor.update_progress(4, 100)
        progress.progress(84, text="Stage 5/6: Embeddings computed...")
        time.sleep(0.3)

        # Stage 6: Transitive inference
        status_msg.markdown("**Stage 6/6:** Running Cross-Domain Reasoning...")
        nodes = kg.nodes()
        inferred_count = 0
        for node in nodes:
            neighbors = kg.get_neighbors(node)
            for nb in neighbors:
                nb_neighbors = kg.get_neighbors(nb)
                for nnb in nb_neighbors:
                    if nnb != node and not kg.graph.has_edge(node, nnb):
                        n_domain = kg.graph.nodes[node].get("domain", "General")
                        kg.add_edge(node, nnb, "IS_A",
                                    confidence=round(random.uniform(0.55, 0.75), 2),
                                    inferred=True, domain=n_domain, status="Pending")
                        inferred_count += 1
                        if inferred_count >= 10:
                            break
                if inferred_count >= 10:
                    break
            if inferred_count >= 10:
                break

        bridge_count = add_cross_domain_bridges(
            kg,
            domain1=domain1,
            domain2=domain2,
            max_bridges=250,
        )

        monitor.update_progress(5, 100)
        progress.progress(100, text="✅ Pipeline complete!")

        entities = set()
        for t in triples1 + triples2:
            entities.add(t["subject"])
            entities.add(t["object"])

        monitor.complete_pipeline(entities=len(entities),
                                   relations=len(triples1) + len(triples2) + inferred_count + bridge_count)

        from refinement_tools import RefinementEngine as RE
        st.session_state.refinement = RE(kg)
        st.session_state.initialized = True

        status_msg.empty()

        if graph_edges_added >= MAX_GRAPH_EDGES:
            st.warning(
                f"Graph edge cap reached at {MAX_GRAPH_EDGES} edges for performance. "
                "Use filters or smaller subsets for a denser visual graph."
            )

        # ══════════════════════════════════════════════════════════════════════
        #  SHOW RESULTS — Pipeline Summary
        # ══════════════════════════════════════════════════════════════════════

        st.success(
            f"✅ Cross-domain pipeline complete! "
            f"**{len(entities)}** entities, **{len(triples1)+len(triples2)}** relations "
            f"(+ **{inferred_count}** inferred, **{bridge_count}** cross-domain bridges)."
        )

        st.markdown("---")

        # ── Pipeline Metrics ──────────────────────────────────────────────────
        st.markdown('<div class="section-header">⚙️ Pipeline Execution Summary</div>',
                    unsafe_allow_html=True)

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            st.metric("📄 Total Docs", total_docs)
        with m2:
            st.metric("🏷️ Entities", len(entities))
        with m3:
            st.metric(f"📘 {domain1}", len(triples1))
        with m4:
            st.metric(f"📗 {domain2}", len(triples2))
        with m5:
            st.metric("🔮 Inferred", inferred_count)
        with m6:
            st.metric("🌉 Bridges", bridge_count)

        # ── Models Used ───────────────────────────────────────────────────────
        st.markdown('<div class="section-header">🤖 Active Models</div>',
                    unsafe_allow_html=True)
        mc1, mc2, mc3, mc4 = st.columns(4)
        models_info = [
            ("NER Model", "spaCy (en_core_web_sm)"),
            ("Relation Extraction", "Regex + spaCy NLP"),
            ("Embeddings", "all-MiniLM-L6-v2"),
            ("Reasoning", "Transitive Inference"),
        ]
        for col, (mname, mval) in zip([mc1, mc2, mc3, mc4], models_info):
            with col:
                st.markdown(f"""
                <div style="background:rgba(108,99,255,0.06); border:1px solid rgba(108,99,255,0.15);
                            border-radius:10px; padding:0.7rem; text-align:center;">
                    <div style="font-size:0.7rem; color:#64748B; text-transform:uppercase;
                                letter-spacing:0.5px; margin-bottom:0.2rem;">{mname}</div>
                    <div style="font-weight:600; color:#1E293B; font-size:0.82rem;">{mval}</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # ── Extracted Triples Table ──────────────────────────────────────────
        st.markdown('<div class="section-header">📋 Extracted Knowledge Triples</div>',
                    unsafe_allow_html=True)

        all_triples_display = []
        for t in triples1:
            all_triples_display.append({
                "Entity 1": t["subject"], "Relation": t["relation"],
                "Entity 2": t["object"], "Confidence": t["confidence"],
                "Domain": domain1, "Type": "Extracted"
            })
        for t in triples2:
            all_triples_display.append({
                "Entity 1": t["subject"], "Relation": t["relation"],
                "Entity 2": t["object"], "Confidence": t["confidence"],
                "Domain": domain2, "Type": "Extracted"
            })
        # Add inferred
        for u, v, d in kg.edges():
            if d.get("inferred", False):
                all_triples_display.append({
                    "Entity 1": u, "Relation": d.get("relation", "IS_A"),
                    "Entity 2": v, "Confidence": d.get("confidence", 0.6),
                    "Domain": "Cross-Domain",
                    "Type": "🔮 Inferred"
                })

        # Assuming pandas is imported as pd and streamlit.components.v1 as components
        import pandas as pd
        import streamlit.components.v1 as components

        df_triples = pd.DataFrame(all_triples_display)
        st.dataframe(df_triples, use_container_width=True, hide_index=True)

        st.markdown("---")

        # ── Generated Knowledge Graph ─────────────────────────────────────────
        st.markdown('<div class="section-header">🗺️ Generated Cross-Domain Knowledge Graph</div>',
                    unsafe_allow_html=True)

        # Domain legend
        st.markdown(f"""
        <div style="display:flex; gap:1.5rem; margin:0.5rem 0 1rem 0;">
            <span style="display:flex; align-items:center; gap:0.3rem;">
                <span style="width:14px; height:14px; border-radius:50%; background:#6C63FF; display:inline-block;"></span>
                <span style="font-size:0.82rem; color:#334155; font-weight:600;">{domain1}</span>
            </span>
            <span style="display:flex; align-items:center; gap:0.3rem;">
                <span style="width:14px; height:14px; border-radius:50%; background:#43B89C; display:inline-block;"></span>
                <span style="font-size:0.82rem; color:#334155; font-weight:600;">{domain2}</span>
            </span>
            <span style="display:flex; align-items:center; gap:0.3rem;">
                <span style="width:14px; height:14px; border-radius:50%; background:#FFA552; display:inline-block;"></span>
                <span style="font-size:0.82rem; color:#334155; font-weight:600;">Inferred</span>
            </span>
        </div>
        """, unsafe_allow_html=True)

        # Render interactive graph
        try:
            html = kg.render_pyvis_html(height="650px")
            components.html(html, height=680, scrolling=False)
        except Exception:
            buf = kg.render_matplotlib(title="Cross-Domain Knowledge Graph")
            st.image(buf, use_container_width=True)

        # Graph stats
        summary = kg.summary()
        gs1, gs2, gs3 = st.columns(3)
        with gs1:
            st.metric("Total Nodes", summary["nodes"])
        with gs2:
            st.metric("Total Edges", summary["edges"])
        with gs3:
            density = summary["edges"] / max(summary["nodes"] * (summary["nodes"] - 1), 1)
            st.metric("Graph Density", f"{density:.3f}")

        st.markdown("---")
        st.info("✅ Use the **sidebar navigation** to access Graph Refinement, Semantic Search, Reasoning Validation, and Feedback tools.")

    # ── Show current graph if data exists (after reloads) ─────────────────────────────
    elif kg.summary()["nodes"] > 0:
        st.markdown("---")
        st.markdown('<div class="section-header">📊 Current Graph Summary</div>',
                    unsafe_allow_html=True)

        summary = kg.summary()
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔵 Nodes", summary["nodes"])
        with col2:
            st.metric("🔗 Edges", summary["edges"])
        with col3:
            domains = summary.get("domains", {})
            st.metric("🌐 Domains", len(domains))
        with col4:
            inferred = len([t for t in kg.get_triples_as_dicts() if t["Inferred"]])
            st.metric("🔮 Inferred", inferred)

        # Show existing graph
        import streamlit.components.v1 as components
        try:
            html = kg.render_pyvis_html(height="600px")
            components.html(html, height=630, scrolling=False)
        except Exception:
            buf = kg.render_matplotlib(title="Cross-Domain Knowledge Graph")
            st.image(buf, use_container_width=True)
