"""
utils.py — Shared utility functions for the KnowMap Admin Dashboard.
"""

import re
import logging
from datetime import datetime

# ─── Logging ─────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ─── Text Helpers ─────────────────────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Remove extra whitespace and normalise punctuation."""
    text = re.sub(r"\s+", " ", text)
    text = text.strip()
    return text


def split_sentences(text: str) -> list[str]:
    """Split a paragraph into individual sentences (simple rule-based)."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if s.strip()]


def timestamp_label() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ─── Color Palette ────────────────────────────────────────────────────────────

DOMAIN_COLORS = {
    "AI":           "#6C63FF",
    "Healthcare":   "#43B89C",
    "Physics":      "#FF8C42",
    "Law":          "#FF6584",
    "DataScience":  "#2D6CDF",
    "Agriculture and Climatic science": "#6A994E",
    "Technology":   "#00D4AA",
    "General":      "#A8DADC",
    "default":      "#A8DADC",
}

NODE_COLORS = {
    "Vehicle":      "#6C63FF",
    "Machine":      "#FF6584",
    "Technology":   "#43B89C",
    "default":      "#A8DADC",
}

EDGE_COLORS = {
    "IS_A":         "#6C63FF",
    "SUBCLASS_OF":  "#FF6584",
    "RELATED_TO":   "#43B89C",
    "PART_OF":      "#F9C74F",
    "USES":         "#00D4AA",
    "INCLUDES":     "#A78BFA",
    "DEVELOPED":    "#FB923C",
    "INFERRED":     "#FFA552",
    "INHERITS_FROM":"#A8DADC",
    "default":      "#CCCCCC",
}


def node_color(label: str) -> str:
    return NODE_COLORS.get(label, NODE_COLORS["default"])


def edge_color(rel: str) -> str:
    return EDGE_COLORS.get(rel, EDGE_COLORS["default"])


def domain_color(domain: str) -> str:
    return DOMAIN_COLORS.get(domain, DOMAIN_COLORS["default"])


# ─── Score Formatting ─────────────────────────────────────────────────────────

def fmt_score(score: float, decimals: int = 4) -> str:
    return f"{score:.{decimals}f}"


def confidence_label(score: float) -> str:
    if score >= 0.85:
        return "🟢 Very High"
    elif score >= 0.70:
        return "🔵 High"
    elif score >= 0.50:
        return "🟡 Medium"
    elif score >= 0.30:
        return "🟠 Low"
    else:
        return "🔴 Very Low"


def confidence_score_color(score: float) -> str:
    """Return hex color based on confidence score."""
    if score >= 0.85:
        return "#22C55E"
    elif score >= 0.70:
        return "#3B82F6"
    elif score >= 0.50:
        return "#EAB308"
    elif score >= 0.30:
        return "#F97316"
    else:
        return "#EF4444"
