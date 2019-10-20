# Mussels

- [Mussels](#mussels)
  - [Introduction](#introduction)
  - [But really, what is Mussels?](#but-really-what-is-mussels)
  - [Terminology](#terminology)
    - [`recipe`](#recipe)
    - [`tool`](#tool)
    - [`cookbook`](#cookbook)
    - [`platform`](#platform)
    - [`target`](#target)

## Introduction

Mussels can help you build software on macOS, Linux/Unix, and Windows operating systems.  Though current recipes and tools are written to build C-based software for the host machine, Mussels provides the flexibility to extend recipes to other architectures, and to build software written in other languages.

At its core, a Mussels recipe defines the following for each build platform and each target architecture:

- A list of other recipes (dependencies) that must be built first.
- A list of tools needed to perform the build.
- A patch-set directory. (optional)
- Build scripts. (optional)
- Extra install files. (optional)

Building a recipe performs the following:

1. Download and extract the source archive for your build, using a URL defined by the recipe.
2. Apply patches to the extracted source, if needed.
3. Run scripts, defined by the recipe:
  a. Configure the build, only run the first time a build is run.
  b. Build (make) a build.
  c. Install the build.
4. Copy additional files declared by the recipe to specified directories.

## But really, what is Mussels?

Mussels...

- Is all about sharing.  Place your recipes in a public Git repository or "cookbook".  Anyone else can then use your recipes as templates for their own project.

  _IMPORTANT_: Users aren't intended to blindly build recipes from other users' cookbooks, which would amount to blinding downloading and executing untrusted code.  Yikes!  Users ARE, however, encouraged to copy each others recipes and tweak them to suite their projects' needs.

  To this end, Mussels provides the `cookbook add` and `cookbook update` commands to find new recipes, along with the `recipe clone` and `tool clone` commands to copy any recipe or tool definition into the current working directory.

  In addition, you have the option to explicitly "trust" a cookbook with the `cookbook trust` command, allowing you to run builds directly from that cookbook.  Mussels will not let you build recipes from untrusted cookbooks.

- Is cross-platform!  Mussels is designed to work on Windows, macOS, Linux, and other forms of UNIX.

- Provides dependency chaining and dependency versioning.

  Each recipe must identify the names of its depependencies and may optionally specify which dependency versions are compatible using `>` (greater than), `<` (less than), or `=` (equal to).

  Recipes for dependencies must either be provided in the same location, or a "cookbook" may be specified to indicate where to find the recipe.

  For example, a recipe depends on the `zlib` recipe, version greather than `1.2.8`, provided by the `scrapbook`^ cookbook would state its "dependencies" as follows:

  ```yaml
      dependencies:
        - scrapbook:zlib>1.2.8
  ```

- Provides build tool detection and build tool version selection.

  Similar to how recipes identify their recipe dependencies, recipes must identify the tools required to build a recipe. Developers may create custom tool definitions if existing tool definitions don't suit their needs.

  A recipe may depend on specific build tools, and may tool versions as needed. As with recipes, a curated list of tools is provided in the Mussels "scrapbook" cookbook, but users are welcome to define their own to suit their needs.

  Example recipe "required_tools" definition using tool definitions provided by the scrapbook:

  ```yaml
      required_tools:
        - scrapbook:nasm
        - scrapbook:perl
        - scrapbook:visualstudio>=2017
  ```

- Does _NOT_ require changes to your project source code.

  Unlike other dependency management tools, there is no requirement to add any Mussels files to your project repository.

  If you need to define your own recipes, and you probably will, you're encouraged to place them in a "cookbook" repository. We suggest that you make this separate from your main project repository, although you could also place them in a sub-directory in your project if you so desire.

- Does _NOT_ insert itself as a new dependency for your project.

  Mussels exists make your life easier by providing a framework to automate your existing build processes.

- Does _NOT_ require you to write all new build tooling. Unlike other dependency management tools, there are no custom CMakelists, Makefiles, or Visual Studio project files required for your code or your dependencies.

  Mussels recipes are, at their core, simple bash or batch scripts written to build your dependencies using the tools and commands that the library authors expected you to use.

- Is _NOT_ a replacement for traditional build tools.

  Your project will still require a traditional build system and compiler such a Make, CMake, Meson, Bazel, Visual Studio, gcc, Clang, _etc_.

- Is _NOT_ a package manager. Mussels is not intended to compete with or replace application distribution tools such as DNF/Yum, Homebrew, Chocolatey, apt-get, Snapcraft, Flatpak, the Windows App Store, _etc_.

- Is intended to enable application developers to build their own dependencies to be distributed with their applications on systems where the system cannot or should not be relied upon to provide application dependencies.

^_Nota bene_: The [scrapbook](https://github.com/Cisco-Talos/mussels-recipe-scrapbook) is a curated collection of general purpose recipes. If you would like to provide a recipe or two for public use and don't want to maintain your own cookbook repository, consider submitting your recipes in a pull-request to the scrapbook.

## Terminology

### `recipe`

A YAML file defining how to build a specific library or application. It defines the following:

- name
- version
- download URL
- build scripts, each of which are optional:
  - configure
    - This will only run the first time a recipe is built, unless you build with the `--clean` option, or delete the build directory from the `~/.mussels/cache`
  - make
  - install
- dependencies (other recipes) required for the build
- required tools needed to perform the build
- files and directories to be copied to the `~/.mussels/install/{target}` directory after install
- (optional) A recipe may be a collection; that is - a list of recipe "dependencies" with no download URL or and no build instructions.

For more detail about recipes, please view the [recipe specification](docs/recipes.md).

### `tool`

A YAML file defining how to find tools used to build recipes. It defines the following:

- name
- version
- how to identify that the tool is installed.  May check:
  - if a file exists in the PATH directories
  - if a command executes
    - with an option to check if the output includes some text, such as a specific version string
  - if a filepath exists
    - this will add the directory where the file is found to the PATH variable at build time automatically.
- file or directory paths that, if they exist, indicate that the tool is installed

For more detail about tools, pleases view the [tool specification](docs/tools.md).

### `cookbook`

A git repository containing recipe and tool definitions.

Mussels maintains a [an index of cookbooks](mussels/bookshelf.py). To register your cookbook in the index so that others may more easily reference your recipes, please submit a [pull-request on GitHub](https://github.com/Cisco-Talos/Mussels/pulls).

When Mussels is run in a local directory containing recipe and/or tool definitions, it will detect^ these and make them available as being provided by the "local" cookbook.

^_Caution_: Mussels recursively indexes your current working directory looking for YAML files containing the `mussels_version` field.  This is how it identifies local recipes and tools.  **There is no recursion depth limit at this time**, so this process can take a while in very large directory trees.  _You are advised to run Mussels in a small directory tree or empty directory._

### `platform`

The host operating system.  The `platform` options extend Python's `platform.system()` function, and may be one of the following^:

- Darwin / macOS / OSX
- Windows
- Linux
- Unix ( Darwin, FreeBSD, OpenBSD, SunOS, AIX, HP-UX )
- Posix ( Unix and Linux )
- FreeBSD
- OpenBSD
- SunOS
- AIX
- HP-UX

^_Disclaimer_: Mussels has really only been tested on macOS, Windows, and Linux so far but is intended to work on any OS that supports Python, and Git.

### `target`

The target architecture for a build.  The default on Posix systems is `host`, and the default on Windows is the host architecture (`x64` or `x86`).  You're welcome to define any `target` name that you wish in your recipes, so long as all of your recipe dependencies also support that `target`.
