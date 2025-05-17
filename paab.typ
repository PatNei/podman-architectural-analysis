// The goal of the project is to recover one or more architectural views and present them in a brief report.
// The audience is someone who has not seen the system before and needs a high-level understanding of it.
// If you devoted time to building an advanced analysis tool, describe it—even if the analysis section can be more concise in that case.
//
//
//
#import "frontpage.typ": frontpage
#set text(font: "Baghdad PUA", size: 12pt)
#set scale(reflow: true)
#show selector(<nn>): set heading(numbering: none)
#show selector(<ntoc>): set heading(outlined: false,numbering: none)
// #show heading.where(level: 3): set heading(numbering: none) 
#set page(
  paper: "a4",
  margin: (left: 1in, right: 1in, top: 1in, bottom: 1in),
)
#set heading(numbering: "1.")
#set figure(numbering: "1")

#show raw.where(block: true): set block(
  fill: luma(95.29%),   // Light gray background
  inset: 1em,           // Padding inside the block
  radius: 0.0em,        // Rounded corners
  width: 100%
)
#show raw.where(block: false): set text(
  fill: rgb("#c35b5b"),


)
#frontpage()
#pagebreak()
#outline()
#pagebreak()
= Introduction
== Goal of the report
`Docker`'s architecture has been comprehensively described in its official documentation#footnote(link("https://docs.docker.com/get-started/docker-overview/")), in technical talks, and in various external analyses. In contrast, `Podman`'s documentation provides a less direct and detailed architectural overview. 

In this report, I aim to construct a reflexion model by visualising and comparing the proposed architecture outlined in `Podman`'s documentation with its actual implementation using the source code as my truth.

// == Introduction to Docker
// `Docker` popularized software isolation by encapsulating applications within containers, revolutionizing how environments are standardized. Containers are lightweight virtual environments that bundle an application with all its dependencies, ensuring consistent behavior across diverse execution environments. Despite these operational benefits, `Docker`'s reliance on a central daemon that runs with root privileges has raised security concerns. 

// The Docker daemon, critical for container management, increases the system's attack surface, especially if an intruder gains control of this privileged service. 

== Introduction to Podman
Podman emerged as a promising container engine alternative to address the security vulnerabilities found in the docker project. Unlike `Docker`, `Podman` operates without a central daemon running with elevated privileges. 

Instead, it operates entirely in user space#footnote("Meaning it runs with the same privileges as the current user") by integrating with the host's native systemd process, thereby reducing the security risks associated with a privileged daemon. 

= Methodology
== General Approach
My approach to the reconstructing the architecture is the Symphoni method as described in van Deursen et al.@vandeursenSymphonyViewdrivenSoftware2004 with the target view being a generated view of the documentation verified with a reflexion model as described in Murphy et al.@murphySoftwareReflexionModels2001a

For my source view I use the codebase and documentation found in the Github repository for the Podman project #footnote(link("https://github.com/containers/podman"))

My target view is the core project dependencies as seen in @figure_plantuml_generated.

Hypothetical view can be found in @fig_podman_manual and is constructed on the documentation found in the source view.

Additionally my reflexion model can be found in @figure_plantuml_generated in the appendix and the score of the similarity of the implementation and the hypothetical view can be found in @section_reflexion_result.

== Tool support <tool-support>
// Discuss how off-the-shelf tools assisted your analysis.
// Elaborate on how each tool (gomod, graphviz, goplantuml) contributed to analyzing dependencies, module views, and potential code complexity.
// Contrast the benefits of automated script-generated graphs versus manual mapping, and mention any trade-offs.

The `Go` ecosystem ships native tooling to find some statistics about the codebase but there exists very little tooling to actually learn something interesting about the codebase so I use custom created scripts to remedy this limitation.

 These scripts were partly created using LLM's, like `ChatGPT` especially for the documentation and for the parsing functionality.

=== Go Project
By design `Go` projects are encouraged by the compiler to have a clear split between the packages in a project.

// We can learn a lot about the general architecture by looking at the go mod file and supplemented with the `package` keyword in each go file.

