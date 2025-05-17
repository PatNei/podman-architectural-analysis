"""
This script compares two PlantUML files to compute a similarity score using either:
1. An AST-based approach (which only captures whether a dependency exists 
   between two components, ignoring relationship details).
2. A fuzzy (approximate string matching) approach.
   
It is designed to parse PlantUML files such as:
    @startuml
    skinparam linetype ortho
    ... (diagram definitions)
    @enduml

Usage:
    python compare_plantuml.py --file1 path/to/file1.puml --file2 path/to/file2.puml --method ast [--visualize]
"""
import re
import difflib
import argparse
import networkx as nx
import matplotlib.pyplot as plt

def remove_uml_markers(content):
    """
    Remove PlantUML start/end markers (@startuml, @enduml)
    and return the remaining content.
    """
    lines = content.splitlines()
    filtered_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower() in ("@startuml", "@enduml"):
            continue
        filtered_lines.append(line)
    return "\n".join(filtered_lines)

def build_connection_ast(content):
    """
    Build an AST from the connection lines in the PlantUML content.
    This version captures only the dependency existence by recording the source
    and target components.
    
    The technique is:
      1. Remove UML markers.
      2. For each line that contains an arrow (e.g., "-->", "->", or "..>"):
         a. Remove any quoted text to ignore relationship details.
         b. Split the cleaned line on the arrow indicator.
         c. Use the first token of the left part as the source,
            and the first token of the right part (after stripping any trailing colon) as the target.
    """
    content = remove_uml_markers(content)
    connections = []
    arrow_regex = r'\s*(?:-->|->|\.{2}>)\s*'
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("'"):
            continue
        # Process line only if an arrow is present.
        if not re.search(r'(-->|->|\.{2}>)', line):
            continue
        # Remove quoted text entirely.
        clean_line = re.sub(r'"[^"]*"', '', line)
        # Split on the arrow indicators.
        parts = re.split(arrow_regex, clean_line)
        if len(parts) >= 2:
            # The source is taken from the left part.
            source_tokens = parts[0].strip().split()
            if source_tokens:
                source = source_tokens[0]
            else:
                continue
            # The target is taken from the right part; remove any trailing colon.
            target_tokens = parts[-1].strip().split()
            if target_tokens:
                target = target_tokens[0].rstrip(':')
            else:
                continue
            connections.append({
                "source": source,
                "target": target
            })
    return connections

def serialize_ast(connections):
    """
    Produce a canonical string representation of the connection AST.
    Only the existence of a dependency (source and target) is recorded.
    Sorting connections ensures that differences in ordering do not affect comparison.
    """
    serialized_lines = []
    for conn in sorted(connections, key=lambda x: (x["source"], x["target"])):
        line = f'{conn["source"]}|{conn["target"]}'
        serialized_lines.append(line)
    return "\n".join(serialized_lines)

def ast_based_similarity(file_content1, file_content2):
    """
    Compute similarity between two PlantUML files based on their connection ASTs.
    Only the dependency (source and target) is considered.
    """
    ast1 = build_connection_ast(file_content1)
    ast2 = build_connection_ast(file_content2)
    serialized1 = serialize_ast(ast1)
    serialized2 = serialize_ast(ast2)
    return difflib.SequenceMatcher(None, serialized1, serialized2).ratio()

def fuzzy_similarity(text1, text2):
    """
    Compute fuzzy similarity between two texts using difflib's SequenceMatcher.
    Preprocessing includes removing comments and UML start/end markers.
    """
    def preprocess(s):
        s = remove_uml_markers(s)
        lines = s.splitlines()
        clean_lines = [line.split("'")[0].strip() for line in lines if line.strip()]
        return "\n".join(clean_lines)
    t1 = preprocess(text1)
    t2 = preprocess(text2)
    return difflib.SequenceMatcher(None, t1, t2).ratio()

def visualize_ast_networkx(connections, output_file):
    """
    Visualize the connection AST using NetworkX and save the graph as a PNG.
    Each unique component is a node; each dependency becomes a directed edge.
    Since this AST only captures dependencies, no edge labels are provided.
    """
    G = nx.DiGraph()
    for conn in connections:
        src = conn["source"]
        tgt = conn["target"]
        G.add_node(src)
        G.add_node(tgt)
        G.add_edge(src, tgt)
    pos = nx.spring_layout(G, k=1.5, iterations=50)
    plt.figure(figsize=(12, 8))
    nx.draw(G, pos, with_labels=True, node_color="lightblue",
            edge_color="gray", node_size=2000, font_size=10, arrowsize=20)
    plt.title("PlantUML Dependency AST")
    plt.axis("off")
    plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.05)
    plt.savefig(output_file, format="png")
    plt.close()
    print(f"AST visualization saved to {output_file}")

def compare_plantuml_files(file1_path, file2_path):
    """
    Compare two PlantUML files and return a tuple of similarity scores:
      (AST-based similarity, fuzzy similarity)
    """
    with open(file1_path, "r", encoding="utf-8") as f1:
        content1 = f1.read()
    with open(file2_path, "r", encoding="utf-8") as f2:
        content2 = f2.read()
    return ast_based_similarity(content1, content2), fuzzy_similarity(content1, content2)

def main():
    parser = argparse.ArgumentParser(description='Compare two PlantUML files for similarity.')
    parser.add_argument('file1', type=str, help='Path to the first PlantUML file.')
    parser.add_argument('file2', type=str, help='Path to the second PlantUML file.')
    parser.add_argument('--visualize', action='store_true',
                        help='Generate AST visualization images for each input file as PNGs.')
    args = parser.parse_args()
    # Compare files.
    ast_score, fuzzy_score = compare_plantuml_files(args.file1, args.file2)
    print(f"Similarity score using AST approach: {ast_score:.4f}")
    print(f"Similarity score using fuzzy approach: {fuzzy_score:.4f}")
    # If visualization is requested, generate AST PNGs.
    if args.visualize:
        for file_path in [args.file1, args.file2]:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            connections = build_connection_ast(content)
            if "." in file_path:
                base_name = ".".join(file_path.split(".")[:-1])
            else:
                base_name = file_path
            output_png = f"{base_name}_ast.png"
            visualize_ast_networkx(connections, output_png)

if __name__ == "__main__":
    main()