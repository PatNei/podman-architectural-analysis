#!/usr/bin/env python3
"""
This script reads a go‑mod dependency graph file, filters it by allowed package prefixes,
optionally hides packages matching specified prefixes, restricts maximum dependency depth,
removes isolated nodes, and visualizes the filtered dependency graph as an interactive HTML file
using pyvis.

Usage:
    python3 gomodgraph_pyvis.py go_mod_graph.txt output.html --packages github.com/containers [--hide-packages github.com/containers/vendor ...] [--remove-isolated] [--max-depth=N] [--show-version]

Example:
    python3 gomodgraph_pyvis.py go_mod_graph.txt gomod_pyvis.html --packages github.com/containers --hide-packages github.com/containers/vendor --remove-isolated --max-depth=3 --show-version

For more details on pyvis, see [1] and [2].
"""

import re
import sys
import argparse
import hashlib
import collections
import networkx as nx
from pyvis.network import Network


# Utility: Create a safe identifier by replacing non-alphanumerics with underscores.
def safe_id(modname):
    return re.sub(r'[^A-Za-z0-9]', '_', modname)


# Utility: Convert a package prefix to its safe version.
def safe_prefix(prefix):
    return re.sub(r'[^A-Za-z0-9]', '_', prefix.rstrip("/"))


# Deterministically assign a color to a package using MD5 hash.
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
                continue  # Skip lines that do not have exactly two modules.
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


def filter_graph_by_packages(G, nodes_defined, allowed_safe_prefixes, hidden_safe_prefixes, allow_all=False):
    """
    Produces a new graph that retains only nodes whose safe IDs begin with one of the allowed_safe_prefixes,
    unless allowed is "*" (i.e., allow_all=True). Then, it removes any nodes whose safe IDs begin with any
    of the hidden_safe_prefixes. Only edges where both endpoints are retained are added.
    
    Returns:
        G_filtered (nx.DiGraph): The filtered graph.
    """
    if allow_all:
        allowed_nodes = set(G.nodes())
    else:
        allowed_nodes = {node for node, safe in nodes_defined.items()
                         if any(safe.startswith(prefix) for prefix in allowed_safe_prefixes)}
    # Remove nodes that should be hidden.
    if hidden_safe_prefixes:
        allowed_nodes = {node for node in allowed_nodes
                         if not any(nodes_defined[node].startswith(prefix) for prefix in hidden_safe_prefixes)}
    
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


def simplify_label(module_name, package_prefix):
    """
    Simplify the module name:
      1. Remove any leading "github.com/".
      2. Remove any version information from the module name (i.e., anything after "@").
      3. Insert a newline between the organization and project.
    """
    simplified = re.sub(r'^github\.com/', '', module_name)
    if "@" in simplified:
        simplified = simplified.split("@", 1)[0]
    simplified = simplified.strip("/")
    if "/" in simplified:
        parts = simplified.split("/", 1)
        simplified = parts[0] + "\n" + parts[1]
    return simplified


