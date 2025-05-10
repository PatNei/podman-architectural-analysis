#!/usr/bin/env python3
"""
This script reads a go‑mod dependency graph file, filters it by allowed organization prefixes,
optionally restricts maximum dependency depth, removes isolated nodes, and visualizes the filtered 
dependency graph as a PNG. Arrow endpoints are manually adjusted so that arrows connect at
node borders rather than their centers. With the scaling changes, the full name can be placed
inside the node. The simplify label function also inserts a newline between the organization 
and the project name.
 
Usage:
    python3 gomodgraph.networkx.py go_mod_graph.txt output.png "github.com/containers" [--remove-isolated] [--max-depth=N] [--show-version]
Example:
    python3 gomodgraph.networkx.py go_mod_graph.txt gomod_networkx.png "github.com/containers" --remove-isolated --max-depth=3 --show-version
"""

import re
import sys
import argparse
import hashlib
import collections
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch

# Utility: Create a safe identifier by replacing non-alphanumerics with underscores.
def safe_id(modname):
    return re.sub(r'[^A-Za-z0-9]', '_', modname)

# Utility: Convert an organization prefix to its safe version.
def safe_prefix(org_prefix):
    return re.sub(r'[^A-Za-z0-9]', '_', org_prefix.rstrip("/"))

# Deterministically assign a color to an org prefix using MD5 hash.
def assign_color(prefix, palette):
    h = hashlib.md5(prefix.encode("utf-8")).hexdigest()
    index = int(h[:8], 16) % len(palette)
    return palette[index]

# Build the full dependency graph from file.
def build_graph(input_file):
    """
    Reads the go mod graph data from a file and builds a directed NetworkX graph.
    
    Returns:
        G (nx.DiGraph): A directed graph with nodes as original module names.
        nodes_defined (dict): Mapping of original module names to their safe IDs.
    """
    G = nx.DiGraph()
    nodes_defined = {}
    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue  # Skip empty lines or comments.
            parts = line.split()
            if len(parts) != 2:
                continue  # Skip if line does not have exactly two modules.
            modA, modB = parts
            # Record nodes (if not already added).
            if modA not in nodes_defined:
                nodes_defined[modA] = safe_id(modA)
                G.add_node(modA, safe_id=nodes_defined[modA])
            if modB not in nodes_defined:
                nodes_defined[modB] = safe_id(modB)
                G.add_node(modB, safe_id=nodes_defined[modB])
            # Add directed edge.
            G.add_edge(modA, modB)
    return G, nodes_defined

def filter_graph_by_orgs(G, nodes_defined, allowed_safe_prefixes, allow_all=False):
    """
    Produces a new graph that retains only nodes whose safe IDs start with one of the allowed_safe_prefixes and
    only adds edges where both endpoints are among these nodes.
    If allow_all is True, no filtering is done.
    
    Returns:
        G_filtered (nx.DiGraph): The filtered graph.
    """
    if allow_all:
        return G.copy()

    allowed_nodes = {node for node, safe in nodes_defined.items() 
                     if any(safe.startswith(prefix) for prefix in allowed_safe_prefixes)}
    
    G_filtered = nx.DiGraph()
    for node in allowed_nodes:
        G_filtered.add_node(node, safe_id=nodes_defined[node])
    
    for u, v in G.edges():
        if u in allowed_nodes and v in allowed_nodes:
            G_filtered.add_edge(u, v)
    
    return G_filtered

def compute_depths(G):
    """
    Compute the minimum depth for every node in graph G starting from roots.
    Roots are defined as nodes with no incoming edges.
    
    Returns:
        depths (dict): Mapping node -> depth.
    """
    depths = {}
    roots = [node for node in G.nodes() if G.in_degree(node) == 0]
    if not roots:
        roots = list(G.nodes())
    queue = collections.deque()
    for r in roots:
        depths[r] = 0
        queue.append(r)
    while queue:
        node = queue.popleft()
        for neighbor in G.successors(node):
            if neighbor not in depths or depths[node] + 1 < depths[neighbor]:
                depths[neighbor] = depths[node] + 1
                queue.append(neighbor)
    return depths

def filter_graph_by_max_depth(G, max_depth):
    """
    Returns a subgraph of G containing only nodes with depth <= max_depth.
    """
    depths = compute_depths(G)
    nodes_in_range = {node for node, depth in depths.items() if depth <= max_depth}
    return G.subgraph(nodes_in_range).copy()

def simplify_label(module_name, org_prefix):
    """
    Simplify the module name:
      1. Remove any leading "github.com/".
      2. Remove any version information from the module name (i.e., anything after "@").
      3. Split the remaining text at the first "/" to insert a newline between the organization and project.
         For instance, "containers/podman" becomes "containers\npodman".
    """
    # Remove leading "github.com/" if present.
    simplified = re.sub(r'^github\.com/', '', module_name)
    
    # Remove version info.
    if "@" in simplified:
        simplified = simplified.split("@", 1)[0]
    
    simplified = simplified.strip("/")
    
    # Insert a newline between the organization and project.
    if "/" in simplified:
        parts = simplified.split("/", 1)
        simplified = parts[0] + "\n" + parts[1]
    
    return simplified

