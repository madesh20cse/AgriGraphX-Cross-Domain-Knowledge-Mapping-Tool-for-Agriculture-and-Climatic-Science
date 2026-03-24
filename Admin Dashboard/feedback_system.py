"""
feedback_system.py — Expert Feedback Collection & Management.

Allows admin/expert reviewers to classify relations as:
- Correct
- Needs Review
- Incorrect

Stores feedback in CSV and provides analytics.
"""

from __future__ import annotations

import os
import csv
import json
import pandas as pd
from datetime import datetime
from utils import get_logger

logger = get_logger(__name__)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
FEEDBACK_FILE = os.path.join(DATA_DIR, "feedback.csv")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

FEEDBACK_OPTIONS = ["Correct", "Needs Review", "Incorrect"]


class FeedbackSystem:
    """Manages expert feedback on knowledge graph relations."""

    def __init__(self, filepath: str = FEEDBACK_FILE):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        """Create feedback CSV if it doesn't exist."""
        if not os.path.exists(self.filepath):
            with open(self.filepath, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "entity1", "relation", "entity2",
                    "feedback", "reviewer", "notes"
                ])

    def submit_feedback(
        self,
        entity1: str,
        relation: str,
        entity2: str,
        feedback: str,
        reviewer: str = "Admin",
        notes: str = "",
    ) -> dict:
        """Submit feedback for a relation."""
        if feedback not in FEEDBACK_OPTIONS:
            return {
                "success": False,
                "message": f"Invalid feedback. Choose from: {FEEDBACK_OPTIONS}",
            }

        timestamp = datetime.now().isoformat()

        with open(self.filepath, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp, entity1, relation, entity2,
                feedback, reviewer, notes
            ])

        logger.info(
            f"Feedback: {feedback} for ({entity1} --{relation}--> {entity2}) "
            f"by {reviewer}"
        )

        return {
            "success": True,
            "message": f"Feedback '{feedback}' recorded for ({entity1} → {entity2}).",
        }

    def get_all_feedback(self) -> pd.DataFrame:
        """Load all feedback as a DataFrame."""
        if not os.path.exists(self.filepath):
            return pd.DataFrame(columns=[
                "timestamp", "entity1", "relation", "entity2",
                "feedback", "reviewer", "notes"
            ])

        try:
            df = pd.read_csv(self.filepath)
            return df
        except Exception as e:
            logger.error(f"Error reading feedback file: {e}")
            return pd.DataFrame(columns=[
                "timestamp", "entity1", "relation", "entity2",
                "feedback", "reviewer", "notes"
            ])

    def get_feedback_summary(self) -> dict:
        """Get summary counts of feedback categories."""
        df = self.get_all_feedback()
        if df.empty:
            return {
                "Correct": 0,
                "Needs Review": 0,
                "Incorrect": 0,
                "total": 0,
            }

        counts = df["feedback"].value_counts().to_dict()
        return {
            "Correct": counts.get("Correct", 0),
            "Needs Review": counts.get("Needs Review", 0),
            "Incorrect": counts.get("Incorrect", 0),
            "total": len(df),
        }

    def get_feedback_for_relation(
        self, entity1: str, relation: str, entity2: str
    ) -> list[dict]:
        """Get all feedback entries for a specific relation."""
        df = self.get_all_feedback()
        if df.empty:
            return []

        mask = (
            (df["entity1"] == entity1) &
            (df["relation"] == relation) &
            (df["entity2"] == entity2)
        )
        return df[mask].to_dict("records")

    def get_feedback_by_reviewer(self, reviewer: str) -> pd.DataFrame:
        """Get all feedback from a specific reviewer."""
        df = self.get_all_feedback()
        if df.empty:
            return df
        return df[df["reviewer"] == reviewer]

    def get_recent_feedback(self, n: int = 10) -> pd.DataFrame:
        """Get the n most recent feedback entries."""
        df = self.get_all_feedback()
        if df.empty:
            return df
        return df.tail(n)

    def clear_feedback(self):
        """Clear all feedback data."""
        self._ensure_file()
        with open(self.filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "entity1", "relation", "entity2",
                "feedback", "reviewer", "notes"
            ])
        logger.info("Feedback data cleared.")

    def export_feedback_json(self) -> str:
        """Export feedback as JSON string."""
        df = self.get_all_feedback()
        return df.to_json(orient="records", indent=2)

    def get_accuracy_metrics(self) -> dict:
        """Calculate accuracy metrics from feedback."""
        summary = self.get_feedback_summary()
        total = summary["total"]
        if total == 0:
            return {
                "accuracy": 0.0,
                "review_rate": 0.0,
                "error_rate": 0.0,
                "total_reviews": 0,
            }

        return {
            "accuracy": summary["Correct"] / total * 100,
            "review_rate": summary["Needs Review"] / total * 100,
            "error_rate": summary["Incorrect"] / total * 100,
            "total_reviews": total,
        }
