#!/usr/bin/env python3
"""
This script reads a PlantUML file (e.g. full_graph.puml) and produces a new PlantUML file
in which any component (node) that is not referenced by any dependency edge is removed.

Usage:
    python3 remove_isolated_nodes.py input.puml output.puml

The script assumes the PlantUML file declares components with lines like:
    component "Full Module Name" as SAFE_ID
and edges with lines like:
    SAFE_ID1 --> SAFE_ID2
Only nodes (components) that are used in at least one edge (source or target) will be kept.
"""

import sys
import re

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 remove_isolated_nodes.py input.puml output.puml")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    header_lines = []
    edge_lines = []
    footer_lines = []
    
    # Dictionary to map safe id to its full module name (from component declarations).
    safeid_to_component = {}
    
    # Regular expression for a component declaration.
    comp_pattern = re.compile(r'\s*component\s+"(.+)"\s+as\s+([A-Za-z0-9_]+)')
    # Regular expression for an edge definition.
    edge_pattern = re.compile(r'\s*([A-Za-z0-9_]+)\s*-->\s*([A-Za-z0-9_]+)')
    
    # To help decide header vs edge vs footer, we assume that all edges appear in one block.
    in_edges = False

    with open(input_file, "r", encoding="utf-8") as file:
        lines = file.readlines()
        
    for line in lines:
        stripped = line.rstrip("\n")
        # Try matching a component declaration
        comp_match = comp_pattern.match(stripped)
        if comp_match:
            full_module, safeid = comp_match.groups()
            safeid_to_component[safeid] = stripped  # store the whole line
            if not in_edges:
                header_lines.append(stripped)
            else:
                footer_lines.append(stripped)
            continue
        
        if edge_pattern.match(stripped):
            in_edges = True
            edge_lines.append(stripped)
        else:
            if not in_edges:
                header_lines.append(stripped)
            else:
                footer_lines.append(stripped)
    
    # Build a set of safeIds that appear in the edge definitions
    used_ids = set()
    for edge in edge_lines:
        m = edge_pattern.match(edge)
        if m:
            src, tgt = m.groups()
            used_ids.add(src)
            used_ids.add(tgt)
    
    # Rebuild the header by filtering out any component that is not used.
    filtered_header = []
    for line in header_lines:
        m = comp_pattern.match(line)
        if m:
            _, safeid = m.groups()
            if safeid in used_ids:
                filtered_header.append(line)
            else:
                continue  # skip this isolated node
        else:
            # keep non-component header lines (for title, @startuml, comments, etc.)
            filtered_header.append(line)
    
    # Write out the new PlantUML file with the filtered header, all edges, and the original footer.
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("@startuml\n")
        # Write filtered header lines
        for line in filtered_header:
            out.write(line + "\n")
        out.write("\n' Direct dependency edges (only nodes referenced in an edge remain):\n")
        for edge in edge_lines:
            out.write(edge + "\n")
        for line in footer_lines:
            out.write(line + "\n")
    
    print(f"Output written to {output_file} – isolated nodes removed.")

if __name__ == "__main__":
    main()