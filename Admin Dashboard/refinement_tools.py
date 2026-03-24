"""
refinement_tools.py — Graph Refinement Tools for Admin Dashboard.

Provides tools for manual knowledge graph correction:
- Merge duplicate nodes
- Edit relations
- Delete incorrect edges
- Add new edges
- Batch operations
"""

from __future__ import annotations

import re
from knowledge_graph import KnowledgeGraph
from utils import get_logger

logger = get_logger(__name__)


class RefinementEngine:
    """Engine for refining knowledge graph through admin actions."""

    def __init__(self, kg: KnowledgeGraph):
        self.kg = kg
        self.history: list[dict] = []  # Action history for undo

    def _record_action(self, action_type: str, details: dict):
        """Record an action for history tracking."""
        self.history.append({
            "type": action_type,
            "details": details,
        })

    # ── Merge Nodes ───────────────────────────────────────────────────────────

    def merge_nodes(self, old_name: str, new_name: str) -> dict:
        """
        Merge duplicate entities.
        Example: 'Einstein' → 'Albert Einstein'
        """
        if old_name == new_name:
            return {"success": False, "message": "Source and target names are the same."}

        if old_name not in self.kg.nodes():
            return {"success": False, "message": f"Node '{old_name}' not found in graph."}

        edges_updated = self.kg.merge_nodes(old_name, new_name)

        self._record_action("merge", {
            "old_name": old_name,
            "new_name": new_name,
            "edges_updated": edges_updated,
        })

        return {
            "success": True,
            "message": f"Merged '{old_name}' → '{new_name}'. Updated {edges_updated} edges.",
            "edges_updated": edges_updated,
        }

    # ── Edit Relation ─────────────────────────────────────────────────────────

    def edit_relation(self, src: str, tgt: str, new_relation: str) -> dict:
        """
        Edit the relation type on an edge.
        Example: 'AI uses ML' → 'AI includes ML'
        """
        old_edges = self.kg.edges()
        old_rel = None
        for u, v, d in old_edges:
            if u == src and v == tgt:
                old_rel = d.get("relation", "")
                break

        if old_rel is None:
            return {"success": False, "message": f"Edge ({src} → {tgt}) not found."}

        success = self.kg.update_edge_relation(src, tgt, new_relation)

        if success:
            self._record_action("edit_relation", {
                "src": src, "tgt": tgt,
                "old_relation": old_rel,
                "new_relation": new_relation,
            })
            return {
                "success": True,
                "message": f"Changed ({src} → {tgt}) from '{old_rel}' to '{new_relation}'.",
            }
        return {"success": False, "message": "Failed to update relation."}

    # ── Delete Edge ───────────────────────────────────────────────────────────

    def delete_edge(self, src: str, tgt: str) -> dict:
        """Delete an incorrect edge from the graph."""
        # Store for history
        edge_data = None
        for u, v, d in self.kg.edges():
            if u == src and v == tgt:
                edge_data = d.copy()
                break

        if edge_data is None:
            return {"success": False, "message": f"Edge ({src} → {tgt}) not found."}

        success = self.kg.delete_edge(src, tgt)

        if success:
            self._record_action("delete", {
                "src": src, "tgt": tgt,
                "edge_data": edge_data,
            })
            return {
                "success": True,
                "message": f"Deleted edge ({src} → {tgt}).",
            }
        return {"success": False, "message": "Failed to delete edge."}

    # ── Add Edge ──────────────────────────────────────────────────────────────

    def add_edge(self, src: str, tgt: str, relation: str,
                 confidence: float = 0.9, domain: str = "General") -> dict:
        """Add a new edge to the graph."""
        if not src or not tgt or not relation:
            return {"success": False, "message": "Source, target, and relation are required."}

        self.kg.add_new_edge(src, tgt, relation, confidence=confidence, domain=domain)

        self._record_action("add", {
            "src": src, "tgt": tgt,
            "relation": relation,
            "confidence": confidence,
        })

        return {
            "success": True,
            "message": f"Added edge ({src} --{relation}--> {tgt}) with confidence {confidence:.2f}.",
        }

    # ── Approve / Reject ──────────────────────────────────────────────────────

    def approve_relation(self, src: str, tgt: str) -> dict:
        """Approve a relation (set status to Approved)."""
        success = self.kg.update_edge_status(src, tgt, "Approved")
        if success:
            self._record_action("approve", {"src": src, "tgt": tgt})
            return {"success": True, "message": f"Approved ({src} → {tgt})."}
        return {"success": False, "message": f"Edge ({src} → {tgt}) not found."}

    def reject_relation(self, src: str, tgt: str) -> dict:
        """Reject a relation (set status to Rejected)."""
        success = self.kg.update_edge_status(src, tgt, "Rejected")
        if success:
            self._record_action("reject", {"src": src, "tgt": tgt})
            return {"success": True, "message": f"Rejected ({src} → {tgt})."}
        return {"success": False, "message": f"Edge ({src} → {tgt}) not found."}

    # ── Find Duplicates ───────────────────────────────────────────────────────

    def find_potential_duplicates(self) -> list[tuple[str, str, float]]:
        """
        Find potential duplicate nodes by string similarity.
        Returns list of (node1, node2, similarity_score) tuples.
        """
        nodes = self.kg.nodes()
        duplicates = []

        for i, n1 in enumerate(nodes):
            for j, n2 in enumerate(nodes):
                if i >= j:
                    continue
                sim = _string_similarity(n1, n2)
                if sim > 0.6 and n1.lower() != n2.lower():
                    duplicates.append((n1, n2, sim))
                elif n1.lower() == n2.lower() and n1 != n2:
                    duplicates.append((n1, n2, 1.0))

        duplicates.sort(key=lambda x: x[2], reverse=True)
        return duplicates

    # ── History ───────────────────────────────────────────────────────────────

    def get_history(self) -> list[dict]:
        """Return action history."""
        return self.history

    def get_history_summary(self) -> dict:
        """Return summary of actions taken."""
        summary = {}
        for action in self.history:
            t = action["type"]
            summary[t] = summary.get(t, 0) + 1
        return summary


def _string_similarity(s1: str, s2: str) -> float:
    """Simple string similarity based on common characters."""
    s1_lower = s1.lower().replace(" ", "")
    s2_lower = s2.lower().replace(" ", "")

    if not s1_lower or not s2_lower:
        return 0.0

    # Check if one is a substring of the other
    if s1_lower in s2_lower or s2_lower in s1_lower:
        return max(len(s1_lower), len(s2_lower)) / (len(s1_lower) + len(s2_lower)) * 2

    # Character overlap
    common = set(s1_lower) & set(s2_lower)
    total = set(s1_lower) | set(s2_lower)
    if not total:
        return 0.0
    return len(common) / len(total)
