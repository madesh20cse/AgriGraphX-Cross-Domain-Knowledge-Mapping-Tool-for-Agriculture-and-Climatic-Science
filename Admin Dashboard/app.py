"""
app.py — KnowMap Admin Dashboard & Graph Refinement System
          Module 5 · Hybrid Semantic Intelligence Engine

Streamlit-based Admin Control Panel for:
  • NLP Pipeline Monitoring
  • Dataset Management
  • Knowledge Graph Refinement
  • Semantic Search
  • Reasoning Validation
  • Expert Feedback Collection
"""

import streamlit as st
import pandas as pd
import numpy as np
import random
from datetime import datetime
from typing import Optional

from knowledge_graph import KnowledgeGraph
from refinement_tools import RefinementEngine
from pipeline_monitor import PipelineMonitor, create_demo_monitor
from feedback_system import FeedbackSystem
from dataset_manager import get_dataset, SAMPLE_DATASETS
from insights import run_insight_pipeline
from admin_dashboard import (
    render_overview_dashboard,
    render_pipeline_monitor,
    render_dataset_management,
    render_knowledge_table,
    render_graph_refinement,
    render_interactive_graph,
    render_semantic_search,
    render_reasoning_validation,
    render_feedback_panel,
    render_cross_domain_upload,
    extract_triples_simple,
)

# ─── NEW MODULE 1: AUTHENTICATION & DATASET SELECTION ─────────────────────────
from auth import initialize_session_state, is_authenticated, render_auth_page, render_user_info
from auth.user_profile import get_user, update_user
from dataset_selection_ui import (
    initialize_dataset_state,
    render_dataset_selection,
    render_dataset_summary,
    get_selected_dataset,
)

# ═══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ═══════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="AgriGraphX Cross Domain Knowledge Mapping Tool for Agriculture And Climatic Intelligence",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ═══════════════════════════════════════════════════════════════════════════════
#  GLOBAL CSS — Professional Light Theme
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
/* ── CSS Variables — Green & White Theme ── */
:root {
    --bg-primary:     #F5FBFD;
    --bg-secondary:   #FFFFFF;
    --bg-card:        rgba(255, 255, 255, 0.98);
    --accent:         #10B981;
    --accent-light:   rgba(16, 185, 129, 0.1);
    --accent-glow:    rgba(16, 185, 129, 0.2);
    --accent-dark:    #059669;
    --success:        #10B981;
    --warning:        #F59E0B;
    --danger:         #EF4444;
    --text-primary:   #064E3B;
    --text-secondary: #047857;
    --text-muted:     #6B7280;
    --border:         rgba(16, 185, 129, 0.15);
    --shadow:         0 2px 8px rgba(16, 185, 129, 0.08), 0 1px 3px rgba(16, 185, 129, 0.06);
    --shadow-md:      0 8px 16px rgba(16, 185, 129, 0.12), 0 2px 6px rgba(16, 185, 129, 0.08);
    --shadow-lg:      0 12px 24px rgba(16, 185, 129, 0.15);
}

/* ── Main container ── */
.stApp {
    background: linear-gradient(135deg, #F5FBFD 0%, #ECFDF5 25%, #F0FDF4 50%, #ECFDF5 75%, #F5FBFD 100%);
    color: var(--text-primary);
}
.block-container {
    padding: 1.5rem 2.5rem 2.5rem 2.5rem;
    max-width: 1400px;
}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #FFFFFF 0%, #F0FDF4 100%);
    border-right: 2px solid rgba(16, 185, 129, 0.2);
}
section[data-testid="stSidebar"] * { color: var(--text-primary) !important; }

/* ── Metric cards ── */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.95));
    border: 2px solid var(--border);
    border-radius: 14px;
    padding: 1.2rem 1.5rem;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

div[data-testid="metric-container"]:nth-child(1) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(236, 253, 245, 0.95));
    border-color: rgba(16, 185, 129, 0.3);
}

div[data-testid="metric-container"]:nth-child(2) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.95));
    border-color: rgba(52, 211, 153, 0.3);
}

div[data-testid="metric-container"]:nth-child(3) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(230, 253, 245, 0.95));
    border-color: rgba(110, 231, 183, 0.3);
}

div[data-testid="metric-container"]:nth-child(4) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(207, 250, 254, 0.95));
    border-color: rgba(34, 211, 238, 0.3);
}

div[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #10B981, #34D399, #6EE7B7);
}

div[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-4px);
    background: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(240, 253, 244, 0.98));
}

div[data-testid="stMetricValue"] {
    font-weight: 900;
    color: var(--accent) !important;
    font-size: 2rem !important;
}

div[data-testid="stMetricLabel"] {
    color: var(--text-secondary) !important;
    font-weight: 700;
    font-size: 0.85rem;
}

/* ── Buttons ── */
.stButton > button {
    border-radius: 10px;
    font-weight: 700;
    letter-spacing: 0.5px;
    transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
    border: 2px solid rgba(16, 185, 129, 0.3);
    background: rgba(16, 185, 129, 0.08);
    color: var(--accent);
    position: relative;
    overflow: hidden;
}

.stButton > button::before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: rgba(16, 185, 129, 0.1);
    transition: left 0.35s ease;
    z-index: -1;
}

.stButton > button:hover::before {
    left: 0;
}

.stButton > button:hover {
    background: rgba(16, 185, 129, 0.1);
    border-color: var(--accent);
    box-shadow: 0 6px 20px rgba(16, 185, 129, 0.3);
    transform: translateY(-2px);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
    border: none;
    color: white !important;
    box-shadow: var(--shadow-md);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #059669 0%, #10B981 100%);
    box-shadow: var(--shadow-lg);
    transform: translateY(-3px);
}

/* ── Button Variants ── */
.stButton:nth-child(odd) > button {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(52, 211, 153, 0.06));
}

.stButton:nth-child(odd) > button:hover {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(52, 211, 153, 0.12));
    box-shadow: 0 8px 24px rgba(16, 185, 129, 0.25);
}

.stButton:nth-child(even) > button {
    background: linear-gradient(135deg, rgba(52, 211, 153, 0.12), rgba(6, 182, 212, 0.08));
    border-color: rgba(52, 211, 153, 0.4);
    color: #047857;
}

.stButton:nth-child(even) > button:hover {
    background: linear-gradient(135deg, rgba(52, 211, 153, 0.2), rgba(6, 182, 212, 0.15));
    border-color: #34D399;
    box-shadow: 0 8px 24px rgba(52, 211, 153, 0.2);
}

