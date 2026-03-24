"""
knowledge_graph.py — Dynamic Knowledge Graph Construction & Visualisation.

Uses NetworkX for graph logic and PyVis for interactive rendering.
Stores an enriched attributed graph with domain metadata.
"""

from __future__ import annotations

import io
import os
import json
import random
import networkx as nx
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from utils import get_logger, domain_color, edge_color

logger = get_logger(__name__)

# ─── Colour Map ───────────────────────────────────────────────────────────────

RELATION_PALETTE = {
    "IS_A":        "#6C63FF",
    "SUBCLASS_OF": "#FF6584",
    "RELATED_TO":  "#43B89C",
    "PART_OF":     "#F9C74F",
    "USES":        "#00D4AA",
    "INCLUDES":    "#A78BFA",
    "DEVELOPED":   "#FB923C",
    "INFERRED":    "#FFA552",
    "INHERITS_FROM": "#A8DADC",
    "default":     "#CCCCCC",
}

DOMAIN_NODE_PALETTE = {
    "AI":         "#6C63FF",
    "Healthcare": "#43B89C",
    "Physics":    "#FF8C42",
    "Law":        "#FF6584",
    "DataScience": "#2D6CDF",
    "Agriculture and Climatic science": "#6A994E",
    "General":    "#A8DADC",
    "default":    "#A8DADC",
}