// `Go` projects manage dependencies using a go.mod file, which records both the libraries involved and their respective versions. 

In my analysis, I leverage `Go`'s built-in tools, specifically the `go mod graph` command to display the external dependency tree directly from a go.mod file. This helps me identify and understand the relationships between the external dependencies used in the project.

=== Documentation based diagram
To construct the diagram found in @podman_manual_full, I used the diagramming language `PlantUML`. This allows for quick iteration by taking a coding approach to defining the architecture and will allow us later to compare diagrams by the use of AST or a fuzzing comparison.

=== Cyclomatic complexity
To find the cyclomatic complexity for all function in the project, I used the tool `Gocyclo`#footnote(link("https://github.com/fzipp/gocyclo")).

I supplement this with a custom script found in the file `cyclomatic_complexity.py`, to display the cyclomatic complexity metric by package instead of by function with the intention of revealing the packages most important to the project. 

Additionally the output will contain total amount of functions and the average cyclomatic complexity for the module and by passing the `--sort <column_header>` flags we can sort the output on a given column header.

=== Count Lines of Code (CLOC)
I used a homemade implementation of `cloc` #footnote(link("https://github.com/AlDanial/cloc")) in `python` found in the file called `cloc.py`.
This script groups CLOC pr. package instead of pr. language as it helps highlight the most important modules used in the project.

The script counts only executable lines of code and ignores comments and empty lines.

=== Gomod based diagram

To gain insight into the dependencies defined in the go mod file I use a tool called `goplantuml`#footnote(link("https://github.com/jfeliu007/goplantuml")). The tool takes a go project folder as input and maps the modules, classes and their relationship in the `PlantUML` language. This enables us to leverage the `PlantUML` tool chain to render it as an `svg` or `png`.

Due to performance bottlenecks on larger `PlantUML` files, it was necessary to construct a custom script to limit the amount of dependencies that is rendered.

The script found in the `gomodgraph.plantuml.py` file maps the output of the `go mod graph` command to a `PlantUML` diagram.

=== Reflexion model

To calculate the similarities between the PlantUML diagrams, I have created a script found in `calculate_reflexion_score.py`. 

The script compares two PlantUML files using two strategies
1. First by constructing an AST, serializing it and then comparing it using the python diff-lib#footnote((link("https://docs.python.org/3/library/difflib.html"))) library.
2. Second by using the difflib library between the raw source files.

== Data gathering

=== Documentation based diagram
This is largely based on the documentation found in the `Podman` repository#footnote(
  link("https://github.com/containers/podman")
) with supplementing documentation found in the individual library repositories. 

Information is gathered using both a manual approach based on explicit module declarations but also by checking the repository code to continously verify correct understanding of the architecture.
// Further analysis is done using the tools mentioned in @tool-support.
// Explain what data you collected and from which sources (e.g., GitHub repositories, go.mod files).
// Describe how these files served as the raw data for your architectural reconstruction.
// Make clear whether your data gathering was solely automated using provided tools, or if you supplemented it with manual reasoning and cross-checking.

=== Cyclomatic complexity
To calculate the cyclomatic complexity in `Podman` project I use the command
```sh
gocyclo -over 5 . > cyclomatic_complexity.txt
```
This enables us to retrieve every function with a cyclomatic complexity over 5.

The output produced is the cyclomatic complexity for every function in the project but to reveal information about the importance of a given module we need extract the cyclomatic complexity pr. package.

To reach my result as shown in @figure_cyclomatic_complexity_total, I used the following command on the `gocyclo` output.
```bash
python cyclomatic_complexity.py cyclomatic_complexity.txt --sort Total_Complexity
```

=== CLOC

To get the top 20 modules sorted by lines of code I use the `cloc.py` script.

We can ignore folders using the `--skip-folders` flag and we can filter the results by getting the top x results with `--top x` flag.

To reach my result as found in @figure_cloc, I used the following command.
```shell-unix-generic
python cloc.py podman-5.4.2 --top 20 --skip-folders vendor, test
```

