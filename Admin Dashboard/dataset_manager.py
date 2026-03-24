"""
dataset_manager.py — Dataset Management Module.

Handles dataset loading, statistics, and sample data generation.
"""

from __future__ import annotations

import os
import json
import csv
import pandas as pd
from datetime import datetime
from utils import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
DATASETS_DIR = os.path.join(DATA_DIR, "datasets")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

# Ensure directories exist
os.makedirs(DATASETS_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)


# ─── Sample Datasets ─────────────────────────────────────────────────────────

SAMPLE_DATASETS = {
    "AI & Machine Learning": {
        "domain": "AI",
        "documents": [
            "Artificial Intelligence is a field of Computer Science.",
            "Machine Learning is a subclass of Artificial Intelligence.",
            "Deep Learning is a subclass of Machine Learning.",
            "Neural Network is part of Deep Learning.",
            "Natural Language Processing uses Machine Learning.",
            "Computer Vision uses Deep Learning.",
            "Reinforcement Learning is a subclass of Machine Learning.",
            "GPT is related to Natural Language Processing.",
            "Transformer is part of Deep Learning.",
            "TensorFlow uses Neural Network.",
            "PyTorch uses Neural Network.",
            "AI uses Data Science.",
            "Data Science is related to Machine Learning.",
            "Supervised Learning is a subclass of Machine Learning.",
            "Unsupervised Learning is a subclass of Machine Learning.",
            "Convolutional Neural Network is a subclass of Neural Network.",
            "Recurrent Neural Network is a subclass of Neural Network.",
            "BERT uses Transformer.",
            "Self-Driving Car uses Computer Vision.",
            "Chatbot uses Natural Language Processing.",
        ],
    },
    "Healthcare & Medical": {
        "domain": "Healthcare",
        "documents": [
            "Medical AI uses Machine Learning.",
            "Doctor uses Electronic Health Records.",
            "Patient is related to Doctor.",
            "Diagnosis uses Medical AI.",
            "Drug Discovery uses Deep Learning.",
            "Genomics is related to Bioinformatics.",
            "Bioinformatics uses Machine Learning.",
            "Radiology uses Computer Vision.",
            "Surgery is related to Doctor.",
            "Telemedicine uses AI.",
            "Clinical Trial is related to Drug Discovery.",
            "Pathology uses Medical Imaging.",
            "Medical Imaging is a subclass of Computer Vision.",
            "Wearable Device is related to Patient.",
            "Heart Disease is related to Diagnosis.",
        ],
    },
    "Physics & Science": {
        "domain": "Physics",
        "documents": [
            "Albert Einstein developed Theory of Relativity.",
            "NASA uses Theory of Relativity.",
            "Quantum Mechanics is related to Physics.",
            "String Theory is a subclass of Theoretical Physics.",
            "Theoretical Physics is a subclass of Physics.",
            "Particle Physics is a subclass of Physics.",
            "Large Hadron Collider is related to Particle Physics.",
            "Dark Matter is related to Cosmology.",
            "Cosmology is a subclass of Physics.",
            "Newton developed Classical Mechanics.",
            "Classical Mechanics is a subclass of Physics.",
            "Electromagnetism is a subclass of Physics.",
            "Gravity is related to Theory of Relativity.",
        ],
    },
    "Law & Legal": {
        "domain": "Law",
        "documents": [
            "Contract Law is a subclass of Civil Law.",
            "Civil Law is a subclass of Law.",
            "Criminal Law is a subclass of Law.",
            "Constitutional Law is a subclass of Law.",
            "Judge is related to Court.",
            "Lawyer uses Legal Database.",
            "Legal AI uses Natural Language Processing.",
            "Patent Law is a subclass of Intellectual Property Law.",
            "Intellectual Property Law is a subclass of Law.",
            "Legal Tech uses AI.",
        ],
    },
    "DataScience & Analytics": {
        "domain": "DataScience",
        "documents": [
            "Data Science uses Statistics.",
            "Data Scientist uses Python.",
            "Data Analysis uses Pandas.",
            "Data Visualization uses Matplotlib.",
            "Feature Engineering supports Machine Learning.",
            "Data Cleaning is part of Data Preparation.",
            "Big Data uses Distributed Computing.",
            "A B Testing uses Hypothesis Testing.",
            "Business Intelligence uses Data Visualization.",
            "Predictive Analytics uses Machine Learning.",
        ],
    },
    "Agriculture & Climatic Science": {
        "domain": "Agriculture and Climatic science",
        "documents": [
            "Precision Agriculture uses IoT Sensors.",
            "Crop Yield Prediction uses Machine Learning.",
            "Soil Health is related to Crop Productivity.",
            "Irrigation Management uses Weather Forecasting.",
            "Climate Change affects Rainfall Patterns.",
            "Greenhouse Gas is related to Global Warming.",
            "Agroforestry supports Carbon Sequestration.",
            "Drought Monitoring uses Satellite Imagery.",
            "Sustainable Farming reduces Soil Degradation.",
            "Climate Model predicts Temperature Trends.",
        ],
    },
}


