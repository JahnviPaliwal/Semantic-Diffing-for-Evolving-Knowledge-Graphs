"""
backend/graph_utils.py
NetworkX graph construction + Matplotlib diff visualisation + JSON export.
"""
import io, base64
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import to_rgba


# ── Palette ──────────────────────────────────────────────────────────────────
ADD_NODE  = '#1D9E75'
ADD_EDGE  = '#1D9E75'
REM_NODE  = '#D85A30'
REM_EDGE  = '#D85A30'
NEU_NODE  = '#5a7fa8'
NEU_EDGE  = '#9aa8b8'
BG        = '#0f1117'
TEXT_COL  = '#e8e6e0'


def build_graph(extracted_data: dict) -> nx.DiGraph:
    """Build a directed NetworkX graph from extraction output."""
    G = nx.DiGraph()
    for entity in extracted_data.get('entities', []):
        G.add_node(entity)
    for rel in extracted_data.get('relations', []):
        if len(rel) == 3:
            subj, pred, obj = rel
            G.add_edge(subj, obj, label=pred)
    return G


def visualise_diff(old_graph: nx.DiGraph,
                   new_graph: nx.DiGraph,
                   diff: dict) -> str:
    """
    Render a side-by-side diff visualisation.
    Returns a base64-encoded PNG string.
    """
    added_ents   = set(diff.get('added_entities', []))
    removed_ents = set(diff.get('removed_entities', []))
    added_rels   = {tuple(r) for r in diff.get('added_relations', [])}
    removed_rels = {tuple(r) for r in diff.get('removed_relations', [])}

    fig, axes = plt.subplots(1, 2, figsize=(18, 8), facecolor=BG)
    fig.suptitle('Knowledge Graph Diff', fontsize=15, fontweight='bold',
                 color=TEXT_COL, y=0.98)

    pairs = [(axes[0], old_graph, 'Baseline  (v1)'),
             (axes[1], new_graph, 'Updated  (v2)')]

    for ax, G, title in pairs:
        ax.set_facecolor(BG)
        ax.set_title(title, fontsize=12, color=TEXT_COL, pad=10)
        ax.axis('off')

        if len(G.nodes) == 0:
            ax.text(0.5, 0.5, 'No entities extracted',
                    ha='center', va='center', transform=ax.transAxes,
                    fontsize=11, color=TEXT_COL, alpha=0.5)
            continue

        pos = nx.spring_layout(G, seed=42, k=1.6)

        # Node colours
        node_colours = []
        node_sizes   = []
        for node in G.nodes:
            if node in added_ents:
                node_colours.append(ADD_NODE)
                node_sizes.append(2400)
            elif node in removed_ents:
                node_colours.append(REM_NODE)
                node_sizes.append(2400)
            else:
                node_colours.append(NEU_NODE)
                node_sizes.append(2000)

        # Edge colours
        edge_colours = []
        edge_widths  = []
        for u, v in G.edges:
            label = G[u][v].get('label', '')
            triple = (u, label, v)
            if triple in added_rels:
                edge_colours.append(ADD_EDGE)
                edge_widths.append(2.5)
            elif triple in removed_rels:
                edge_colours.append(REM_EDGE)
                edge_widths.append(2.5)
            else:
                edge_colours.append(NEU_EDGE)
                edge_widths.append(1.2)

        nx.draw_networkx_nodes(G, pos, ax=ax,
                               node_color=node_colours,
                               node_size=node_sizes, alpha=0.92)
        nx.draw_networkx_labels(G, pos, ax=ax,
                                font_size=7.5, font_color='white',
                                font_weight='bold')
        nx.draw_networkx_edges(G, pos, ax=ax,
                               edge_color=edge_colours,
                               width=edge_widths,
                               arrows=True, arrowsize=18,
                               connectionstyle='arc3,rad=0.12',
                               min_source_margin=18, min_target_margin=18)
        edge_labels = {(u, v): G[u][v].get('label', '') for u, v in G.edges}
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, ax=ax,
                                     font_size=6.5, font_color=TEXT_COL,
                                     label_pos=0.35, alpha=0.85)

    # Legend
    legend_handles = [
        mpatches.Patch(color=NEU_NODE,  label='Unchanged node'),
        mpatches.Patch(color=ADD_NODE,  label='Added node'),
        mpatches.Patch(color=REM_NODE,  label='Removed node'),
        mpatches.Patch(color=NEU_EDGE,  label='Unchanged edge'),
        mpatches.Patch(color=ADD_EDGE,  label='Added edge'),
        mpatches.Patch(color=REM_EDGE,  label='Removed edge'),
    ]
    fig.legend(handles=legend_handles, loc='lower center', ncol=6,
               fontsize=9, framealpha=0.25, facecolor=BG,
               labelcolor=TEXT_COL, edgecolor='none')
    plt.tight_layout(rect=[0, 0.06, 1, 0.97])

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130, bbox_inches='tight',
                facecolor=BG)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def graph_to_json(G: nx.DiGraph) -> dict:
    """Export graph as a node/edge list for D3 rendering in the frontend."""
    nodes = [{'id': n} for n in G.nodes]
    links = [{'source': u, 'target': v, 'label': G[u][v].get('label', '')}
             for u, v in G.edges]
    return {'nodes': nodes, 'links': links}