Note: we ignore folders `"vendor, test"` as they contain nothing interesting specific to the `Podman` project but contain a lot of generic code with a high CLOC score.

=== Gomod based diagram
Using the following command will output a file that contains all external dependencies for the project. 

```sh
go mod graph > go_mod_graph.txt
```
The output follows the pattern:
```sh
<package1> <package2>
```
where the space represents an implicit arrow from `<package1> → <package2>`.

I wish to translate this output into a viewable diagram, that can be compared with the documentation based diagram. 

To do this I used a tool called `goplantuml` and a variety of scripts found in the files `gomodgraph.networkx.py`,`gomodgraph.pyvis.py`,`gomodgraph.plantuml.py`. 

They all solve the same issue but use different underlying technologies which helped me get a better overview of the architecture. The which output can be found in @section_general_architecture in the appendix.

For my final analysis I used the `gomodgraph.plantuml.py` script as it will allow us to create an artifact that can be programmatically compared to the documentation based diagram. 

// Using the script found in the file `gomodgraph.pyvis.py`, it is possible to generate a `pyvis` graph visualising all the relationships contained in the `go_mod_graph.txt` file. 

// The user can show specific packages using the `--package <package1> <package2> <package3>` flag, and oppositely packages can be hidden with the `--hide-packages <package4> <package5>` flag.

To view the overall dependency graph of the project I used the following command
```sh
python3 gomodgraph.pyvis.py go_mod_graph.txt pyvis.html --packages "*"
```
But using the wildcard "\*" will output a gigantic file as seen @figure_pyvis_full. This indicates that it is critical to limit the scope of the dependencies shown.

To achieve my results found in @figure_plantuml_generated, I used the following command and filter based on the information gathered from earlier analysis.
```sh
python3 gomodgraph.plantuml.py go_mod_graph.txt podman_generated.puml --show-version --remove-isolated --packages github.com/containers github.com/opencontainers github.com/checkpoint-restore github.com/rootless-containers github.com/passt github.com/cri-o github.com/containernetworking
```

A limitation of this approach is that the command only outputs external dependencies and not internal dependencies so to remedy this we can use `goplantuml` as it allows us to get a full view of the internal dependencies in a `PlantUML` format.

I have simplified the output further by adding a variety of flags and to reach the output as found in @goplant_figure_podman_simplified_2, I used the following command.
```sh
goplantuml -recursive -hide-fields -hide-methods -hide-private-members -hide-connections -show-compositions . > simplified.puml
```

=== Reflexion model
To compare the similarity of two PlantUML files I used the following command.

```sh
python calculate_reflexion_score.py podman_manual.puml podman_generated.puml --visualize
```

And to verify the correctness of the AST's I added the `--visualize` so it generates two `networkx` diagrams constructed from the AST so we can visually verify its correctness.

== Knowledge Inference

The tools and the processes in conjunction with the research question have led me to use the reflexion model @murphySoftwareReflexionModels2001a to verify the result of my analysis.

Due to the sheer size of the project it was crucial to abstract some parts of the system away.

=== Expert knowledge
I have based a lot of my initial data gathering on the official documentation for the project.

=== Remove irrelevant nodes
We only filter out nodes not close to the core of the project and we have to be careful or we might miss important packages for the architecture of the system.

  

// Provide insights into how you interpreted the raw data to generate a high-level architectural view.
// Discuss any abstraction models, like the reflexion model, that you invoked to compare documentation versus implementation.
// Mention any challenges in inferring the architecture and how you resolved them (for example, handling discrepancies between expected and actual module dependencies).

= Results
// Present your most significant recovered architectural view(s) here.
// Explain the visible components, modules, and their relationships as depicted in your diagrams.
// Include commentary on how your automated mapping (using gomod/goplantuml) confirms or diverges from the architectural description in the documentation.
// 
// ¨
== Diagram based on the documentation <section_result_manual_diagram>
The documentation describes a module heavy architecture where a majority of the components in `Podman` are isolated in libraries located in different repositories. 

