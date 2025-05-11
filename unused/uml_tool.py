#!/usr/bin/env python3
import re
import sys
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Remove a given node (of any supported type) and all its references from a PUML file."
    )
    parser.add_argument("input", help="Input PUML file")
    parser.add_argument("node_type", help="Type of the node to remove (e.g., package, class, interface, enum, annotation, record, component, node, artifact, usecase, actor, state, activity, database, folder, entity, note)")
    parser.add_argument("node_name", help="Name of the node to remove")
    parser.add_argument("-o", "--output", help="Output file (default is output.puml)", default="output.puml")
    return parser.parse_args()

def remove_node(lines, node_type, node_name):
    output_lines = []
    node_type_lower = node_type.lower().strip()
    node_name = node_name.strip()
    
    # Create a pattern to remove any relationship/reference line that mentions the node as a whole word.
    ref_pattern = re.compile(r'\b{}\b'.format(re.escape(node_name)))
    
    # For 'package', we assume a block that starts with: package <name> {
    if node_type_lower == "package":
        decl_pattern = re.compile(r'^\s*package\s+{}\s*\{{'.format(re.escape(node_name)))
        in_block = False
        block_depth = 0

        for line in lines:
            # Start of package block (if not already in one)
            if not in_block and decl_pattern.match(line):
                in_block = True
                block_depth = line.count("{") - line.count("}")
                continue  # Skip this line and enter block-removal mode

            # If inside the package block, update block depth based on braces
            if in_block:
                block_depth += line.count("{") - line.count("}")
                if block_depth <= 0:
                    in_block = False  # end of block
                continue  # Skip all lines within the package block

            # For other lines, if reference exists, skip them.
            if ref_pattern.search(line):
                continue

            output_lines.append(line)

    # For all other node types, we assume simple single line declaration.
    else:
        # Prepare the declaration pattern based on node type.
        # Many common node types (class, interface, enum, annotation, record, component, node, artifact, usecase, actor,
        # state, activity, database, folder, entity) have a declaration pattern like:
        #   "<node_type> <node_name>"
        # Some, like "class", may be prefixed with "abstract" optionally.
        if node_type_lower == "class":
            decl_pattern = re.compile(r'^\s*(?:abstract\s+)?class\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "interface":
            decl_pattern = re.compile(r'^\s*interface\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "enum":
            decl_pattern = re.compile(r'^\s*enum\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "annotation":
            decl_pattern = re.compile(r'^\s*annotation\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "record":
            decl_pattern = re.compile(r'^\s*record\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "component":
            decl_pattern = re.compile(r'^\s*component\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "node":
            decl_pattern = re.compile(r'^\s*node\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "artifact":
            decl_pattern = re.compile(r'^\s*artifact\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "usecase":
            decl_pattern = re.compile(r'^\s*usecase\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "actor":
            decl_pattern = re.compile(r'^\s*actor\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "state":
            decl_pattern = re.compile(r'^\s*state\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "activity":
            decl_pattern = re.compile(r'^\s*activity\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "database":
            decl_pattern = re.compile(r'^\s*database\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "folder":
            decl_pattern = re.compile(r'^\s*folder\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "entity":
            decl_pattern = re.compile(r'^\s*entity\s+{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        elif node_type_lower == "note":
            # Note can be defined as:
            # note [left/right/top/bottom] of <node_name> or note as <node_name> ... 
            # For simplicity we identify a note line if it contains "note" followed by the node name.
            decl_pattern = re.compile(r'^\s*note.*\b{}\b'.format(re.escape(node_name)), re.IGNORECASE)
        else:
            # If the node type isn't supported, notify and exit.
            print("Unsupported node type: {}. Supported types include package, class, interface, enum, annotation, record, component, node, artifact, usecase, actor, state, activity, database, folder, entity, note.".format(node_type))
            sys.exit(1)

        for line in lines:
            # Skip the line if it is a declaration of the node.
            if decl_pattern.match(line):
                continue

            # Also, skip any line if it references the node in relationships or elsewhere.
            if ref_pattern.search(line):
                continue

            output_lines.append(line)
            
    return output_lines

def main():
    args = parse_arguments()
    node_type = args.node_type
    node_name = args.node_name

    try:
        with open(args.input, 'r', encoding='utf-8') as file:
            lines = file.readlines()
    except IOError as error:
        print("Error reading file {}: {}".format(args.input, error))
        sys.exit(1)

    new_lines = remove_node(lines, node_type, node_name)

    try:
        with open(args.output, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
    except IOError as error:
        print("Error writing to file {}: {}".format(args.output, error))
        sys.exit(1)

    print("Node '{} {}' has been removed. Output saved to {}".format(node_type, node_name, args.output))

if __name__ == "__main__":
    main()