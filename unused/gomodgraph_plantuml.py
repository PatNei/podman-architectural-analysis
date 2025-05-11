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
    
    print("@startuml")
    print("title Go Module Dependency Graph")
    print("")
    print("' Define all nodes as components")

    for mod, ident in nodes_defined.items():
        print(f'component "{mod}" as {ident}')
    
    print("")
    print("' Now add dependency edges")
    for modA, modB in edges:
        idA = nodes_defined[modA]
        idB = nodes_defined[modB]
        print(f'{idA} --> {idB}')
        
    print("")
    # print("note right of " + nodes_defined[next(iter(nodes_defined))] + " : (Generated from go-mod graph)")
    print("@enduml")


if __name__ == "__main__":
    main()