`Podman` itself is a soft wrapper around Libpod and Libpod does not exist as an external dependency but only within in the project itself. 

It is not easy to see how the two projects differ and the diagram shown is based on my interpretation of the public documentation.


#figure(scale(20%,image("./out/podman_manual_pretty/podman_manual_pretty.png"),reflow: true),caption: [This is a simplified/prettified overview based on the `Podman` documentation. Full raw view can be found at @podman_manual_full in the appendix.]) <fig_podman_manual>

*Note: To improve the visual appeal of this diagram, all dependencies associated with Libpod have been grouped into a single Libpod module.*

// If we look at the @fig_podman_manual then we can see.

Podman tries to adhere to the specifications outlined by the `Open Container Initiative`#footnote(link("https://opencontainers.org")) and have as a result external dependencies that are important for the core of the project.

// === Diagram based on 


== Cyclomatic complexity
The resulting tables generated.

#figure(caption: [The top 20 packages ranked by average complexity. Full table is available on @figure_full_cyclomatic_complexity_total in the appendix.])[
#align(center)[
#scale(70%,reflow: true, origin: horizon)[
#table(
  columns: (auto, auto, auto, auto),
  inset: 10pt,
  align: horizon,
  table.header(
    [*Package*],
    [*Total Complexity*],
    [*Average Complexity*],
    [*Function Count*]
  ),
  "libpod", "5594", "17.11", "327",
  "generate", "1284", "25.18", "51",
  "abi", "1177", "17.31", "68",
  "compat", "770", "21.39", "36",
  "containers", "756", "17.58", "43",
  "specgenutil", "553", "25.14", "22",
  "images", "436", "20.76", "21",
  "kube", "408", "17.00", "24",
  "main", "395", "11.62", "34",
  "common", "359", "17.10", "21",
  "util", "336", "14.61", "23",
  "quadlet", "258", "17.20", "15",
  "specgen", "234", "19.50", "12",
  "tunnel", "233", "12.26", "19",
  "events", "204", "17.00", "12",
  "resource", "189", "11.81", "16",
  "system", "186", "11.62", "16",
  "machine", "175", "10.94", "16",
  "parser", "171", "15.55", "11",
  "wsl", "166", "9.76", "17",
)]]] <figure_cyclomatic_complexity_total>

We can map this output to the documentation based diagram as found in @fig_podman_manual, we can see an overlap between some of the modules.

Libpod ranks highest with the highest total complexity and a somewhat high `Average Complexity`, unsurprising as it facilitates a lot of the interactions between the user and the different libraries. 

By sorting for average complexity we get more results for packages that could potentially be relevant to the core project

#figure(caption: [The top 20 packages ranked by average complexity. Full table is available on @figure_full_cyclomatic_complexity_average in the appendix.])[
#align(center)[
#scale(70%,reflow: true, origin: horizon)[
#table(
  columns: (auto, auto, auto, auto),
  inset: 10pt,
  align: horizon,
  table.header(
    [*Package*],
    [*Total Complexity*],
    [*Average Complexity*],
    [*Function Count*]
  ),
  "filters","159","53.00","3",
  "checkpoint","41","41.00","1",
  "infra","73","36.50","2",
  "validate","27","27.00","1",
  "generate","1284","25.18","51",
  "specgenutil","553","25.14","22",
  "manifests","48","24.00","2",
  "inspect","45","22.50","2",
  "compat","770","21.39","36",
  "images","436","20.76","21",
  "apple","59","19.67","3",
  "specgen","234","19.50","12",
  "containers","756","17.58","43",
  "abi","1177","17.31","68",
  "quadlet","258","17.20","15",
  "libpod","5594","17.11","327",
  "common","359","17.10","21",
  "kube","408","17.00","24",
  "events","204","17.00","12",
  "integration","117","16.71","7",
)]]] <figure_cyclomatic_complexity_average>