/* ── DataFrames ── */
div[data-testid="stDataFrame"] {
    border: 2px solid var(--border);
    border-radius: 14px;
    overflow: hidden;
    box-shadow: var(--shadow);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.95));
}

div[data-testid="stDataFrame"]:hover {
    box-shadow: var(--shadow-md);
}

/* ── Expander ── */
div[data-testid="stExpander"] {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.95));
    border: 2px solid var(--border);
    border-radius: 12px;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}

div[data-testid="stExpander"]:nth-child(1) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(236, 253, 245, 0.95));
    border-color: rgba(16, 185, 129, 0.25);
}

div[data-testid="stExpander"]:nth-child(2) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.95));
    border-color: rgba(52, 211, 153, 0.25);
}

div[data-testid="stExpander"]:nth-child(3) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(230, 253, 245, 0.95));
    border-color: rgba(110, 231, 183, 0.25);
}

div[data-testid="stExpander"]:nth-child(4) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(207, 250, 254, 0.95));
    border-color: rgba(34, 211, 238, 0.25);
}

div[data-testid="stExpander"]:nth-child(5) {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 249, 255, 0.95));
    border-color: rgba(59, 130, 246, 0.25);
}

div[data-testid="stExpander"]:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    border-color: var(--accent);
}

/* ── Tabs ── */
div[data-testid="stTabs"] button {
    font-weight: 700;
    color: var(--text-muted) !important;
    border-radius: 10px 10px 0 0;
    transition: all 0.3s ease;
    position: relative;
}

div[data-testid="stTabs"] button:hover {
    background: rgba(16, 185, 129, 0.08);
}

div[data-testid="stTabs"] button[aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 4px solid var(--accent) !important;
    box-shadow: 0 -2px 8px rgba(16, 185, 129, 0.15);
}

/* ── Text Inputs ── */
.stTextInput > div > div {
    border-radius: 10px;
    border: 2px solid var(--border);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(240, 253, 244, 0.98));
    color: var(--text-primary);
    transition: all 0.3s ease;
}

.stTextInput > div > div:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
    background: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(236, 253, 245, 0.99));
}

.stTextInput input {
    color: var(--text-primary) !important;
}

.stTextArea > div > div {
    border-radius: 10px;
    border: 2px solid var(--border);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(240, 253, 244, 0.98));
    transition: all 0.3s ease;
}

.stTextArea > div > div:focus-within {
    border-color: var(--accent);
    box-shadow: 0 0 0 4px rgba(16, 185, 129, 0.15);
    background: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(236, 253, 245, 0.99));
}

.stTextArea textarea {
    color: var(--text-primary) !important;
}

/* ── Select boxes ── */
.stSelectbox > div > div {
    border-radius: 10px;
    border: 2px solid var(--border);
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.99), rgba(240, 253, 244, 0.98));
    color: var(--text-primary);
    transition: all 0.3s ease;
}

.stSelectbox > div > div:hover {
    border-color: var(--accent);
    background: linear-gradient(135deg, rgba(255, 255, 255, 1), rgba(236, 253, 245, 0.99));
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}

/* ── Section headers ── */
.section-header {
    padding: 0.6rem 0 0.5rem 1rem;
    border-left: 4px solid var(--accent);
    border-radius: 0 12px 12px 0;
    margin: 1.5rem 0 1rem 0;
    font-size: 1.15rem;
    font-weight: 800;
    color: var(--text-primary);
    background: linear-gradient(90deg, rgba(16, 185, 129, 0.08), transparent);
}

/* ── Info banners ── */
.info-banner {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(52, 211, 153, 0.05));
    border-left: 4px solid var(--accent);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.9rem;
    color: var(--text-secondary);
    margin: 0.8rem 0;
    box-shadow: var(--shadow);
}

/* ── Badge ── */
.badge {
    display: inline-block;
    padding: 0.25rem 0.8rem;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.4px;
    margin-left: 0.6rem;
    transition: all 0.3s ease;
}

.badge-green  { background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(52, 211, 153, 0.1)); color: #059669; border: 1.5px solid rgba(16, 185, 129, 0.4); }
.badge-red    { background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(220, 38, 38, 0.1)); color: #DC2626; border: 1.5px solid rgba(239, 68, 68, 0.4); }
.badge-yellow { background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(217, 119, 6, 0.1)); color: #B45309; border: 1.5px solid rgba(245, 158, 11, 0.4); }
.badge-blue   { background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(37, 99, 235, 0.1)); color: #2563EB; border: 1.5px solid rgba(59, 130, 246, 0.4); }

/* ── Custom Content Boxes ── */
.box-success {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(52, 211, 153, 0.05));
    border: 2px solid rgba(16, 185, 129, 0.3);
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(16, 185, 129, 0.1);
}

.box-info {
    background: linear-gradient(135deg, rgba(59, 130, 246, 0.08), rgba(96, 165, 250, 0.05));
    border: 2px solid rgba(59, 130, 246, 0.3);
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.box-warning {
    background: linear-gradient(135deg, rgba(245, 158, 11, 0.08), rgba(251, 191, 36, 0.05));
    border: 2px solid rgba(245, 158, 11, 0.3);
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(245, 158, 11, 0.1);
}

.box-error {
    background: linear-gradient(135deg, rgba(239, 68, 68, 0.08), rgba(248, 113, 113, 0.05));
    border: 2px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.1);
}

.box-primary {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(52, 211, 153, 0.08));
    border: 2px solid rgba(16, 185, 129, 0.4);
    border-radius: 12px;
    padding: 1.2rem;
    box-shadow: 0 6px 16px rgba(16, 185, 129, 0.15);
}

.box-gradient-1 {
    background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(16, 185, 129, 0.05));
    border: 2px solid rgba(34, 197, 94, 0.3);
    border-radius: 12px;
    padding: 1.2rem;
}

.box-gradient-2 {
    background: linear-gradient(135deg, rgba(6, 182, 212, 0.1), rgba(34, 211, 238, 0.05));
    border: 2px solid rgba(6, 182, 212, 0.3);
    border-radius: 12px;
    padding: 1.2rem;
}

.box-gradient-3 {
    background: linear-gradient(135deg, rgba(139, 92, 246, 0.1), rgba(168, 85, 247, 0.05));
    border: 2px solid rgba(139, 92, 246, 0.3);
    border-radius: 12px;
    padding: 1.2rem;
}