def draw_and_save_graph(G, nodes_defined, allowed_org_prefix, palette, output_filename, show_version):
    """
    Draws the graph with manually adjusted arrows so that they start and end at the node borders.
    Each node is assigned a unique color (used for the node fill and for all its outgoing arrows).
    If show_version is True, version text (if any) is displayed along each edge with lower opacity.
    Node labels are simplified (with no version information) and formatted over multiple lines.
    
    Parameters:
        G: The filtered NetworkX graph.
        nodes_defined: Mapping of original module names to safe IDs.
        allowed_org_prefix: The raw organization prefix (e.g., "github.com/containers/")
                            to remove from node labels.
        palette: List of color names.
        output_filename: Path to the output PNG file.
        show_version: Boolean flag that controls whether version text is displayed on edges.
    """
    import numpy as np
    from matplotlib.patches import FancyArrowPatch

    default_edge_color = "gray"
    
    # Create a node-to-color mapping using each node's name (hashed) to pick a color.
    node_color_mapping = {}
    for node in G.nodes():
        # Here we use the assign_color function by passing the node's name.
        node_color_mapping[node] = assign_color(node, palette)
    
    # Use graphviz layout for left-to-right, or fall back to spring layout.
    try:
        pos = nx.nx_agraph.graphviz_layout(G, prog="dot", args="-Grankdir=LR")
    except Exception:
        pos = nx.spring_layout(G, k=5, iterations=50)
    
    # Create simplified multiline labels.
    labels = {node: simplify_label(node, allowed_org_prefix) for node in G.nodes()}
    
    fig, ax = plt.subplots(figsize=(16, 12))
    
    # Set node colors from the node_color_mapping.
    node_colors = [node_color_mapping[node] for node in G.nodes()]
    nx.draw_networkx_nodes(G, pos, node_color=node_colors, node_size=2500, ax=ax)
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=8, font_color="black", ax=ax)
    
    for u, v in G.edges():
        # Use the color of the source node for the arrow.
        edge_color = node_color_mapping.get(u, default_edge_color)
        
        src = np.array(pos[u])
        tgt = np.array(pos[v])
        
        vec = tgt - src
        distance = np.linalg.norm(vec)
        if distance == 0:
            continue
        direction = vec / distance
        
        # Offset so that arrows start/end at node borders.
        offset = 0.05 * distance  
        new_src = src + direction * offset
        new_tgt = tgt - direction * offset
        
        arrow = FancyArrowPatch(tuple(new_src), tuple(new_tgt),
                                arrowstyle="-|>",
                                mutation_scale=12,
                                color=edge_color,
                                lw=1)
        arrow.set_zorder(2)
        ax.add_patch(arrow)
        
        # Draw version text along the edge if the flag --show-version is provided.
        if show_version:
            version_text = ""
            if "@" in v:
                version_text = v.split("@", 1)[1]
            if version_text:
                version_text = version_text[:min(len(version_text),10)]
                midpoint = (new_src + new_tgt) / 2.0
                ax.text(midpoint[0], midpoint[1], version_text,
                        fontsize=6, color="black", alpha=0.5,
                        horizontalalignment='',
                        verticalalignment='center')
    
    ax.set_title("Go Module Dependency Graph (Filtered)", fontsize=16)
    ax.axis("off")
    plt.tight_layout()
    plt.savefig(output_filename, format="PNG")
    print(f"Graph saved as {output_filename}")
    plt.show()
def main():
    parser = argparse.ArgumentParser(
        description="Filter a go-mod dependency graph by allowed organization prefixes, "
                    "optionally restrict maximum depth, remove isolated nodes, and output a PNG visualization."
    )
    parser.add_argument("input", help="Input file containing go mod graph output")
    parser.add_argument("output", help="Output PNG filename")
    parser.add_argument("orgs", help="Comma-separated allowed organization prefixes (e.g., 'github.com/containers' or '*' to allow all)")
    parser.add_argument("--remove-isolated", action="store_true", help="Remove nodes with no edges")
    parser.add_argument("--max-depth", type=int, default=None, help="Maximum dependency depth to include (default: include all depths)")
    parser.add_argument("--show-version", action="store_true", help="Display version text on edges")
    args = parser.parse_args()
    
    org_list = [o.strip() for o in args.orgs.split(",") if o.strip()]
    allow_all = ("*" in org_list)
    allowed_org_prefix = org_list[0] if not allow_all else ""
    allowed_safe_prefixes = [] if allow_all else [safe_prefix(o) for o in org_list]
    
    palette = ["green", "red", "orange", "purple",
               "brown", "olive", "teal", "maroon"]
    
    G, nodes_defined = build_graph(args.input)
    G_filtered = filter_graph_by_orgs(G, nodes_defined, allowed_safe_prefixes, allow_all=allow_all)
    
    if args.max_depth is not None:
        G_filtered = filter_graph_by_max_depth(G_filtered, args.max_depth)
    
    if args.remove_isolated:
        isolates = list(nx.isolates(G_filtered))
        if isolates:
            G_filtered.remove_nodes_from(isolates)
    
    draw_and_save_graph(G_filtered, nodes_defined, allowed_org_prefix, palette, args.output, args.show_version)

if __name__ == "__main__":
    main()