Podman packages CLI friendly version for their equivalent described in @fig_podman_manual and by looking into the code and the import statements we can map them as follows.
- `images` wraps `containers | Image` and | `containers | buildah`,
- `generate` wraps `opencontainers | runtime-tools`
- `main` wraps `containers | podman`
- `specgen` wraps `OCI Compliant Image`
- `machine` wraps `containers | gvisor-tap-vsock`
- `checkpoint` wraps `CRIU | CRIU`
- `containers` wraps nothing but manages interaction with containers. A core feature of Libpod/Podman but only mentioned briefly in the documentation.
- `common` wraps a large amount of utility functions and most of the network stack.

Not mentioned
- `abi` creates an Application Binary Interface. 
- `compat` Is a docker compatible layer.
- `specgenutil` utility functions for the `generate` package.
- `kube` out of scope, but handles kubernetes interaction.
- `tunnel` ssh based container management.
- `events` handles events in podman, like creation, deletion etc.
- `resource` utility fucntions.
- `system` utility to work with system specific behavior.
- `parser` parsing logic for Dockerfiles and Containerfiles.
- `wsl` windows specific utility.
- `filters` unsure.
- `infra` podman runtime.
- `validate` provides methods to validate a swagger specification.
- `manifest` utilities for working with OCI/Docker manifests #footnote(link("https://docs.docker.com/reference/cli/docker/manifest/")).
- `inspect` inspects docker images, but are used inside the `images` package mentioned above.
- `apple` apple device specific behavior.
- `quadlet` handles declarations for container runtimes similar to docker compose #footnote(link("https://www.redhat.com/en/blog/quadlet-podman")).

== CLOC

There seems to be a large overlap between the count of lines of code and the cyclomatic complexity.

#figure(align(center)[
#table(
  columns: (auto, auto),
  align: horizon,
  table.header(
    [*Package*],
    [*Non-Empty Lines*]
  ),
  "libpod",       "38475",
  "generate",     "9524",
  "containers",   "8098",
  "abi",          "7931",
  "compat",       "5757",
  "images",       "4843",
  "main",         "4312",
  "kube",         "4190",
  "common",       "3324",
  "e2e_test",     "3110",
  "machine",      "2930",
  "util",         "2705",
  "tunnel",       "2521",
  "specgenutil",  "2481",
  "entities",     "2233",
  "define",       "2151",
  "pods",         "2142",
  "system",       "2065",
  "v1",           "2042",
  "wsl",          "1865"
)],caption: [The top 20 packages ranked by their CLOC metric.]) <figure_cloc>

We can notice additional packages that might be relevant for the core package.
- `util` a variety of utility functions
- `entities` different structs to be used throughout the project.
- `define` module used to defining constants
- `v1` docker api compatibility layer

== Diagram based on gomod <section_result_generated_diagram>
#align(center,
  figure(
    scale(10%,
        image("./out/podman_generated/podman_generated.png"),
      ),
    caption: [
      Diagram generated from the gomod file. Higher res version can be found in @figure_plantuml_generated in the appendix. 
    ]
  )
)

*Found in the original diagram*
- "containers | storage"
- "containers | buildah"
- "containers | image/v5"
- "containers | gvisor-tap-vsock"
- "containers | ocicrypt"
- "containers | conmon"
- "containers | podman/v5"
- "opencontainers | runc"
- "opencontainers | runtime-spec"
- "opencontainers | runtime-tools"
- "opencontainers | image-spec"
- "checkpoint-restore | go-criu/v7"
- "checkpoint-restore | go-criu/v6"
- "checkpoint-restore | checkpointctl"

*Not found in the original diagram*
- "containers | common"
- "containers | winquit"
- "containers | psgo"
- "containers | libtrust"
- "containers | libhvee"
- "containers | luksy"
- "rootless-containers | rootlesskit/v2"
- "opencontainers | selinux"
- "opencontainers | go-digest"
- "containernetworking | plugins"
- "containernetworking | cni"

*Expected but not found in the generated diagram*
- "CRI-O | CRI-O" 
- "passt | pasta"
- "rootless-containers | slirp4netns"
- "containers | Crun"
- "containers | Podman Desktop"
- "containers | Seccomp"
- "containers | Container"
- "containers | Libpod"
- "containers | common/libimage"
- "containers | Netavark"
- "containers | Aardvark (DNS)"

