#!/usr/bin/env python3
"""
This script reads a go-mod dependency graph file, filters it by allowed package prefixes,
optionally hides packages matching specified prefixes, restricts maximum dependency depth,
removes isolated nodes, and outputs the filtered dependency graph as a PlantUML file.
Each node in the diagram is rendered as a component and each edge represents a dependency connection.
Usage:
    python3 gomodgraph_plantuml.py go_mod_graph.txt output.puml --packages github.com/containers [--hide-packages github.com/containers/vendor ...] [--remove-isolated] [--max-depth=N] [--show-version]
Example:
    python3 gomodgraph_plantuml.py go_mod_graph.txt gomod_graph.puml --packages github.com/containers --hide-packages github.com/containers/vendor --remove-isolated --max-depth=3 --show-version
"""

import re
import sys
import argparse
import hashlib
import collections
import networkx as nx

# Utility: Create a safe identifier by replacing non-alphanumerics with underscores.
def safe_id(modname):
    return re.sub(r'[^A-Za-z0-9]', '_', modname)

# Utility: Convert a package prefix to its safe version.
def safe_prefix(prefix):
    return re.sub(r'[^A-Za-z0-9]', '_', prefix.rstrip("/"))

def build_graph(input_file):
    """
    Reads the go mod graph data from a file and builds a directed NetworkX graph.
    Returns:
        G (nx.DiGraph): A directed graph with nodes as original module names.
        nodes_defined (dict): Mapping of original module names to their safe IDs.
    """
    G = nx.DiGraph()
    nodes_defined = {}
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue  # Skip empty or commented lines.
                parts = line.split()
                if len(parts) != 2:
                    continue  # Skip lines that don't have exactly two modules.
                modA, modB = parts

                # Add modA only if not already added.
                if modA not in nodes_defined:
                    safe_modA = safe_id(modA)
                    nodes_defined[modA] = safe_modA
                    G.add_node(modA, safe_id=safe_modA)

                # Add modB only if not already added.
                if modB not in nodes_defined:
                    safe_modB = safe_id(modB)
                    nodes_defined[modB] = safe_modB
                    G.add_node(modB, safe_id=safe_modB)

                # Add the edge between the two nodes.
                G.add_edge(modA, modB)
    except Exception as e:
        sys.stderr.write(f"Error reading file {input_file}: {e}\n")
        sys.exit(1)
    return G, nodes_defined

def filter_graph_by_packages(G, nodes_defined, allowed_safe_prefixes, hidden_safe_prefixes, allow_all=False):
    """
    Produces a new graph that retains nodes based on allowed_safe_prefixes.
    Nodes whose safe IDs start with any of hidden_safe_prefixes are removed.
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
    Compute minimum depth for every node in graph G starting from roots.
    Roots are defined as nodes with no incoming edges.
    Returns:
        depths (dict): Mapping of node -> depth.
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
    Simplify the module name by:
      1. Removing a leading "github.com/".
      2. Removing any version information (anything after "@").
      3. seperates organisation and module name using " | ".
    """
    simplified = re.sub(r'^github\.com/', '', module_name)
    if "@" in simplified:
        simplified = simplified.split("@", 1)[0]
    simplified = simplified.strip("/")
    if "/" in simplified:
        parts = simplified.split("/", 1)
        simplified = parts[0] + " | " + parts[1]
    return simplified

def get_project_name(module_name, package_prefix):
    """
    Get project name by:
      1. Removing a leading "github.com/".
      2. Removing any version information (anything after "@").
      3. If the input contains a "|" separator, taking the substring after it.
      4. Converting all non-alphanumeric characters (including '/' and '-') to underscores.
      
    For example, given the input:
       "rootless-containers | rootlesskit/v2"
    the output will be "rootlesskit_v2".

    Note: The package_prefix parameter is currently not used in the transformation.
          It can be integrated if further customization or prefix-based logic is needed.
    """
    # If a "|" is present, use the part after the "|" symbol.
    if "|" in module_name:
        parts = module_name.split("|")
        module_name = parts[1].strip()  # Choose the substring on the right

    # Remove a leading "github.com/" if it exists.
    module_name = re.sub(r'^github\.com/', '', module_name)
    
    # Remove any version information (anything after an '@').
    module_name = module_name.split("@")[0].strip()
    
    # Replace all non-alphanumeric characters with an underscore.
    # This will replace spaces, slashes, hyphens, etc.
    project_name = re.sub(r'[^A-Za-z0-9]+', '_', module_name)
    # Remove any leading or trailing underscores
    project_name = project_name.strip('_')
    
    return f'{project_name}_' # append a dash so we don't have conflicts with the PlantUML syntax

