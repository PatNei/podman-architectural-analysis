## Overview and scope

At a high level, the scope of Podman and libpod is the following:

* Support for multiple container image formats, including OCI and Docker images.
* Full management of those images, including pulling from various sources (including trust and verification), creating (built via Containerfile or Dockerfile or committed from a container), and pushing to registries and other storage backends.
* Full management of container lifecycle, including creation (both from an image and from an exploded root filesystem), running, checkpointing and restoring (via CRIU), and removal.
* Full management of container networking, using Netavark.
* Support for pods, groups of containers that share resources and are managed together.
* Support for running containers and pods without root or other elevated privileges.
* Resource isolation of containers and pods.
* Support for a Docker-compatible CLI interface, which can both run containers locally and on remote systems.
* No manager daemon, for improved security and lower resource utilization at idle.
* Support for a REST API providing both a Docker-compatible interface and an improved interface exposing advanced Podman functionality.
* Support for running on Windows and Mac via virtual machines run by `podman machine`.



## Podman Desktop

[Podman Desktop](https://podman-desktop.io/) provides a local development environment for Podman and Kubernetes on Linux, Windows, and Mac machines.
It is a full-featured desktop UI frontend for Podman which uses the `podman machine` backend on non-Linux operating systems to run containers.
It supports full container lifecycle management (building, pulling, and pushing images, creating and managing containers, creating and managing pods, and working with Kubernetes YAML).
The project develops on [GitHub](https://github.com/containers/podman-desktop) and contributions are welcome.

## OCI Projects Plans

Podman uses OCI projects and best of breed libraries for different aspects:
- Runtime: We use the [OCI runtime tools](https://github.com/opencontainers/runtime-tools) to generate OCI runtime configurations that can be used with any OCI-compliant runtime, like [crun](https://github.com/containers/crun/) and [runc](https://github.com/opencontainers/runc/).
- Images: Image management uses the [containers/image](https://github.com/containers/image) library.
- Storage: Container and image storage is managed by [containers/storage](https://github.com/containers/storage).
- Networking: Networking support through use of [Netavark](https://github.com/containers/netavark) and [Aardvark](https://github.com/containers/aardvark-dns).  Rootless networking is handled via [pasta](https://passt.top/passt) or [slirp4netns](https://github.com/rootless-containers/slirp4netns).
- Builds: Builds are supported via [Buildah](https://github.com/containers/buildah).
- Conmon: [Conmon](https://github.com/containers/conmon) is a tool for monitoring OCI runtimes, used by both Podman and CRI-O.
- Seccomp: A unified [Seccomp](https://github.com/containers/common/blob/main/pkg/seccomp/seccomp.json) policy for Podman, Buildah, and CRI-O.

## Buildah and Podman relationship

Buildah and Podman are two complementary open-source projects that are
available on most Linux platforms and both projects reside at
[GitHub.com](https://github.com) with Buildah
[here](https://github.com/containers/buildah) and Podman
[here](https://github.com/containers/podman).  Both, Buildah and Podman are
command line tools that work on Open Container Initiative (OCI) images and
containers.  The two projects differentiate in their specialization.

Buildah specializes in building OCI images.  Buildah's commands replicate all
of the commands that are found in a Dockerfile.  This allows building images
with and without Dockerfiles while not requiring any root privileges.
Buildah’s ultimate goal is to provide a lower-level coreutils interface to
build images.  The flexibility of building images without Dockerfiles allows
for the integration of other scripting languages into the build process.
Buildah follows a simple fork-exec model and does not run as a daemon
but it is based on a comprehensive API in golang, which can be vendored
into other tools.

Podman specializes in all of the commands and functions that help you to maintain and modify
OCI images, such as pulling and tagging.  It also allows you to create, run, and maintain those containers
created from those images.  For building container images via Dockerfiles, Podman uses Buildah's
golang API and can be installed independently from Buildah.

A major difference between Podman and Buildah is their concept of a container.  Podman
allows users to create "traditional containers" where the intent of these containers is
to be long lived.  While Buildah containers are really just created to allow content
to be added back to the container image.  An easy way to think of it is the
`buildah run` command emulates the RUN command in a Dockerfile while the `podman run`
command emulates the `docker run` command in functionality.  Because of this and their underlying
storage differences, you can not see Podman containers from within Buildah or vice versa.

In short, Buildah is an efficient way to create OCI images while Podman allows
you to manage and maintain those images and containers in a production environment using
familiar container cli commands.  For more details, see the
[Container Tools Guide](https://github.com/containers/buildah/tree/main/docs/containertools).

https://github.com/containers/podman/blob/main/transfer.md


Using gvproxy from homebrew, with podman from git

Recent podman builds depend on a gvproxy binary which comes from containers/gvisor-tap-vsock. A common development scenario may be using the podman desktop app as a baseline, with a development binary of podman you build from git. To ensure that the podman you build here can find the gvproxy installed from podman desktop, use:

make podman-remote HELPER_BINARIES_DIR=/opt/podman/bin

(Also note that because the Makefile rules do not correctly invalidate the binary when this variable changes, so if you already have a build you'll need to rm bin/darwin/podman first if you have an existing build).

Alternatively, you can set helper_binaries_dir= in ~/.config/containers/containers.conf.