Some packages are missing and do not appear even though we use the package namespaces defined in the Podman readme found in @podman_readme in the appendix. Further investigation into the gomod reveals that they exist in the containers/common module. Meaning they appear in the graph but are shipped under the containers/common module.
These packages Include `passt/Pasta`, `slirp4netns` and `netawork`.
The `Libpod` is the core library in `Podman` and does not exist seperately from `Podman` but is instead grouped under the `Podman` package.   

== Reflexion model <section_reflexion_result>
I compare the manual diagram found in @section_result_manual_diagram with the gomod generated diagram found in @section_result_generated_diagram using `calculate_reflexion_score.py`.

This gives me the following result.
- Similarity score using AST approach: 0.0114
- Similarity score using fuzzy approach: 0.0929

If we edit the manual diagram so the component names matches we can improve the result of the AST for a bit.
- Similarity score using AST approach: 0.0241
- Similarity score using fuzzy approach: 0.0780

The documentation for the `ratio` function in the `difflib` library states

#quote([Ratio() returns a float in [0, 1], measuring the "similarity" of the sequences and as a rule of thumb, a.ratio() value over 0.6 means the sequences are close matches])

But as we are way under 0.5 for both approaches we can conclude that either my naive AST approach is not powerful enough to capture the similarities between two PlantUML files or the hypothetical view is not equivalent to the target view. 


= Discussion
// Reflect on the implications of your findings.
// Offer recommendations for potential reengineering if the recovered architecture reveals bottlenecks or weaknesses.
// Discuss limitations of your methods, such as any constraints imposed by using only static analysis tools and dependency graphs.
// Contemplate how additional manual analysis or alternative viewpoints (like deployment views) could have enriched your understanding.
== Recommendations

// is that the `Podman` project seems focused on splitting the different part of their API into seperate modules so they can be maintained seperately and generally this structure is followed except when it comes to `Podman` and `Libpod`. 

`Libpod` is shipped with the `Podman` library and doesn't exist as an external library like every other dependency. This is a strange choice as it becomes unclear what part is `Libpod` and what is `Podman`. This seems to be an intended choice based on the Podman documentation #footnote(link("https://github.com/containers/podman#podman-a-tool-for-managing-oci-containers-and-pods"))

It is also strange to wrap a large part of the networking dependencies in the containers/common module as it becomes unclear whether these are updated and maintained by the `Podman` team.

== Limitations
// In this section, acknowledge the limitations of your architectural reconstruction process. Consider discussing both technical and methodological constraints.
// For instance, note that your approach mainly uses static analysis of the Go code and its dependency graphs. While this reveals structural relationships, it may not capture dynamic aspects or runtime behaviors of Podman.
// Mention that the reliance on automated tools like gomod, Graphviz, and goplantuml, while effective for visualizing dependencies, might miss nuanced behaviors present in the live system.
// Consider the possibility that discrepancies exist between the documented architecture and the actual implementation due to legacy code, ongoing refactors, or undocumented practices.
// Reflect on any trade-offs made – such as favoring simplicity over a more detailed analysis – and how these choices impact the completeness of your recovered architecture.
// Discuss the limitations of inferring architectural decisions solely based on module relationships, as opposed to including other architectural viewpoints (e.g., deployment or performance views).
// Lastly, mention potential future work that could address these limitations, such as integrating runtime analysis or involving developers for interviews to gain deeper insights into the system's dynamics.


`Podman` is in large a wrapper around the `Libpod` library but it becomes hard to figure out what seperates the two projects.

This report has focused on static analysis and have mostly ignored any runtime analytics. This is largely done to prevent scope creep but removes an important dimension for the project. It makes it harder to verify that `Podman` truly only run in userspace as stated in the documentation.

// A hinderance 
// A lot of visualisations I had planned for the project couldn't be visualized as `PlantUML` have performance issues on files with many nodes and connections. This renders projects like `Goplantuml` almost unusable on larger projects. 

