"""
graph_utils.py
Builds NetworkX knowledge graphs and produces Matplotlib visualisations.
"""

import networkx as nx
import matplotlib
matplotlib.use("Agg")          # headless backend – required in Streamlit
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import io


def build_graph(extracted_data: dict) -> nx.DiGraph:
    """
    Converts the LLM extraction dict into a directed NetworkX graph.

    Parameters
    ----------
    extracted_data : dict  – {"entities": [...], "relations": [...]}

    Returns
    -------
    nx.DiGraph
    """
    G = nx.DiGraph()

    # Add all entity nodes
    for entity in extracted_data.get("entities", []):
        G.add_node(entity)

    # Add edges for each relation triple (subject, predicate, object)
    for relation in extracted_data.get("relations", []):
        if len(relation) == 3:
            subj, pred, obj = relation
            G.add_edge(subj, obj, label=pred)

    return G


def visualise_diff(old_graph: nx.DiGraph,
                   new_graph: nx.DiGraph,
                   diff: dict) -> bytes:
    """
    Creates a side-by-side visualisation of old vs new graph,
    colour-coding added (green) and removed (red) elements.

    Returns the PNG image as raw bytes so Streamlit can display it.
    """
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.suptitle("Knowledge Graph Diff", fontsize=16, fontweight="bold")

    added_entities   = set(diff.get("added_entities", []))
    removed_entities = set(diff.get("removed_entities", []))
    added_rels   = {tuple(r) for r in diff.get("added_relations", [])}
    removed_rels = {tuple(r) for r in diff.get("removed_relations", [])}

    for ax, G, title in [(axes[0], old_graph, "Previous Snapshot"),
                          (axes[1], new_graph, "Updated Snapshot")]:
        ax.set_title(title, fontsize=13)

        if len(G.nodes) == 0:
            ax.text(0.5, 0.5, "No nodes", ha="center", va="center",
                    transform=ax.transAxes, fontsize=12)
            ax.axis("off")
            continue

        pos = nx.spring_layout(G, seed=42, k=1.2)

        # Node colours
        node_colours = []
        for node in G.nodes:
            if node in added_entities:
                node_colours.append("limegreen")
            elif node in removed_entities:
                node_colours.append("tomato")
            else:
                node_colours.append("steelblue")

        # Edge colours
        edge_colours = []
        for u, v in G.edges:
            edge_key = (u, v)
            label = G[u][v].get("label", "")
            triple = (u, label, v)
            if triple in added_rels:
                edge_colours.append("limegreen")
            elif triple in removed_rels:
                edge_colours.append("tomato")
            else:
                edge_colours.append("gray")

        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=node_colours,
                               node_size=1800, alpha=0.9)
        nx.draw_networkx_labels(G, pos, ax=ax, font_size=8, font_color="white",
                                font_weight="bold")
        nx.draw_networkx_edges(G, pos, ax=ax, edge_color=edge_colours,
                               arrows=True, arrowsize=20,
                               connectionstyle="arc3,rad=0.1",
                               width=2)

        # Edge labels (relation predicates)
        edge_labels = {(u, v): G[u][v].get("label", "")
                       for u, v in G.edges}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels,
                                     ax=ax, font_size=7, label_pos=0.3)
        ax.axis("off")

    # Legend
    legend_patches = [
        mpatches.Patch(color="steelblue",  label="Unchanged"),
        mpatches.Patch(color="limegreen",  label="Added"),
        mpatches.Patch(color="tomato",     label="Removed"),
    ]
    fig.legend(handles=legend_patches, loc="lower center", ncol=3,
               fontsize=11, framealpha=0.8)

    plt.tight_layout(rect=[0, 0.05, 1, 1])

    # Save to bytes buffer
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.read()
