#!/usr/bin/env python3
"""
This script takes an input PlantUML file (e.g., full_graph.puml) that contains all dependency
edges and removes all edges except those which are direct dependencies of a specified root module.

Usage:
    python3 filter_direct_dependencies.py input.puml output.puml ROOT_SAFE_ID

For example:
    python3 filter_direct_dependencies.py full_graph.puml direct_deps.puml github_com_containers_podman_v5

The ROOT_SAFE_ID should be the identifier of the root module used in the generated PlantUML.
"""

import sys
import re

def filter_plantuml(input_file, output_file, root_id):
    # Lists to store each line of the PlantUML file.
    header_lines = []      # all lines until first edge marker, normally components declarations
    edge_lines = []        # all edge lines
    footer_lines = []      # any lines after edges (like note or @enduml)

    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # We assume that all "component" definitions come first,
    # then edge lines; but we will split inclusive of any lines starting with a valid edge: "ID --> ID"
    edge_pattern = re.compile(r'\s*([A-Za-z0-9_]+)\s*-->\s*([A-Za-z0-9_]+)')
    in_edges = False
    for line in lines:
        if edge_pattern.match(line):
            in_edges = True
            edge_lines.append(line.rstrip("\n"))
        else:
            if not in_edges:
                header_lines.append(line.rstrip("\n"))
            else:
                footer_lines.append(line.rstrip("\n"))
    
    # Now filter all edge lines so that only edges whose source equals root_id remain.
    direct_edges = []
    for edge in edge_lines:
        m = edge_pattern.match(edge)
        if m:
            src, tgt = m.groups()
            if src == root_id:
                direct_edges.append(edge)
    
    # Now write output file. We include the header and filtered edges and footer.
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("@startuml\n")
        # Write header lines (e.g., title, components)
        for line in header_lines:
            out.write(line + "\n")
        out.write("\n' Filtered direct dependency edges:\n")
        for e in direct_edges:
            out.write(e + "\n")
        # Write footer lines (if any)
        for line in footer_lines:
            out.write(line + "\n")
    
    print(f"Filtered PlantUML written to {output_file}.")
    
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 filter_direct_dependencies.py input.puml output.puml ROOT_SAFE_ID")
        sys.exit(1)
    
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
    root_module_safe_id = sys.argv[3]
    
    filter_plantuml(input_filename, output_filename, root_module_safe_id)