def get_available_datasets() -> list[str]:
    """Return list of available dataset names."""
    datasets = list(SAMPLE_DATASETS.keys())
    # Check for custom uploaded datasets
    if os.path.exists(DATASETS_DIR):
        for f in os.listdir(DATASETS_DIR):
            if f.endswith(".json") or f.endswith(".csv") or f.endswith(".txt"):
                name = os.path.splitext(f)[0]
                if name not in datasets:
                    datasets.append(name)
    return datasets


def get_dataset(name: str) -> dict:
    """Get dataset by name. Returns dict with domain and documents."""
    if name in SAMPLE_DATASETS:
        return SAMPLE_DATASETS[name]

    # Try loading from file
    for ext in [".json", ".csv", ".txt"]:
        filepath = os.path.join(DATASETS_DIR, name + ext)
        if os.path.exists(filepath):
            ds = _load_file(filepath)

            # Apply sidecar metadata domain when available.
            meta_path = os.path.join(DATASETS_DIR, f"{name}_meta.json")
            if os.path.exists(meta_path):
                try:
                    with open(meta_path, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta_domain = meta.get("domain")
                    if meta_domain:
                        ds["domain"] = meta_domain
                except Exception as e:
                    logger.warning(f"Failed to read dataset metadata for '{name}': {e}")

            return ds

    return {"domain": "General", "documents": []}


def _load_file(filepath: str) -> dict:
    """Load dataset from file."""
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return {"domain": "General", "documents": data}
        return data

    elif ext == ".csv":
        docs = []
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    # Keep CSV structure so downstream extraction can parse tabular rows.
                    docs.append(",".join(cell.strip() for cell in row))
        return {"domain": "General", "documents": docs}

    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f.readlines() if l.strip()]
        return {"domain": "General", "documents": lines}

    return {"domain": "General", "documents": []}


def get_dataset_stats(name: str) -> dict:
    """Get statistics for a dataset."""
    ds = get_dataset(name)
    docs = ds.get("documents", [])
    total_words = sum(len(d.split()) for d in docs)
    return {
        "name": name,
        "domain": ds.get("domain", "General"),
        "num_documents": len(docs),
        "total_words": total_words,
        "avg_words_per_doc": total_words / max(len(docs), 1),
    }


def save_uploaded_dataset(name: str, content: str, domain: str = "General") -> str:
    """Save an uploaded dataset to the datasets directory."""
    filepath = os.path.join(DATASETS_DIR, f"{name}.txt")
    lines = [l.strip() for l in content.strip().split("\n") if l.strip()]
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # Also save metadata
    meta = {
        "name": name,
        "domain": domain,
        "num_documents": len(lines),
        "created": datetime.now().isoformat(),
    }
    meta_path = os.path.join(DATASETS_DIR, f"{name}_meta.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    logger.info(f"Saved dataset '{name}' with {len(lines)} documents.")
    return filepath


def get_all_dataset_stats() -> list[dict]:
    """Get stats for all available datasets."""
    return [get_dataset_stats(name) for name in get_available_datasets()]