class KnowledgeGraph:
    """
    Enriched directed knowledge graph.

    Each node carries a 'domain' attribute.
    Each edge carries a 'relation', 'confidence', and optional 'inferred' flag.
    """

    def __init__(self):
        self.graph: nx.DiGraph = nx.DiGraph()

    # ── Population ────────────────────────────────────────────────────────────

    def add_node(self, name: str, domain: str = "General") -> None:
        if not self.graph.has_node(name):
            self.graph.add_node(name, domain=domain)
            logger.info(f"KG: added node '{name}' (domain={domain})")
        else:
            # Optionally update domain if not General
            if domain != "General":
                self.graph.nodes[name]["domain"] = domain

    def add_edge(
        self,
        src: str,
        tgt: str,
        relation: str,
        confidence: float = 0.85,
        inferred: bool = False,
        domain: str = "General",
        status: str = "Pending",
    ) -> None:
        self.add_node(src, domain=domain)
        self.add_node(tgt, domain=domain)
        self.graph.add_edge(
            src, tgt,
            relation=relation,
            confidence=confidence,
            inferred=inferred,
            status=status,
        )
        logger.info(
            f"KG: {'[INFERRED] ' if inferred else ''}edge "
            f"({src} --{relation}--> {tgt}) conf={confidence:.2f}"
        )

    def load_triples(self, triples: list[dict], domain: str = "General") -> None:
        for t in triples:
            inferred = t.get("type") == "INFERRED" or t.get("inferred", False)
            self.add_edge(
                t["subject"], t["object"], t["relation"],
                confidence=t.get("confidence", 0.85),
                inferred=inferred, domain=domain,
                status=t.get("status", "Pending"),
            )

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_neighbors(self, node: str) -> list[str]:
        if self.graph.has_node(node):
            return list(self.graph.neighbors(node))
        return []

    def get_predecessors(self, node: str) -> list[str]:
        if self.graph.has_node(node):
            return list(self.graph.predecessors(node))
        return []

    def nodes(self) -> list[str]:
        return list(self.graph.nodes())

    def edges(self) -> list[tuple]:
        return [(u, v, d) for u, v, d in self.graph.edges(data=True)]

    def summary(self) -> dict:
        domains = {}
        for n, d in self.graph.nodes(data=True):
            dom = d.get("domain", "General")
            domains[dom] = domains.get(dom, 0) + 1
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "domains": domains,
        }

    def get_triples_as_dicts(self) -> list[dict]:
        """Return all edges as a list of dicts for table display."""
        triples = []
        for u, v, d in self.graph.edges(data=True):
            triples.append({
                "Entity1": u,
                "Relation": d.get("relation", "RELATED_TO"),
                "Entity2": v,
                "Confidence": d.get("confidence", 0.85),
                "Status": d.get("status", "Pending"),
                "Inferred": d.get("inferred", False),
            })
        return triples

    # ── Graph Modification ────────────────────────────────────────────────────

    def merge_nodes(self, old_name: str, new_name: str) -> int:
        """Merge old_name into new_name, transferring all edges. Returns count of edges updated."""
        if not self.graph.has_node(old_name):
            return 0

        count = 0
        old_domain = self.graph.nodes[old_name].get("domain", "General")

        # Ensure new node exists
        self.add_node(new_name, domain=old_domain)

        # Transfer outgoing edges
        for _, tgt, data in list(self.graph.out_edges(old_name, data=True)):
            if tgt != new_name:
                self.graph.add_edge(new_name, tgt, **data)
                count += 1

        # Transfer incoming edges
        for src, _, data in list(self.graph.in_edges(old_name, data=True)):
            if src != new_name:
                self.graph.add_edge(src, new_name, **data)
                count += 1

        # Remove old node
        self.graph.remove_node(old_name)
        logger.info(f"Merged '{old_name}' → '{new_name}', updated {count} edges.")
        return count

    def update_edge_relation(self, src: str, tgt: str, new_relation: str) -> bool:
        """Update the relation type of an edge."""
        if self.graph.has_edge(src, tgt):
            self.graph[src][tgt]["relation"] = new_relation
            logger.info(f"Updated edge ({src} → {tgt}) relation to {new_relation}")
            return True
        return False

    def update_edge_status(self, src: str, tgt: str, new_status: str) -> bool:
        """Update the status of an edge."""
        if self.graph.has_edge(src, tgt):
            self.graph[src][tgt]["status"] = new_status
            logger.info(f"Updated edge ({src} → {tgt}) status to {new_status}")
            return True
        return False

    def delete_edge(self, src: str, tgt: str) -> bool:
        """Delete an edge from the graph."""
        if self.graph.has_edge(src, tgt):
            self.graph.remove_edge(src, tgt)
            logger.info(f"Deleted edge ({src} → {tgt})")
            # Remove orphan nodes
            for n in [src, tgt]:
                if self.graph.has_node(n) and self.graph.degree(n) == 0:
                    self.graph.remove_node(n)
            return True
        return False

    def add_new_edge(self, src: str, tgt: str, relation: str,
                     confidence: float = 0.9, domain: str = "General") -> None:
        """Add a new manual edge."""
        self.add_edge(src, tgt, relation, confidence=confidence,
                      domain=domain, status="Approved")

    # ── Subgraph Extraction ───────────────────────────────────────────────────

    def get_subgraph(self, center_node: str, depth: int = 2) -> "KnowledgeGraph":
        """Extract a subgraph around center_node up to `depth` hops."""
        if not self.graph.has_node(center_node):
            return KnowledgeGraph()

        nodes_to_include = {center_node}
        frontier = {center_node}
        for _ in range(depth):
            next_frontier = set()
            for n in frontier:
                next_frontier.update(self.graph.neighbors(n))
                next_frontier.update(self.graph.predecessors(n))
            nodes_to_include.update(next_frontier)
            frontier = next_frontier

        sub = KnowledgeGraph()
        for n in nodes_to_include:
            if self.graph.has_node(n):
                sub.add_node(n, self.graph.nodes[n].get("domain", "General"))
        for u, v, d in self.graph.edges(data=True):
            if u in nodes_to_include and v in nodes_to_include:
                sub.graph.add_edge(u, v, **d)
        return sub

    # ── Visualisation ─────────────────────────────────────────────────────────

    def render_matplotlib(
        self,
        title: str = "Knowledge Graph",
        figsize: tuple[int, int] = (14, 9),
        show_inferred: bool = True,
    ) -> io.BytesIO:
        """Render graph as Matplotlib PNG buffer."""
        edges_to_draw = [
            (u, v, d) for u, v, d in self.graph.edges(data=True)
            if show_inferred or not d.get("inferred", False)
        ]
        display_graph = nx.DiGraph()
        for n, data in self.graph.nodes(data=True):
            display_graph.add_node(n, **data)
        for u, v, d in edges_to_draw:
            display_graph.add_edge(u, v, **d)

        # Keep rendering bounded for very large graphs.
        max_nodes = 250
        max_edges = 700
        sampled = False
        if (
            display_graph.number_of_nodes() > max_nodes
            or display_graph.number_of_edges() > max_edges
        ):
            sampled = True
            top_nodes = [
                n for n, _ in sorted(
                    display_graph.degree,
                    key=lambda item: item[1],
                    reverse=True,
                )[:max_nodes]
            ]
            display_graph = display_graph.subgraph(top_nodes).copy()

            if display_graph.number_of_edges() > max_edges:
                ranked_edges = sorted(
                    display_graph.edges(data=True),
                    key=lambda e: e[2].get("confidence", 0.0),
                    reverse=True,
                )
                slim = nx.DiGraph()
                for n, data in display_graph.nodes(data=True):
                    slim.add_node(n, **data)
                for u, v, d in ranked_edges[:max_edges]:
                    slim.add_edge(u, v, **d)
                display_graph = slim

        fig, ax = plt.subplots(figsize=figsize)
        fig.patch.set_facecolor("#F8FAFC")
        ax.set_facecolor("#F8FAFC")

        pos = nx.spring_layout(display_graph, seed=42, k=2.5, iterations=35)

        node_colors = [
            DOMAIN_NODE_PALETTE.get(
                display_graph.nodes[n].get("domain", "General"),
                DOMAIN_NODE_PALETTE["default"]
            )
            for n in display_graph.nodes()
        ]
        nx.draw_networkx_nodes(
            display_graph, pos,
            node_color=node_colors,
            node_size=2800, alpha=0.95, ax=ax,
        )
        nx.draw_networkx_labels(
            display_graph, pos,
            font_size=9, font_color="#1E293B", font_weight="bold", ax=ax,
        )

        edge_groups: dict[str, list] = {}
        for u, v, d in display_graph.edges(data=True):
            rel = "INFERRED" if d.get("inferred") else d.get("relation", "default")
            edge_groups.setdefault(rel, []).append((u, v))

        for rel, edge_list in edge_groups.items():
            color = RELATION_PALETTE.get(rel, RELATION_PALETTE["default"])
            nx.draw_networkx_edges(
                display_graph, pos,
                edgelist=edge_list,
                edge_color=color, arrows=True,
                arrowsize=20, width=2.2,
                connectionstyle="arc3,rad=0.1", ax=ax,
            )

        edge_label_map = {}
        for u, v, d in display_graph.edges(data=True):
            lbl = "INFERRED" if d.get("inferred") else d.get("relation", "")
            edge_label_map[(u, v)] = lbl
        if display_graph.number_of_edges() <= 220:
            nx.draw_networkx_edge_labels(
                display_graph, pos,
                edge_labels=edge_label_map,
                font_size=7, font_color="#334155",
                bbox=dict(boxstyle="round,pad=0.2", fc="#E2E8F0", alpha=0.8),
                ax=ax,
            )

        legend_patches = [
            mpatches.Patch(color=c, label=r)
            for r, c in RELATION_PALETTE.items() if r != "default"
        ]
        ax.legend(
            handles=legend_patches, loc="lower left",
            fontsize=8, framealpha=0.4,
            labelcolor="#1E293B", facecolor="#F1F5F9",
        )
        final_title = title
        if sampled:
            final_title = f"{title} (sampled view for performance)"
        ax.set_title(final_title, color="#1E293B", fontsize=14, fontweight="bold", pad=12)
        ax.axis("off")
        plt.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=130, bbox_inches="tight",
                    facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf

    def render_pyvis_html(self, height: str = "600px", width: str = "100%",
                          notebook: bool = False) -> str:
        """Render graph as interactive PyVis HTML string."""
        from pyvis.network import Network

        net = Network(height=height, width=width, directed=True,
                      bgcolor="#F8FAFC", font_color="#1E293B",
                      notebook=notebook)
        net.barnes_hut(gravity=-8000, central_gravity=0.3,
                       spring_length=200, spring_strength=0.01)

        for n, data in self.graph.nodes(data=True):
            dom = data.get("domain", "General")
            color = DOMAIN_NODE_PALETTE.get(dom, DOMAIN_NODE_PALETTE["default"])
            net.add_node(n, label=n, color=color, size=30,
                         title=f"{n}\nDomain: {dom}",
                         font={"size": 14, "color": "#1E293B"})

        for u, v, data in self.graph.edges(data=True):
            rel = data.get("relation", "RELATED_TO")
            conf = data.get("confidence", 0.85)
            color = RELATION_PALETTE.get(rel, RELATION_PALETTE["default"])
            width = max(1, conf * 4)
            net.add_edge(u, v, label=rel, color=color, width=width,
                         title=f"{rel}\nConfidence: {conf:.2f}")

        html = net.generate_html()
        return html

    def export_json(self) -> str:
        """Export graph data as JSON."""
        data = {
            "nodes": [
                {"id": n, "domain": d.get("domain", "General")}
                for n, d in self.graph.nodes(data=True)
            ],
            "edges": [
                {
                    "source": u, "target": v,
                    "relation": d.get("relation", ""),
                    "confidence": d.get("confidence", 0.85),
                    "status": d.get("status", "Pending"),
                    "inferred": d.get("inferred", False),
                }
                for u, v, d in self.graph.edges(data=True)
            ],
        }
        return json.dumps(data, indent=2)
