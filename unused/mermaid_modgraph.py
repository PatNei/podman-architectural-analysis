import re

def safe_id(modname):
    # Replace punctuation like /, @, -, ., etc.
    return re.sub(r'[^A-Za-z0-9]', '_', modname)

def main():
    input_file = "go_mod_graph.txt"
    nodes_defined = {}
    edges = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) != 2:
                continue
            modA, modB = parts
            # record the nodes if not already recorded
            if modA not in nodes_defined:
                nodes_defined[modA] = safe_id(modA)
            if modB not in nodes_defined:
                nodes_defined[modB] = safe_id(modB)
            edges.append((modA, modB))
    
    # Begin the Mermaid diagram.
    print("```mermaid")
    print("graph LR")
    print("    %% Go Module Dependency Graph")
    print("")
    
    # Define nodes.
    # Mermaid does not require an explicit node definition, but to ensure labels we can declare them once.
    for mod, ident in nodes_defined.items():
        # Using the syntax: id["Display Name"]
        print(f'    {ident}["{mod}"]')
    
    print("")
    # Add dependency edges
    for modA, modB in edges:
        idA = nodes_defined[modA]
        idB = nodes_defined[modB]
        print(f'    {idA} --> {idB}')
    
    print("```")

if __name__ == "__main__":
    main()