I parsed a large number of files using native `Go` tooling and custom regex based scripts. This approach can introduce some inaccuracies as regex is unable to capture the syntactic structure of the project and we are unable to verify the correctness of the scripts due to the size of the project. 

A proposed betterment is to use tools like `tree sitter`#footnote(link("https://tree-sitter.github.io/tree-sitter/")) as it would allow us to reconstruct an abstract syntax tree and parse the code with a more accurate result. As a bonus we would also be able to get the `number of method (NOM)` score. 

There is a discrepancy between the naming between the wrapper packages as they are defined in Libpod and the package they wrap. Some tools are simply wrapped inside the `common` package as seen in @figure_full_cyclomatic_complexity_total. This makes the analysis harder to verify requiring a more thorough analysis of the functionality of the packages, and this had a negative impact result of the AST analysis seen in @section_reflexion_result.

== Future work
Runtime analysis using tools such as `Jaeger`, `DTrace` to see the runtime behavior of `Podman`. Alternatively Google have have developed a profiler that works for `Java`, `C++` and `Go` projects that is built into the `Go` project itself.#footnote(link("https://github.com/DataDog/go-profiler-notes/blob/main/pprof.md"))

Improvements to the quality of the analysis would require investigation into a smarter calculation for the reflection model. One promising direction is to integrate a parsing tool such as tree-sitter with fuzzing techniques for robust package name matching, as it would improve the precision of dependency extraction.

#show bibliography: set heading(numbering: "1.")
#bibliography("bib.bib",style: "ieee")


= Appendix
NOTE: Due to some limitations of puml sizes, the files are cut off but can be viewed in full at in the projects repository #footnote(link("https://github.com/PatNei/podman-architectural-analysis"))

// Use this section to provide additional details that support your reconstruction.
// Include a brief description of your code (e.g., the Python script orchestrating the visualization pipelines).
// Insert links to your GitHub repository or Collab notebook where others can review your scripts.
// Optionally, provide a breakdown of your time allocation and describe which phases took up more time and why.

// == Description of the code

== Breakdown of Time allocation
- 25% script building
- 50% analysis
- 25% writing


== Cyclomatic analysis
#figure(scope: "column",
scale(50%,
table(
  columns: (auto, auto, auto, auto),
  inset: 10pt,
  table.header(
    [*Package*],
    [*Total Complexity*],
    [*Average Complexity*],
    [*Function Count*]
  ),
  "libpod", "5594", "17.11", "327",
  "generate", "1284", "25.18", "51",
  "abi", "1177", "17.31", "68",
  "compat", "770", "21.39", "36",
  "containers", "756", "17.58", "43",
  "specgenutil", "553", "25.14", "22",
  "images", "436", "20.76", "21",
  "kube", "408", "17.00", "24",
  "main", "395", "11.62", "34",
  "common", "359", "17.10", "21",
  "util", "336", "14.61", "23",
  "quadlet", "258", "17.20", "15",
  "specgen", "234", "19.50", "12",
  "tunnel", "233", "12.26", "19",
  "events", "204", "17.00", "12",
  "resource", "189", "11.81", "16",
  "system", "186", "11.62", "16",
  "machine", "175", "10.94", "16",
  "parser", "171", "15.55", "11",
  "wsl", "166", "9.76", "17",
  "shim", "163", "13.58", "12",
  "filters", "159", "53.00", "3",
  "utils", "146", "12.17", "12",
  "farm", "142", "12.91", "11",
  "pods", "123", "15.38", "8",
  "integration", "117", "16.71", "7",
  "rootless", "92", "13.14", "7",
  "qemu", "75", "10.71", "7",
  "ocipull", "73", "9.12", "8",
  "infra", "73", "36.50", "2",
  "volumes", "65", "13.00", "5",
  "trust", "64", "10.67", "6",
  "apple", "59", "19.67", "3",
  "manifest", "59", "14.75", "4",
  "bindings", "58", "14.50", "4",
  "define", "57", "9.50", "6",
  "manifests", "48", "24.00", "2",
  "ps", "47", "15.67", "3",
  "emulation", "47", "15.67", "3",
  "registry", "47", "11.75", "4",
),reflow: true),caption: "Table showing the cyclomatic complexity of the different packages, ranked by total complexity.") <figure_full_cyclomatic_complexity_total>