/* ── Progress bars ── */
.stProgress > div > div > div {
    background: linear-gradient(90deg, #10B981 0%, #34D399 50%, #6EE7B7 100%);
    border-radius: 10px;
}

/* ── Dividers ── */
hr {
    border-color: var(--border);
    opacity: 0.6;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: linear-gradient(180deg, #F0FDF4, #F5FBFD); }
::-webkit-scrollbar-thumb { background: linear-gradient(180deg, #10B981, #34D399); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #059669, #10B981); }

/* ── Hero branding ── */
.hero-header {
    text-align: center;
    padding: 0.5rem 0 1rem 0;
    animation: fadeInDown 0.6s ease-out;
}

.hero-header h1 {
    font-size: 2.2rem;
    font-weight: 900;
    background: linear-gradient(135deg, #10B981, #34D399, #6EE7B7);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem;
    letter-spacing: -0.5px;
}

.hero-header p {
    color: var(--text-secondary);
    font-size: 0.9rem;
    font-weight: 600;
    letter-spacing: 0.3px;
}

@keyframes fadeInDown {
    from {
        opacity: 0;
        transform: translateY(-20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.stCard {
    background: var(--bg-card);
    border: 2px solid var(--border);
    border-radius: 14px;
    padding: 1.5rem;
    box-shadow: var(--shadow);
    transition: all 0.3s ease;
}

.stCard:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-4px);
    border-color: rgba(16, 185, 129, 0.3);
}

/* ── Radio button group ── */
.stRadio > div {
    gap: 0.5rem;
}
.stRadio label {
    color: var(--text-primary) !important;
}

/* ── Checkbox ── */
.stCheckbox > label {
    font-weight: 500;
    color: var(--text-primary) !important;
}

/* ── Slider ── */
.stSlider label {
    color: var(--text-primary) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: linear-gradient(135deg, rgba(236, 253, 245, 0.8) 0%, rgba(240, 253, 244, 0.6) 100%);
    border: 2px dashed rgba(16, 185, 129, 0.4);
    border-radius: 14px;
    padding: 1.5rem;
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"]:hover {
    background: linear-gradient(135deg, rgba(209, 250, 229, 0.9) 0%, rgba(236, 253, 245, 0.8) 100%);
    border-color: #10B981;
    box-shadow: 0 8px 16px rgba(16, 185, 129, 0.15);
    transform: translateY(-2px);
}

[data-testid="stFileUploader"] label {
    color: var(--text-primary) !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
}

[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, #10B981 0%, #34D399 100%) !important;
    color: white !important;
    border: none !important;
    font-weight: 600 !important;
    box-shadow: 0 4px 10px rgba(16, 185, 129, 0.2);
    transition: all 0.3s ease;
}

[data-testid="stFileUploader"] button:hover {
    box-shadow: 0 6px 14px rgba(16, 185, 129, 0.4);
    transform: translateY(-1px);
}

[data-testid="stFileUploader"] small {
    color: var(--text-secondary) !important;
    font-weight: 500;
}

/* ── General text override for visibility ── */
p, span, li, label, .stMarkdown {
    color: var(--text-primary);
}

/* ── Multiselect ── */
.stMultiSelect label {
    color: var(--text-primary) !important;
}
</style>
""", unsafe_allow_html=True)


def render_page_header(
    icon: str,
    title: str,
    module_label: str,
    subtitle: Optional[str] = None,
) -> None:
    """Render a compact, icon-rich header for each module/page."""

    subtitle_html = (
        f"<div style='font-size:0.85rem;color:var(--text-secondary);margin-top:0.15rem;'>{subtitle}</div>"
        if subtitle
        else ""
    )

    st.markdown(
        f"""
        <div class="box-primary" style="margin-top:0.2rem;margin-bottom:0.8rem;
             display:flex;justify-content:space-between;align-items:center;gap:0.85rem;">
            <div>
                <div style="font-size:0.78rem;text-transform:uppercase;letter-spacing:0.14em;
                            color:var(--text-muted);margin-bottom:0.1rem;">
                    {module_label}
                </div>
                <div style="font-size:1.1rem;font-weight:800;color:var(--text-primary);">
                    <span style="margin-right:0.4rem;">{icon}</span>{title}
                </div>
                {subtitle_html}
            </div>
            <div class="badge badge-green">Active Module</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_landing_page() -> None:
    """Render the public marketing-style landing page.

    This page is visible before authentication and routes users
    to the existing login/register screen when they click
    "Get Started" or "Sign In".
    """

    # Landing-specific CSS (removes Streamlit default spacing and header)
    st.markdown(
        """
        <style>
        /* Remove default Streamlit padding so landing starts at the very top */
        .block-container {
            padding-top: 0rem !important;
            padding-bottom: 0rem !important;
            padding-left: 2rem !important;
            padding-right: 2rem !important;
            margin-top: 0 !important;
        }

        /* Remove top header/menu/footer spacing */
        header { visibility: hidden; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }

        /* Remove extra top margin on main section */
        section.main {
            padding-top: 0rem !important;
            margin-top: 0rem !important;
        }

        /* Remove any blank space above first vertical block */
        div[data-testid="stVerticalBlock"] > div:first-child {
            margin-top: 0rem !important;
            padding-top: 0rem !important;
        }

        /* Ensure full-height, zero-margin root for clean landing */
        html, body, [class*="css"] {
            margin: 0;
            padding: 0;
        }

        .landing-wrapper {
            min-height: 100vh;
            padding: 0 2.0rem 2.4rem 2.0rem;
            background: radial-gradient(circle at top left, #dcfce7 0, #ecfdf5 45%, #f9fafb 100%);
        }

        .landing-nav-row {
            padding: 0.65rem 1.2rem;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.95);
            box-shadow: 0 10px 26px rgba(15, 118, 110, 0.15);
            border: 1px solid rgba(16, 185, 129, 0.18);
            margin-bottom: 2.0rem;
        }

        .landing-logo {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-weight: 800;
            font-size: 1.2rem;
            color: #064e3b;
        }

        .landing-logo span.icon {
            font-size: 1.6rem;
        }

        .landing-logo span.text {
            background: linear-gradient(135deg, #10b981, #3b82f6);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.4px;
        }

        .landing-menu {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1.5rem;
            font-size: 0.9rem;
            color: #065f46;
        }

        .landing-menu a {
            text-decoration: none;
            color: #047857;
            font-weight: 600;
        }

        .landing-menu a:hover {
            color: #10b981;
        }

        .landing-hero {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 2.5rem;
            margin-bottom: 3rem;
        }

        .landing-hero-left {
            flex: 1 1 320px;
            max-width: 620px;
        }

        .landing-eyebrow {
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(34, 197, 94, 0.16), rgba(56, 189, 248, 0.18));
            border: 1px solid rgba(34, 197, 94, 0.4);
            font-size: 0.75rem;
            font-weight: 700;
            color: #065f46;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            margin-bottom: 0.9rem;
        }

        .landing-title {
            font-size: clamp(2.2rem, 3.2vw + 1.2rem, 3.1rem);
            line-height: 1.05;
            font-weight: 900;
            color: #052e16;
            margin-bottom: 0.9rem;
        }

        .landing-title span {
            background: linear-gradient(135deg, #16a34a, #10b981, #22c55e);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .landing-subtitle {
            font-size: 1rem;
            max-width: 34rem;
            color: #065f46;
            line-height: 1.6;
            margin-bottom: 1.4rem;
        }

        .landing-pill-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            margin-bottom: 1.4rem;
        }

        .landing-pill {
            padding: 0.3rem 0.8rem;
            border-radius: 999px;
            background: rgba(16, 185, 129, 0.08);
            border: 1px solid rgba(16, 185, 129, 0.28);
            font-size: 0.78rem;
            font-weight: 600;
            color: #047857;
        }

        .landing-hero-right {
            flex: 1 1 280px;
            max-width: 480px;
        }

        .hero-card {
            position: relative;
            border-radius: 1.5rem;
            padding: 1.75rem 1.75rem 1.2rem 1.75rem;
            background: radial-gradient(circle at top left, rgba(59, 130, 246, 0.24), rgba(16, 185, 129, 0.18)),
                        linear-gradient(135deg, #022c22, #052e16);
            box-shadow: 0 24px 55px rgba(6, 95, 70, 0.45);
            color: #ecfdf3;
            overflow: hidden;
        }

        .hero-card::before {
            content: "";
            position: absolute;
            inset: 0;
            background-image: radial-gradient(circle at top right, rgba(45, 212, 191, 0.35), transparent 55%),
                              radial-gradient(circle at bottom left, rgba(59, 130, 246, 0.25), transparent 55%);
            opacity: 0.9;
            pointer-events: none;
        }

        .hero-card-header {
            position: relative;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.3rem;
        }

        .hero-card-title {
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.16em;
            color: #bbf7d0;
            font-weight: 700;
        }

        .hero-chip {
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            background: rgba(22, 163, 74, 0.18);
            border: 1px solid rgba(134, 239, 172, 0.7);
            font-size: 0.72rem;
            font-weight: 600;
        }

        .hero-graph {
            position: relative;
            border-radius: 1.2rem;
            padding: 1.1rem;
            background: radial-gradient(circle at top, rgba(15, 118, 110, 0.6), rgba(6, 78, 59, 0.95));
            border: 1px solid rgba(45, 212, 191, 0.4);
        }

        .hero-graph-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.55rem;
        }

        .hero-node {
            height: 40px;
            border-radius: 999px;
            background: linear-gradient(135deg, rgba(22, 163, 74, 0.95), rgba(34, 197, 94, 0.85));
            box-shadow: 0 10px 20px rgba(22, 163, 74, 0.65);
            border: 1px solid rgba(190, 242, 100, 0.75);
        }

        .hero-node:nth-child(2),
        .hero-node:nth-child(5),
        .hero-node:nth-child(11) {
            background: linear-gradient(135deg, rgba(59, 130, 246, 0.95), rgba(56, 189, 248, 0.9));
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.7);
            border-color: rgba(191, 219, 254, 0.9);
        }

        .hero-stats-row {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            margin-top: 1rem;
            font-size: 0.8rem;
        }

        .hero-stat {
            flex: 1;
            padding: 0.6rem 0.75rem;
            border-radius: 0.9rem;
            background: rgba(15, 23, 42, 0.64);
            border: 1px solid rgba(148, 163, 184, 0.6);
        }

        .hero-stat-label {
            color: #a7f3d0;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.1rem;
        }

        .hero-stat-value {
            font-weight: 700;
            color: #ecfeff;
        }

        .landing-section-title {
            font-size: 1.4rem;
            font-weight: 800;
            color: #064e3b;
            margin-bottom: 0.4rem;
        }

        .landing-section-subtitle {
            font-size: 0.9rem;
            color: #047857;
            margin-bottom: 1.4rem;
        }

        .feature-card {
            border-radius: 1rem;
            padding: 1.25rem 1.3rem;
            background: linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(240, 253, 244, 0.96));
            border: 1px solid rgba(16, 185, 129, 0.18);
            box-shadow: 0 10px 22px rgba(15, 118, 110, 0.12);
            height: 100%;
        }

        .feature-icon {
            width: 32px;
            height: 32px;
            border-radius: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 0.6rem;
            background: linear-gradient(135deg, #bbf7d0, #6ee7b7);
        }

        .feature-title {
            font-weight: 700;
            margin-bottom: 0.25rem;
            color: #052e16;
        }

        .feature-desc {
            font-size: 0.86rem;
            color: #065f46;
        }

        .how-it-works-list {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 1.1rem;
            margin-top: 0.5rem;
        }

        .how-step {
            padding: 0.9rem 1rem;
            border-radius: 0.9rem;
            background: rgba(240, 253, 244, 0.9);
            border: 1px solid rgba(34, 197, 94, 0.2);
            font-size: 0.86rem;
            color: #064e3b;
        }

        .how-step span.index {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 1.3rem;
            height: 1.3rem;
            border-radius: 999px;
            background: #22c55e;
            color: white;
            font-size: 0.72rem;
            font-weight: 700;
            margin-right: 0.45rem;
        }

        .contact-card {
            border-radius: 1rem;
            padding: 1.1rem 1.3rem;
            background: linear-gradient(135deg, rgba(22, 163, 74, 0.08), rgba(59, 130, 246, 0.08));
            border: 1px solid rgba(59, 130, 246, 0.2);
            font-size: 0.88rem;
            color: #064e3b;
        }

        @media (max-width: 900px) {
            .landing-wrapper {
                padding: 1.2rem 1.5rem 2.2rem 1.5rem;
            }

            .landing-nav {
                flex-direction: column;
                align-items: flex-start;
                gap: 0.7rem;
                border-radius: 1.25rem;
            }

            .landing-menu {
                justify-content: flex-start;
                flex-wrap: wrap;
            }
        }

        @media (max-width: 640px) {
            .landing-wrapper {
                padding: 1rem 1rem 2rem 1rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Wrapper layout
    with st.container():
        st.markdown('<div class="landing-wrapper">', unsafe_allow_html=True)

        # Navbar layout (logo + menu + CTA buttons in a single row)
        st.markdown('<div class="landing-nav-row" id="home-nav">', unsafe_allow_html=True)
        nav_left, nav_center, nav_right = st.columns([1.4, 2.4, 1.7])
        with nav_left:
            st.markdown(
                """
                <div class="landing-logo">
                    <span class="icon">🌱</span>
                    <span class="text">AgriGraphX</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with nav_center:
            st.markdown(
                """
                <div class="landing-menu">
                    <a href="#home-nav">Home</a>
                    <a href="#features">Features</a>
                    <a href="#how-it-works">How It Works</a>
                    <a href="#contact">Contact</a>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with nav_right:
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                if st.button("Sign In", key="landing_nav_signin"):
                    st.session_state.ui_mode = "auth"
                    st.rerun()
            with btn_col2:
                if st.button("Get Started", key="landing_nav_get_started", type="primary"):
                    st.session_state.ui_mode = "auth"
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Hero section
        st.markdown("<div class='landing-hero'>", unsafe_allow_html=True)

        hero_left, hero_right = st.columns([1.1, 1])
        with hero_left:
            st.markdown(
                """
                <div class="landing-hero-left">
                    <div class="landing-eyebrow">Hybrid Semantic Intelligence · Admin Studio</div>
                    <div class="landing-title">
                        AI-Powered <span>Cross Domain Knowledge Mapping</span><br/>
                        for Agriculture &amp; Climate
                    </div>
                    <div class="landing-subtitle">
                        Discover relationships between crops, climate variables, and data science
                        workflows using explainable knowledge graphs and domain-aware AI.
                    </div>
                    <div class="landing-pill-row">
                        <div class="landing-pill">🕸️ Knowledge Graph Visualization</div>
                        <div class="landing-pill">🔍 Semantic Search</div>
                        <div class="landing-pill">🌍 Cross-Domain Mapping</div>
                        <div class="landing-pill">🤖 AI Insights &amp; Recommendations</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            cta_col1, cta_col2 = st.columns([1.1, 1])
            with cta_col1:
                if st.button("🚀 Get Started", key="landing_cta_get_started", type="primary"):
                    st.session_state.ui_mode = "auth"
                    st.rerun()
            with cta_col2:
                if st.button("🔑 Sign In", key="landing_cta_signin"):
                    st.session_state.ui_mode = "auth"
                    st.rerun()

        with hero_right:
            st.markdown(
                """
                <div class="landing-hero-right">
                    <div class="hero-card">
                        <div class="hero-card-header">
                            <div class="hero-card-title">Real-Time Graph Studio</div>
                            <div class="hero-chip">Admin Dashboard · v1</div>
                        </div>
                        <div class="hero-graph">
                            <div class="hero-graph-grid">
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                                <div class="hero-node"></div>
                            </div>
                            <div class="hero-stats-row">
                                <div class="hero-stat">
                                    <div class="hero-stat-label">Nodes</div>
                                    <div class="hero-stat-value">Agriculture · Climate · AI</div>
                                </div>
                                <div class="hero-stat">
                                    <div class="hero-stat-label">Relations</div>
                                    <div class="hero-stat-value">CAUSES · IMPACTS · USES</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)  # close hero

        # Features section
        st.markdown("<div id='features'>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="landing-section-title">Features</div>
            <div class="landing-section-subtitle">
                Built for agricultural researchers, climate scientists, and data teams
                who need explainable, cross-domain intelligence.
            </div>
            """,
            unsafe_allow_html=True,
        )

        f1, f2, f3, f4 = st.columns(4)
        with f1:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">🕸️</div>
                    <div class="feature-title">Knowledge Graph Visualization</div>
                    <div class="feature-desc">
                        Explore entities and relationships across agriculture, climate,
                        and data science pipelines with interactive graph views.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with f2:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">🔍</div>
                    <div class="feature-title">Semantic Search</div>
                    <div class="feature-desc">
                        Ask natural language questions and discover relevant concepts
                        and relations using hybrid semantic search.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with f3:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">🌍</div>
                    <div class="feature-title">Cross-Domain Mapping</div>
                    <div class="feature-desc">
                        Connect signals from weather, soil, crop management and models
                        into a unified, navigable knowledge map.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with f4:
            st.markdown(
                """
                <div class="feature-card">
                    <div class="feature-icon">🤖</div>
                    <div class="feature-title">AI Insights &amp; Recommendations</div>
                    <div class="feature-desc">
                        Generate explainable insights and scenario-aware
                        recommendations from your knowledge graph.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        # How it works
        st.markdown("<div id='how-it-works' style='margin-top: 2.4rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="landing-section-title">How It Works</div>
            <div class="landing-section-subtitle">
                From raw documents to curated cross-domain intelligence in four steps.
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="how-it-works-list">
                <div class="how-step"><span class="index">1</span>Ingest agriculture, climate and data science datasets and documents.</div>
                <div class="how-step"><span class="index">2</span>Automatically extract entities and relations to build a unified graph.</div>
                <div class="how-step"><span class="index">3</span>Refine and validate links with the admin dashboard and expert feedback.</div>
                <div class="how-step"><span class="index">4</span>Run semantic search and AI reasoning for explainable recommendations.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Contact / call-to-action footer
        st.markdown("<div id='contact' style='margin-top: 2.4rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            """
            <div class="landing-section-title">Ready to explore your knowledge graph?</div>
            <div class="landing-section-subtitle">
                Sign in to the admin dashboard to start mapping agriculture &amp; climate intelligence.
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_contact, col_cta = st.columns([1.6, 1.2])
        with col_contact:
            st.markdown(
                """
                <div class="contact-card">
                    <strong>AgriGraphX · Cross Domain Knowledge Mapping Tool</strong><br/>
                    Designed for internal demos, research pilots, and domain expert reviews.
                    Use your admin credentials to access the full dashboard.
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_cta:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("Get Started", key="landing_footer_get_started", type="primary"):
                    st.session_state.ui_mode = "auth"
                    st.rerun()
            with c2:
                if st.button("Sign In", key="landing_footer_signin"):
                    st.session_state.ui_mode = "auth"
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)  # close landing-wrapper


 # ═══════════════════════════════════════════════════════════════════════════════
#  ENTRY ROUTER — LANDING VS AUTH/APP
# ═══════════════════════════════════════════════════════════════════════════════

if "ui_mode" not in st.session_state:
    # First-time visitors land on the public landing page
    st.session_state.ui_mode = "landing"

# 🚨 FIRST: Handle landing page WITHOUT any prior app layout
if st.session_state.ui_mode == "landing":
    render_landing_page()
    st.stop()


# ═══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INIT (RUN ONLY AFTER LEAVING LANDING)
# ═══════════════════════════════════════════════════════════════════════════════

def init_state():
    """Initialize session state with all required objects.

    Assumes authentication and dataset session keys have already
    been initialized by initialize_session_state() and
    initialize_dataset_state().
    """

    # ─── EXISTING STATE ───────────────────────────────────────────────────────
    if "kg" not in st.session_state:
        st.session_state.kg = KnowledgeGraph()

    if "monitor" not in st.session_state:
        st.session_state.monitor = PipelineMonitor()

    if "feedback" not in st.session_state:
        st.session_state.feedback = FeedbackSystem()

    if "refinement" not in st.session_state:
        st.session_state.refinement = RefinementEngine(st.session_state.kg)

    if "active_page" not in st.session_state:
        st.session_state.active_page = "Cross-Domain Input"

    if "initialized" not in st.session_state:
        st.session_state.initialized = False


# ✅ ONLY AFTER landing, initialize everything
initialize_session_state()
initialize_dataset_state()
init_state()


# ═══════════════════════════════════════════════════════════════════════════════
#  AUTHENTICATION CHECK — MODULE 1 INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

# If user is not authenticated, show login/register page and exit
if not is_authenticated():
    auth_ok = render_auth_page()
    if not auth_ok:
        # Stay on the authentication screen until login succeeds
        st.stop()

    # On successful login, move into the main app view
    st.session_state.ui_mode = "app"
    st.rerun()
else:
    # Already authenticated; ensure we remain in app mode
    st.session_state.ui_mode = "app"


# ═══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ═══════════════════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1.2rem 0 0.8rem 0;">
        <div style="font-size: 3rem; line-height:1; animation: bounce 2s infinite;">🌱</div>
        <div style="font-size: 1.5rem; font-weight: 900; margin-top: 0.5rem; letter-spacing: -0.5px;
                    background: linear-gradient(135deg, #10B981, #34D399, #6EE7B7);
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;">
            AgriGraphX
        </div>
        <div style="font-size: 0.75rem; color: #047857; letter-spacing: 1.2px;
                    text-transform: uppercase; margin-top: 0.3rem; font-weight: 700;">
            Cross-Domain Knowledge Mapping
        </div>
    </div>
    <style>
        @keyframes bounce {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-8px); }
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # ─── AUTHENTICATION INFO & USER PROFILE ───────────────────────────────────
    current_user = None
    profile = {}
    preferences = {}
    saved_graphs = []

    if is_authenticated():
        current_user = st.session_state.user
        st.markdown(f"👤 **Logged in as:** `{current_user}`")

        # Load (or create) the user's profile
        profile = get_user(current_user) or {}
        preferences = profile.get("preferences", {})
        saved_graphs = profile.get("saved_graphs", []) or []

        # Debug: Show JWT Token
        with st.expander("🔑 Debug: View Token"):
            token = st.session_state.get("token", "No token found")
            st.code(token, language="text", wrap_lines=True)

        # Logout control
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.user = None
            st.session_state.token = None
            st.session_state.auth_status = None
            st.success("✅ Logged out successfully!")
            st.rerun()

        st.markdown("---")

    # Navigation — dropdown-style grouped by modules
    if "page" not in st.session_state:
        st.session_state["page"] = "Dashboard"
    if "active_page" not in st.session_state:
        st.session_state.active_page = st.session_state["page"]

    # Ensure only one module is expanded by default (optional enhancement)
    if "sidebar_module" not in st.session_state:
        st.session_state.sidebar_module = "module1"

    current_page = st.session_state["page"]

    # 🔐 Authentication & Dataset
    with st.expander("🔐 Authentication & Dataset", expanded=st.session_state.sidebar_module == "module1"):
        # User preferences inside Module 1
        if current_user is not None:
            st.markdown("#### ⚙️ User Preferences")
            theme_options = ["light", "dark"]
            current_theme = preferences.get("theme", "light")
            if current_theme not in theme_options:
                current_theme = "light"

            default_domain_options = ["Agriculture", "Climate", "Data Science"]
            current_domain = preferences.get("default_domain", "Agriculture")
            if current_domain not in default_domain_options:
                current_domain = "Agriculture"

            theme = st.selectbox(
                "Theme",
                theme_options,
                index=theme_options.index(current_theme),
                key="user_pref_theme",
            )

            default_domain = st.selectbox(
                "Default domain",
                default_domain_options,
                index=default_domain_options.index(current_domain),
                key="user_pref_domain",
            )

            if st.button("💾 Save Preferences", key="btn_save_prefs", use_container_width=True):
                update_user(
                    current_user,
                    {"preferences": {"theme": theme, "default_domain": default_domain}},
                )
                st.success("Preferences saved for this user.")

            # Saved graphs overview
            st.markdown("### 📂 My Saved Graphs")
            if not saved_graphs:
                st.caption("No saved graphs yet. Use 'Graph View' to save one.")
            else:
                for idx, graph_meta in enumerate(saved_graphs):
                    name = graph_meta.get("name", f"Graph {idx + 1}")
                    created_at = graph_meta.get("created_at", "-")
                    dataset = graph_meta.get("dataset", "Unknown")
                    nodes = graph_meta.get("nodes")
                    edges = graph_meta.get("edges")

                    with st.container():
                        st.markdown(
                            f"**{name}**  \\n++                        🕒 {created_at}  |  📁 {dataset}"
                        )
                        if nodes is not None and edges is not None:
                            st.caption(f"Nodes: {nodes} · Edges: {edges}")

                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Load", key=f"load_saved_graph_{idx}", use_container_width=True):
                                # Store the selected graph metadata in session state;
                                # the Graph View page can react to this.
                                st.session_state["active_saved_graph_index"] = idx
                                st.session_state["page"] = "Graph View"
                                st.session_state["active_page"] = "Graph View"
                                st.rerun()
                        with col_b:
                            if st.button("Delete", key=f"delete_saved_graph_{idx}", use_container_width=True):
                                new_graphs = [g for j, g in enumerate(saved_graphs) if j != idx]
                                update_user(current_user, {"saved_graphs": new_graphs})
                                st.success(f"Deleted saved graph '{name}'.")
                                st.rerun()

            st.markdown("---")

        if st.button("📊 Dataset Selection", key="nav_Dataset_Selection", use_container_width=True):
            st.session_state["page"] = "Dataset Selection"
            st.session_state.active_page = "Dataset Selection"
            st.session_state.sidebar_module = "module1"
            st.rerun()
        if st.button("📁 Datasets", key="nav_Datasets", use_container_width=True):
            st.session_state["page"] = "Datasets"
            st.session_state.active_page = "Datasets"
            st.session_state.sidebar_module = "module1"
            st.rerun()

    # 🧠 NLP Pipeline
    with st.expander("🧠 NLP Pipeline", expanded=st.session_state.sidebar_module == "module2"):
        if st.button("⚙️ Pipeline Monitor", key="nav_Pipeline_Monitor", use_container_width=True):
            st.session_state["page"] = "Pipeline Monitor"
            st.session_state.active_page = "Pipeline Monitor"
            st.session_state.sidebar_module = "module2"
            st.rerun()

    # 🕸️ Knowledge Graph
    with st.expander("🕸️ Knowledge Graph", expanded=st.session_state.sidebar_module == "module3"):
        if st.button("📋 Knowledge Table", key="nav_Knowledge_Table", use_container_width=True):
            st.session_state["page"] = "Knowledge Table"
            st.session_state.active_page = "Knowledge Table"
            st.session_state.sidebar_module = "module3"
            st.rerun()
        if st.button("🗺️ Graph View", key="nav_Graph_View", use_container_width=True):
            st.session_state["page"] = "Graph View"
            st.session_state.active_page = "Graph View"
            st.session_state.sidebar_module = "module3"
            st.rerun()

    # 🔍 Semantic Search & Mapping
    with st.expander("🔍 Semantic Search & Mapping", expanded=st.session_state.sidebar_module == "module4"):
        if st.button("📥 Cross-Domain Input", key="nav_Cross_Domain_Input", use_container_width=True):
            st.session_state["page"] = "Cross-Domain Input"
            st.session_state.active_page = "Cross-Domain Input"
            st.session_state.sidebar_module = "module4"
            st.rerun()
        if st.button("🔍 Semantic Search", key="nav_Semantic_Search", use_container_width=True):
            st.session_state["page"] = "Semantic Search"
            st.session_state.active_page = "Semantic Search"
            st.session_state.sidebar_module = "module4"
            st.rerun()

    # ⚙️ Dashboard & Refinement
    with st.expander("⚙️ Dashboard & Refinement", expanded=st.session_state.sidebar_module == "module5"):
        if st.button("📊 Dashboard", key="nav_Dashboard", use_container_width=True):
            st.session_state["page"] = "Dashboard"
            st.session_state.active_page = "Dashboard"
            st.session_state.sidebar_module = "module5"
            st.rerun()
        if st.button("🔧 Graph Refinement", key="nav_Graph_Refinement", use_container_width=True):
            st.session_state["page"] = "Graph Refinement"
            st.session_state.active_page = "Graph Refinement"
            st.session_state.sidebar_module = "module5"
            st.rerun()

    # 🧩 Reasoning & Feedback
    with st.expander("🧩 Reasoning & Feedback", expanded=st.session_state.sidebar_module == "module6"):
        if st.button("🧠 Reasoning", key="nav_Reasoning", use_container_width=True):
            st.session_state["page"] = "Reasoning"
            st.session_state.active_page = "Reasoning"
            st.session_state.sidebar_module = "module6"
            st.rerun()
        if st.button("💬 Feedback", key="nav_Feedback", use_container_width=True):
            st.session_state["page"] = "Feedback"
            st.session_state.active_page = "Feedback"
            st.session_state.sidebar_module = "module6"
            st.rerun()

    # 🤖 AI Insight & Recommendation Engine
    with st.expander("🤖 AI Insights", expanded=st.session_state.sidebar_module == "module7"):
        if st.button("🤖 AI Insights", key="nav_AI_Insights", use_container_width=True):
            st.session_state["page"] = "AI Insights"
            st.session_state.active_page = "AI Insights"
            st.session_state.sidebar_module = "module7"
            st.rerun()

    st.markdown("---")

    # System info
    summary = st.session_state.kg.summary()
    st.markdown(f"""
    <div style="padding: 0.5rem; border-radius: 10px;
                background: rgba(108,99,255,0.06);
                border: 1px solid rgba(108,99,255,0.15);">
        <div style="font-size: 0.75rem; color: #64748B; text-transform: uppercase;
                    letter-spacing: 0.5px; margin-bottom: 0.4rem;">System Status</div>
        <div style="font-size: 0.85rem; color: #1E293B; line-height: 1.6;">
            🔵 Nodes: <b>{summary['nodes']}</b><br/>
            🔗 Edges: <b>{summary['edges']}</b><br/>
            📊 Status: <b style="color:#22C55E;">Online</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="text-align:center; padding: 1.5rem 0 0.5rem 0;
                font-size: 0.7rem; color: #64748B;">
        Module 5 · KnowMap Architecture<br/>
        <span style="color:#6C63FF;">Hybrid Semantic Intelligence Engine</span>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  HERO HEADER
# ═══════════════════════════════════════════════════════════════════════════════

st.markdown(f"""
<div class="hero-header">
    <h1>🌳 AgriGraphX Cross Domain Knowledge Mapping tool for Agriculture and Climatic Insights</h1>
    <p>Cross-Domain Knowledge Graph Management</p>
</div>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════════
#  MAIN CONTENT ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

# Sync 'active_page' from the canonical 'page' key if present
if "page" in st.session_state:
    st.session_state.active_page = st.session_state["page"]

active_page = st.session_state.active_page
kg = st.session_state.kg
monitor = st.session_state.monitor
feedback = st.session_state.feedback
refinement = st.session_state.refinement

if active_page == "Cross-Domain Input":
    render_page_header(
        icon="📥",
        title="Cross-Domain Input",
        module_label="Module 4 · Semantic Search & Mapping",
        subtitle="Ingest agriculture & climate text for cross-domain mapping.",
    )
    render_cross_domain_upload(kg, monitor, feedback, refinement)

elif active_page == "Dataset Selection":
    render_page_header(
        icon="📦",
        title="Module 1 · Dataset Ingestion & Selection",
        module_label="Module 1 · Dataset & Source Management",
        subtitle="Upload, fetch and prepare datasets for downstream NLP processing.",
    )
    initialize_dataset_state()
    render_dataset_selection()
    render_dataset_summary()

    # Log dataset history per user when a new dataset is selected
    if is_authenticated():
        has_dataset, content, source = get_selected_dataset()
        if has_dataset and source:
            # Avoid logging the same selection repeatedly
            last_logged = st.session_state.get("_last_logged_dataset_source")
            if last_logged != source:
                user_id = st.session_state.user
                profile = get_user(user_id) or {}
                history = profile.get("dataset_history", []) or []

                # Classify source type
                src_lower = str(source).lower()
                if src_lower in {"wikipedia", "news", "arxiv"}:
                    src_type = src_lower
                elif source in SAMPLE_DATASETS:
                    src_type = "sample"
                elif "upload" in src_lower:
                    src_type = "upload"
                else:
                    src_type = "other"

                history.append(
                    {
                        "dataset_name": str(source),
                        "source": src_type,
                        "timestamp": datetime.utcnow().isoformat(),
                    }
                )
                update_user(user_id, {"dataset_history": history})
                st.session_state["_last_logged_dataset_source"] = source

elif active_page == "Dashboard":
    render_page_header(
        icon="📊",
        title="System Overview Dashboard",
        module_label="Module 5 · Admin Control Panel",
        subtitle="Monitor graph health, pipeline status and feedback quality at a glance.",
    )
    render_overview_dashboard(kg, monitor, feedback)

elif active_page == "Pipeline Monitor":
    render_page_header(
        icon="⚙️",
        title="NLP Pipeline Monitor",
        module_label="Module 2 · Processing Pipeline",
        subtitle="Track document processing, entity extraction and relation building.",
    )
    render_pipeline_monitor(monitor, kg)

elif active_page == "Datasets":
    render_page_header(
        icon="📁",
        title="Dataset Management",
        module_label="Module 1 · Dataset & Source Management",
        subtitle="Inspect, validate and manage datasets used to build the graph.",
    )
    render_dataset_management(kg, monitor)

elif active_page == "Knowledge Table":
    render_page_header(
        icon="📋",
        title="Knowledge Table",
        module_label="Module 3 · Knowledge Graph",
        subtitle="Review extracted triples with confidence scores and status labels.",
    )
    render_knowledge_table(kg, refinement, feedback)

elif active_page == "Graph Refinement":
    render_page_header(
        icon="🔧",
        title="Graph Refinement Studio",
        module_label="Module 5 · Graph Curation",
        subtitle="Approve, reject or adjust relations to keep the graph trustworthy.",
    )
    render_graph_refinement(kg, refinement)

elif active_page == "Graph View":
    render_page_header(
        icon="🗺️",
        title="Interactive Graph View",
        module_label="Module 3 · Knowledge Graph",
        subtitle="Explore entities and relations across agriculture, climate and AI domains.",
    )
    # Allow user to save the current graph against their profile
    if is_authenticated():
        current_user = st.session_state.user
        profile = get_user(current_user) or {}
        summary = kg.summary()

        st.markdown("---")
        st.markdown("#### 💾 Save Current Graph")

        dataset_label = st.session_state.get("dataset_source") or "Unknown dataset"
        default_name = f"{dataset_label} graph" if dataset_label else "My Graph"

        graph_name = st.text_input(
            "Graph name",
            value=default_name,
            key="graph_save_name",
        )

        if st.button("💾 Save Current Graph", key="btn_save_current_graph"):
            if summary.get("nodes", 0) <= 0:
                st.warning("There is no graph data to save yet.")
            else:
                saved_graphs = profile.get("saved_graphs", []) or []
                entry = {
                    "name": graph_name.strip() or default_name,
                    "created_at": datetime.utcnow().isoformat(),
                    "dataset": dataset_label,
                    "nodes": summary.get("nodes", 0),
                    "edges": summary.get("edges", 0),
                }
                saved_graphs.append(entry)
                update_user(current_user, {"saved_graphs": saved_graphs})
                st.success("Current graph saved to your profile.")

    render_interactive_graph(kg)

elif active_page == "Semantic Search":
    render_page_header(
        icon="🔍",
        title="Semantic Search",
        module_label="Module 4 · Semantic Search & Mapping",
        subtitle="Ask natural language questions over the curated knowledge graph.",
    )
    render_semantic_search(kg)

elif active_page == "Reasoning":
    render_page_header(
        icon="🧠",
        title="Reasoning Validation",
        module_label="Module 6 · Reasoning & Feedback",
        subtitle="Validate inference chains and explanations produced by the hybrid engine.",
    )
    render_reasoning_validation(kg, refinement)

elif active_page == "Feedback":
    render_page_header(
        icon="💬",
        title="Expert Feedback",
        module_label="Module 6 · Reasoning & Feedback",
        subtitle="Capture expert feedback to continuously improve graph quality.",
    )
    render_feedback_panel(feedback, kg)

elif active_page == "AI Insights":
    render_page_header(
        icon="🤖",
        title="AI Insight & Recommendation Engine",
        module_label="Module 7 · Insight Engine",
        subtitle="Combine graph, search and triples into explainable domain insights.",
    )
    st.markdown('<div class="section-header">🤖 AI Insight & Recommendation Engine</div>', unsafe_allow_html=True)

    st.markdown(
        """
        <div class="info-banner">
            This module combines the existing knowledge graph, semantic search
            and NLP triples to generate explainable insights and
            recommendations for agriculture and climate questions.
        </div>
        """,
        unsafe_allow_html=True,
    )

    query = st.text_input(
        "Enter your query (e.g. 'How does rainfall affect crop yield?')",
        key="ai_insight_query",
    )

    if st.button("Generate Insights", key="btn_generate_ai_insights"):
        if not query.strip():
            st.warning("Please enter a query first.")
        else:
            result = run_insight_pipeline(query, kg)

            st.subheader("💡 Insights")
            if result.get("insights"):
                st.write(result["insights"])
            else:
                st.info("No insights could be generated for this query yet.")

            st.subheader("🌱 Recommendations")
            recs = result.get("recommendations", [])
            if recs:
                for rec in recs:
                    st.write(f"- {rec}")
            else:
                st.info("No specific recommendations were generated.")

            st.subheader("🔗 Supporting Relations")
            rels = result.get("supporting_relations", [])
            if rels:
                for rel in rels:
                    src = rel.get("source")
                    tgt = rel.get("target")
                    rtype = rel.get("relation")
                    conf = rel.get("confidence")
                    st.write(f"{src} --{rtype}→ {tgt} (confidence {conf:.2f})")
            else:
                st.caption("No supporting relations found in the current graph.")
