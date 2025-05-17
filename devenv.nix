{ pkgs, lib, config, inputs, ... }:

{
  # https://devenv.sh/basics/
  env.GREET = "devenv";

  # https://devenv.sh/packages/
  packages = [ 
  pkgs.git 
  pkgs.graphviz
  pkgs.plantuml
  pkgs.golangci-lint
  pkgs.cloc
  pkgs.imagemagick

  ];

  # https://devenv.sh/languages/
  # languages.rust.enable = true;
  languages.go.enable = true;
  languages.java.enable = true;
  languages.python.enable = true;
  languages.python.venv.enable = true;
  languages.typst.enable = true;

  # https://devenv.sh/processes/
  # processes.cargo-watch.exec = "cargo-watch";

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/scripts/
  scripts.hello.exec = ''
    echo hello from $GREET
  '';
  
  scripts.generate.exec = ''
  python3 gomodgraph.networkx.py go_mod_graph.txt $1 $2
  '';

  scripts.gomod-graph.exec = ''
  go mod graph > go_mod_graph.txt
  '';

  scripts.component_diagram.exec =''
  #!/bin/bash

  # Create the initial PlantUML file with configuration for a component style.
  {
    echo "@startuml"
    # Set the style. 'rectangle' is often clearer for module views.
    echo "skinparam componentStyle rectangle"
    echo "hide empty description"
    echo ""
    
    # Create a mapping for each unique module.
    # We use a simple alias conversion to ensure valid identifiers.
    modules=$(go mod graph | awk '{print $1; print $2}' | sort | uniq)
    
    for module in $modules; do
      # Convert the module string to a valid identifier. Remove punctuation or replace with underscores.
      alias=$(echo "$module" | tr './@-' '_' )
      echo "component \"$module\" as $alias"
    done
    
    echo ""
    
    # Generate dependency relationships.
    go mod graph | awk '{printf("\"%s\" --> \"%s\"\n", $1, $2)}' | sort | uniq
    
    echo ""
    echo "@enduml"
  } > diagram.puml

  echo "PlantUML component diagram saved to diagram.puml"
  
  '';

  enterShell = ''
    hello
    git --version
  '';

  # https://devenv.sh/tasks/
  # tasks = {
  #   "myproj:setup".exec = "mytool build";
  #   "devenv:enterShell".after = [ "myproj:setup" ];
  # };

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
    git --version | grep --color=auto "${pkgs.git.version}"
  '';

  # https://devenv.sh/git-hooks/
  # git-hooks.hooks.shellcheck.enable = true;

  # See full reference at https://devenv.sh/reference/options/
}
