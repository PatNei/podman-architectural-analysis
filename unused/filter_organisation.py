#!/usr/bin/env python3
"""
This script reads a full PlantUML dependency graph file (generated from go‑mod)
and outputs a new PlantUML diagram that includes only dependencies within a specific
organization (e.g. "github.com/containers"). That is, only edges with both endpoints
whose full module names start with a given prefix will be included.

Usage:
    python3 filter_containers_dependencies.py input.puml output.puml ORG_PREFIX

For example:
    python3 filter_containers_dependencies.py full_graph.puml filtered_graph.puml github.com/containers

This will output only the dependencies among modules whose names begin with "github.com/containers".
"""

import sys
import re

def main():
    if len(sys.argv) != 4:
        print("Usage: python3 filter_containers_dependencies.py input.puml output.puml ORG_PREFIX")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2]
    org_prefix = sys.argv[3].rstrip("/")  # remove trailing slash if present

    header_lines = []
    edge_lines = []
    footer_lines = []
    
    # Dictionary to map safe id to its full module name.
    safeid_to_full = {}
    
    # Regular expression to match component declarations in the PlantUML file.
    # Expected format: component "FULL_MODULE_NAME" as SAFE_ID
    comp_pattern = re.compile(r'\s*component\s+"(.+)"\s+as\s+([A-Za-z0-9_]+)')
    # Regular expression to match an edge line: SAFE_ID1 --> SAFE_ID2
    edge_pattern = re.compile(r'\s*([A-Za-z0-9_]+)\s*-->\s*([A-Za-z0-9_]+)')

    in_edges = False
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Process the file line by line.
    for line in lines:
        stripped = line.rstrip("\n")
        
        # Try matching component declarations.
        comp_match = comp_pattern.match(stripped)
        if comp_match:
            full_module, safeid = comp_match.groups()
            safeid_to_full[safeid] = full_module
            if not in_edges:
                header_lines.append(stripped)
            else:
                footer_lines.append(stripped)
            continue

        # If it matches an edge, mark the section as edges.
        if edge_pattern.match(stripped):
            in_edges = True
            edge_lines.append(stripped)
        else:
            if not in_edges:
                header_lines.append(stripped)
            else:
                footer_lines.append(stripped)
    
    # Filter edge lines: keep only those edges where BOTH the source and target full
    # module names start with the given organization prefix.
    filtered_edges = []
    for edge in edge_lines:
        m = edge_pattern.match(edge)
        if m:
            src_safe, tgt_safe = m.groups()
            full_src = safeid_to_full.get(src_safe, "")
            full_tgt = safeid_to_full.get(tgt_safe, "")
            # Only keep the edge if both modules start with the organization prefix.
            if full_src.startswith(org_prefix) and full_tgt.startswith(org_prefix):
                filtered_edges.append(edge)
    
    # Write output PlantUML file.
    with open(output_file, "w", encoding="utf-8") as out:
        out.write("@startuml\n")
        out.write("title Dependencies within Organization: " + org_prefix + "\n\n")
        # Output the header (component declarations & title)
        for line in header_lines:
            out.write(line + "\n")
        out.write("\n' Filtered direct dependency edges among modules with prefix " + org_prefix + ":\n")
        for edge in filtered_edges:
            out.write(edge + "\n")
        for line in footer_lines:
            out.write(line + "\n")
    
    print(f"Filtered PlantUML written to {output_file}.")

if __name__ == "__main__":
    main()