#figure(scope: "column",
scale(50%,
table(
  columns: (auto, auto, auto, auto),
  inset: 10pt,
  table.header(
    [*Package*],
    [*Total Complexity*],
    [*Average Complexity*],
    [*Function Count*]
  ),
"filters","159","53.00","3",
"checkpoint","41","41.00","1",
"infra","73","36.50","2",
"validate","27","27.00","1",
"generate","1284","25.18","51",
"specgenutil","553","25.14","22",
"manifests","48","24.00","2",
"inspect","45","22.50","2",
"compat","770","21.39","36",
"images","436","20.76","21",
"apple","59","19.67","3",
"specgen","234","19.50","12",
"containers","756","17.58","43",
"abi","1177","17.31","68",
"quadlet","258","17.20","15",
"libpod","5594","17.11","327",
"common","359","17.10","21",
"kube","408","17.00","24",
"events","204","17.00","12",
"integration","117","16.71","7",
"autoupdate","33","16.50","2",
"network","32","16.00","2",
"logs","16","16.00","1",
"ps","47","15.67","3",
"emulation","47","15.67","3",
"parser","171","15.55","11",
"parse","31","15.50","2",
"pods","123","15.38","8",
"connection","46","15.33","3",
"e2e_test","45","15.00","3",
"manifest","59","14.75","4",
"util","336","14.61","23",
"bindings","58","14.50","4",
"crutils","14","14.00","1",
"shim","163","13.58","12",
"rootless","92","13.14","7",
"entities","26","13.00","2",
"vmconfigs","26","13.00","2",
"os","13","13.00","1",
"volumes","65","13.00","5",
"notifyproxy","26","13.00","2",
"farm","142","12.91","11",
"artifact","38","12.67","3",
"tunnel","233","12.26","19",
"utils","146","12.17","12",
"common_test","12","12.00","1",
"camelcase","12","12.00","1",
"auth","12","12.00","1",
"bindings_test","12","12.00","1",
),reflow: true),caption: "Table showing the cyclomatic complexity of the different packages, ranked by average complexity.") <figure_full_cyclomatic_complexity_average>

== Documentation based view


#figure(scale(100%,image("./out/podman_manual/podman_manual.png"),reflow: true),caption: [Module overview based on the `Podman` documentation.]) <podman_manual_full>

== Generated Architecture <section_general_architecture>
#figure(image("./out/podman_full/podman_full.png"),caption: [Module overview generated by `goplantuml` on the project folder. Shows internal dependencies for `Podman` before any filtering. Full version can be found in the github repository for this report.]) <goplant_podman_full>

#figure(scale(100%,image("./out/podman_simplified_v1/podman_simplified_v1.png")),caption: [Module overview generated by `goplantuml` on the project folder. Shows a simplified view. Full version can be found in the github repository for this report.])<goplant_figure_podman_simplified_2>

// #figure(image("./out/podman_simplified_v2/podman_simplified_v2.png"),caption: [V2: Module overview based on the `goplantuml` documentation.]) <podman_simplified_v2>
#figure(image("pyvis_full.png"),caption: [All dependencies from the gomod file visualized]) <figure_pyvis_full>

#figure(image("pyvis_filtered.png"),caption: [Filtered version of the same diagram, showing only modules from organisations found in the manual diagram]) <figure_pyvis_filtered>

#figure(image("./out/podman_generated/podman_generated.png"),caption: [Diagram equivalent to @figure_pyvis_filtered but using the PlantUML language for its representation.]) <figure_plantuml_generated>

// #figure(image("podman_full.png")) <figure_>

== Podman Readme <podman_readme>
#figure(caption: [Podman readme taken from the Github repository page #link("https://github.com/containers/podman")])[
#image("podman_readme.png",height: 90%, width: 100%,fit: "contain")]