def draw_and_save_graph_plantuml(G, nodes_defined, allowed_package_prefix, output_filename: str, show_version):
    """
    Draws the dependency graph as a PlantUML file.
    Consolidates nodes that produce the same simplified alias.
    
    Instead of creating duplicates, we map the module's simplified label (and its base alias)
    to one unique entry and then create a consolidated node. Edges between nodes are then 
    merged into a set to prevent duplicate connections.
    """
    lines = []
    lines.append("@startuml")
    config = [
        "skinparam componentStyle rectangle",
        "left to right direction",
        "title Generated Architecture of Podman",
        'legend "Naming scheme: Organisations | ProjectName"',
        "skinparam backgroundColor white",
        "skinparam ArrowFontSize 15",
        "skinparam ArrowFontBackgroundColor White"
    ]
    lines.extend(config)
    lines.append("")

    # Consolidate nodes by their simplified label.
    # Mapping from base alias (from get_project_name) to its simplified label.
    consolidated_nodes = {}
    for node in G.nodes():
        # Obtain the simplified label.
        simplified = simplify_label(node, allowed_package_prefix)
        base_alias = get_project_name(simplified, allowed_package_prefix)
        # If this node's base alias is already present, choose one common simplified label.
        if base_alias not in consolidated_nodes:
            consolidated_nodes[base_alias] = simplified

    # Write out the consolidated component definitions.
    for base_alias, simplified in consolidated_nodes.items():
        lines.append(f'component "{simplified}" as {base_alias}')

    lines.append("")

    # Consolidate edges based on the base alias.
    # These sets will store edges between consolidated nodes so duplicates are eliminated.
    consolidated_edges = set()
    for u, v in G.edges():
        u_simplified = simplify_label(u, allowed_package_prefix)
        v_simplified = simplify_label(v, allowed_package_prefix)
        u_alias = get_project_name(u_simplified, allowed_package_prefix)
        v_alias = get_project_name(v_simplified, allowed_package_prefix)
        # If both nodes consolidate to the same alias, then ignore self-loops (or decide otherwise).
        if u_alias == v_alias:
            continue
        # Optionally, include version information on the edge if desired.
        edge_comment = ""
        if show_version and "@" in v:
            version = v.split("@", 1)[1]
            edge_comment = f" : {version[:10]}"
        # Use a tuple (src, dst, edge_comment) to represent the edge uniquely.
        consolidated_edges.add((u_alias, v_alias, edge_comment))
    
    # Write out edges from the consolidated set.
    for src_alias, dst_alias, edge_comment in consolidated_edges:
        lines.append(f"{src_alias} --> {dst_alias}{edge_comment}")

    lines.append("")
    lines.append("@enduml")

    try:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"PlantUML file saved: {output_filename}")
    except Exception as e:
        sys.stderr.write(f"Error writing PlantUML file {output_filename}: {e}\n")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Filter a go-mod dependency graph and output a PlantUML component diagram."
    )
    parser.add_argument("input", help="Input file containing go mod graph output")
    parser.add_argument("output", help="Output PlantUML filename (.puml or .txt)")
    parser.add_argument(
        "--packages",
        nargs="*",
        default=[],
        help="Allowed package prefixes (e.g., 'github.com/containers'). Use '*' to allow all."
    )
    parser.add_argument(
        "--hide-packages",
        nargs="*",
        default=[],
        help="Package prefixes to hide (e.g., 'github.com/containers/vendor')."
    )
    parser.add_argument("--remove-isolated", action="store_true", help="Remove nodes with no edges")
    parser.add_argument("--max-depth", type=int, default=None, help="Maximum dependency depth to include")
    parser.add_argument("--show-version", action="store_true", help="Display version text with nodes/edges")
    args = parser.parse_args()

    package_list = args.packages if args.packages else ["*"]
    allow_all = ("*" in package_list)
    allowed_package_prefix = package_list[0] if not allow_all else ""
    allowed_safe_prefixes = [] if allow_all else [safe_prefix(pkg) for pkg in package_list]
    hidden_safe_prefixes = [safe_prefix(h) for h in args.hide_packages] if args.hide_packages else []

    # Build the dependency graph.
    G, nodes_defined = build_graph(args.input)

    # Filter the graph by allowed and hidden package prefixes.
    G_filtered = filter_graph_by_packages(G, nodes_defined, allowed_safe_prefixes, hidden_safe_prefixes, allow_all=allow_all)

    # Optionally, apply maximum depth filtering.
    if args.max_depth is not None:
        G_filtered = filter_graph_by_max_depth(G_filtered, args.max_depth)

    # Optionally, remove isolated nodes (nodes with no edges).
    if args.remove_isolated:
        isolates = list(nx.isolates(G_filtered))
        if isolates:
            G_filtered.remove_nodes_from(isolates)

    # Write out the graph as a PlantUML file.
    draw_and_save_graph_plantuml(G_filtered, nodes_defined, allowed_package_prefix, args.output, args.show_version)

if __name__ == "__main__":
    main()