def draw_and_save_graph_pyvis(G, nodes_defined, allowed_package_prefix, palette, output_filename:str, show_version):
    """
    Draws the graph using pyvis, creates an interactive HTML file.
    Each node is assigned a unique color.
    Node labels are simplified to remove version information and formatted over multiple lines.
    
    Parameters:
        G: The filtered NetworkX graph.
        nodes_defined: Mapping of original module names to safe IDs.
        allowed_package_prefix: The primary allowed package prefix (used for label simplification).
        palette: List of color names.
        output_filename: Path to the output HTML file.
        show_version: Boolean flag to include version text as tooltip for edges.
    """
    # Set custom sizes to fill viewport.
    # SIZE_W= "500px" 
    # SIZE_H="500px"
    SIZE_W= "100dvw" 
    SIZE_H="90dvh"
    heading = output_filename.split(".html")[0]
    net = Network(height=SIZE_H, width=SIZE_W, directed=True,filter_menu=True)
    net.force_atlas_2based()  # Alternatively, use a different physics model.
    
    # Create a node-to-color mapping using each node's name hashed to pick a color.
    node_color_mapping = {}
    for node in G.nodes():
        node_color_mapping[node] = assign_color(node, palette)
    
    # Add nodes to pyvis graph.
    for node in G.nodes():
        version = ""
        if show_version and "@" in node:
            version_text = node.split("@", 1)[1]
            # print(version_text)
            version = f"{version_text[:min(len(version_text), 10)]}\n"
        label = f"{version}{simplify_label(node, allowed_package_prefix)}"
        net.add_node(node, label=label, title=label, color=node_color_mapping[node])
    # Add edges to pyvis graph.
    for u, v in G.edges():
        version = ""
        if show_version and "@" in v:
            version_text = v.split("@", 1)[1]
            version = version_text[:min(len(version_text), 10)]
        net.add_edge(u, v, title=version, color=node_color_mapping.get(u, "black"))
    
    # Optionally, configure physics/layout options.
    net.toggle_physics(True)
    net.toggle_drag_nodes(True)
    net.toggle_stabilization(True)
    # net.show_buttons(filter_=["edges"])
    net.set_options("""
    var options = {
        "physics": {
            "forceAtlas2Based": {
                "theta": 0.45,
                "gravitationalConstant": -79,
                "springLength": 10,
                "springConstant": 0.15,
                "damping": 0.45,
                "avoidOverlap": 1
            },
            "minVelocity": 0.75,
            "solver": "forceAtlas2Based"
        }
    }
    """)
    # Force use of the default HTML template by disabling notebook mode.
    net.show(output_filename, notebook=False)
    print(f"Graph saved as interactive HTML: {output_filename}")


def main():
    parser = argparse.ArgumentParser(
        description="Filter a go-mod dependency graph by allowed package prefixes, hide certain packages, "
                    "optionally restrict maximum depth, remove isolated nodes, and output an interactive HTML visualization using pyvis."
    )
    parser.add_argument("input", help="Input file containing go mod graph output")
    parser.add_argument("output", help="Output HTML filename")
    parser.add_argument(
        "--packages",
        nargs="*",
        default=[],
        help="Allowed package prefixes (e.g., 'github.com/containers'). Use '*' to allow all. If not provided, no filtering by package is applied."
    )
    parser.add_argument(
        "--hide-packages",
        nargs="*",
        default=[],
        help="Package prefixes to hide (e.g., 'github.com/containers/vendor')."
    )
    parser.add_argument("--remove-isolated", action="store_true", help="Remove nodes with no edges")
    parser.add_argument("--max-depth", type=int, default=None, help="Maximum dependency depth to include (default: include all depths)")
    parser.add_argument("--show-version", action="store_true", help="Display version text on edges")
    args = parser.parse_args()

    # Allowed packages: if not provided, default to ["*"] to allow all.
    package_list = args.packages if args.packages else ["*"]
    allow_all = ("*" in package_list)
    # Use the first package prefix for label simplification.
    allowed_package_prefix = package_list[0] if not allow_all else ""
    allowed_safe_prefixes = [] if allow_all else [safe_prefix(pkg) for pkg in package_list]

    # Process hidden package prefixes.
    hidden_safe_prefixes = [safe_prefix(h) for h in args.hide_packages] if args.hide_packages else []

    palette = ["green", "red", "orange", "purple", "brown", "olive", "teal", "maroon"]

    # Build and filter the dependency graph.
    G, nodes_defined = build_graph(args.input)
    G_filtered = filter_graph_by_packages(G, nodes_defined, allowed_safe_prefixes, hidden_safe_prefixes, allow_all=allow_all)
    
    if args.max_depth is not None:
        G_filtered = filter_graph_by_max_depth(G_filtered, args.max_depth)
    if args.remove_isolated:
        isolates = list(nx.isolates(G_filtered))
        if isolates:
            G_filtered.remove_nodes_from(isolates)
    
    # Visualize and save the graph with pyvis.
    draw_and_save_graph_pyvis(G_filtered, nodes_defined, allowed_package_prefix, palette, args.output, args.show_version)


if __name__ == "__main__":
    main()