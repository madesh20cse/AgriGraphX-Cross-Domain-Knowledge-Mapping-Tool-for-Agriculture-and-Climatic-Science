"""
pipeline_monitor.py — NLP Pipeline Monitoring Module.

Tracks and simulates NLP pipeline execution for admin monitoring.
"""

from __future__ import annotations

import time
import random
from datetime import datetime, timedelta
from utils import get_logger

logger = get_logger(__name__)


class PipelineMonitor:
    """Monitor and track NLP pipeline execution status."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.status = "idle"  # idle, running, completed, error
        self.start_time = None
        self.end_time = None
        self.total_documents = 0
        self.processed_documents = 0
        self.entities_extracted = 0
        self.relations_extracted = 0
        self.active_dataset = ""
        self.active_domain = ""
        self.models_used = {
            "NER": "spaCy (en_core_web_sm)",
            "Relation Extraction": "Regex + spaCy NLP",
            "Embeddings": "all-MiniLM-L6-v2",
            "Reasoning": "Hybrid (Embedding + Ontology)",
        }
        self.pipeline_stages = [
            {"name": "Text Preprocessing", "status": "pending", "progress": 0},
            {"name": "Entity Extraction (NER)", "status": "pending", "progress": 0},
            {"name": "Relation Extraction", "status": "pending", "progress": 0},
            {"name": "Knowledge Graph Construction", "status": "pending", "progress": 0},
            {"name": "Semantic Embedding", "status": "pending", "progress": 0},
            {"name": "Reasoning & Inference", "status": "pending", "progress": 0},
        ]
        self.logs = []

    def start_pipeline(self, dataset_name: str, domain: str, num_documents: int):
        """Initialize a pipeline run."""
        self.reset()
        self.status = "running"
        self.start_time = datetime.now()
        self.active_dataset = dataset_name
        self.active_domain = domain
        self.total_documents = num_documents
        self._add_log("INFO", f"Pipeline started for dataset: {dataset_name}")
        self._add_log("INFO", f"Domain: {domain}, Documents: {num_documents}")

    def update_progress(self, stage_idx: int, progress: float,
                        docs_processed: int = 0,
                        entities: int = 0, relations: int = 0):
        """Update pipeline stage progress."""
        if stage_idx < len(self.pipeline_stages):
            self.pipeline_stages[stage_idx]["progress"] = min(progress, 100)
            if progress >= 100:
                self.pipeline_stages[stage_idx]["status"] = "completed"
            elif progress > 0:
                self.pipeline_stages[stage_idx]["status"] = "running"

        if docs_processed > 0:
            self.processed_documents = docs_processed
        if entities > 0:
            self.entities_extracted = entities
        if relations > 0:
            self.relations_extracted = relations

    def complete_pipeline(self, entities: int, relations: int):
        """Mark pipeline as completed."""
        self.status = "completed"
        self.end_time = datetime.now()
        self.processed_documents = self.total_documents
        self.entities_extracted = entities
        self.relations_extracted = relations
        for stage in self.pipeline_stages:
            stage["status"] = "completed"
            stage["progress"] = 100
        self._add_log("INFO", f"Pipeline completed successfully.")
        self._add_log("INFO", f"Entities: {entities}, Relations: {relations}")

    def get_overall_progress(self) -> float:
        """Get overall pipeline progress as percentage."""
        if not self.pipeline_stages:
            return 0
        total = sum(s["progress"] for s in self.pipeline_stages)
        return total / len(self.pipeline_stages)

    def get_elapsed_time(self) -> str:
        """Get elapsed time as formatted string."""
        if self.start_time is None:
            return "N/A"
        end = self.end_time or datetime.now()
        delta = end - self.start_time
        total_seconds = int(delta.total_seconds())
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes}m {seconds}s"

    def _add_log(self, level: str, message: str):
        """Add a log entry."""
        self.logs.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "level": level,
            "message": message,
        })

    def get_status_dict(self) -> dict:
        """Return current status as a dictionary."""
        return {
            "status": self.status,
            "active_dataset": self.active_dataset,
            "active_domain": self.active_domain,
            "total_documents": self.total_documents,
            "processed_documents": self.processed_documents,
            "entities_extracted": self.entities_extracted,
            "relations_extracted": self.relations_extracted,
            "overall_progress": self.get_overall_progress(),
            "elapsed_time": self.get_elapsed_time(),
            "models_used": self.models_used,
            "stages": self.pipeline_stages,
            "logs": self.logs[-20:],  # Last 20 logs
        }


def create_demo_monitor(dataset_name: str = "AI & Machine Learning",
                        domain: str = "AI",
                        num_docs: int = 20) -> PipelineMonitor:
    """Create a demo pipeline monitor with simulated completed state."""
    monitor = PipelineMonitor()
    monitor.start_pipeline(dataset_name, domain, num_docs)
    monitor.complete_pipeline(
        entities=random.randint(25, 50),
        relations=random.randint(15, 35),
    )
    return monitor
