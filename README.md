<p align="center">
  <img width="350" height="350" src="https://raw.githubusercontent.com/Cisco-Talos/Mussels/master/images/mussels-500.png" alt='Mussels'>
</p>

<p align="center">A tool to download, build, and assemble application dependencies.
</br>Brought to you by the Clam AntiVirus Team.
<p align="center"><em>Copyright (C) 2019-2021 Cisco Systems, Inc. and/or its affiliates. All rights reserved.</em></p>

<p align="center">
<a href="https://pypi.org/project/mussels/">
  <img src="https://badge.fury.io/py/mussels.svg" alt="PyPI version" height="18">
</a>
<img alt="PyPI - Python Version" src="https://img.shields.io/pypi/pyversions/mussels" height="18">
<a href="https://github.com/Cisco-Talos/Mussels/actions">
  <img alt="Unit Tests" src="https://github.com/Cisco-Talos/Mussels/workflows/Unit%20Tests/badge.svg" height="18">
</a>
</p>

## About

Mussels is a cross-platform and general-purpose dependency build automation tool.

Mussels helps automate the building of applications _and_ their versioned dependency chains using the original build systems intended by the software authors.

For a more in depth explanation, see the [Mussels Introduction](docs/introduction.md).

## Requirements

- Python 3.6 or newer.
- Git (must be added to your PATH environment variable).

An internet connection is required to use the public Mussels cookbooks. Some form of internet or intranet is required to download source archives from the URLs defined in each recipe.

Every recipe will require tools in order to run.  If you don't have the required tools, you'll get an error message stating that you're missing a required tool.  It will be up to you to install the tool in order for that recipe to build.

### Common Tools Requirements for building C/C++ software

Mussels was born out of the ClamAV project so you can find some good example recipe and tool definitions here: https://github.com/Cisco-Talos/clamav-mussels-cookbook/

The ClamAV recipes build C libraries for the most part. When using them, you'll probably the following compiler toolchain software installed on your system for the build to work. If these are missing, the Mussels build will fail and tell you as much.

Linux:

- gcc
- Make
- CMake
- patchelf

MacOS (Darwin):

- Clang (comes with XCode)
- Make
- CMake

Windows:

- Visual Studio 2017+
- CMake

## Installation

You may install Mussels from PyPI using `pip`, or you may clone the Mussels Git repository and use `pip` to install it locally.

Install Mussels from PyPI:

> `python3 -m pip install --user mussels`

## Usage

Use the `--help` option to get information about any Mussels command.

> `mussels`
>
> `mussels --help`
>
> `mussels build --help`

When performing a build, the intermediate build files are placed into the `~/.mussels/cache/work/<target>` directory and the final installed files into the `~/.mussels/install/<target>` directory. This default behavior can be overridden using `msl build --work-dir <path>` to specify a different work directory, and `msl build --install <path>` to specify a different install directory.

_Tip_: Use the `msl` shortcut, instead of `mussels` to save keystrokes.

_Tip_: You may not be able to run `mussels` or the `msl` shortcut directly if your Python Scripts directory is not in your `PATH` environment variable. If you run into this issue, and do not wish to add the Python Scripts directory to your path, you can run Mussels like this:

> `python -m mussels`

Learn more about how use Mussels in our [documentation](docs/usage.md).

## How it works

Any time you run Mussels, Mussels will search your current directory to load Mussels-YAML files that define "recipes" and "tools". Recipes define instructions to build a program or library. Tools describe a way to verify that your computer has a program needed to build a recipe. Recipes may depend any number of tools and on other recipes. Mussels will fail to build a recipe if a circular dependency is detected.

> _Tip_: Don't run Mussels in a big directory like your home directory. The recursive search for Mussels-YAML files will make startup sluggish, and the current version may throw some errors if it encounters non-Mussels YAML files.

All Mussels-YAML files have a type field that may be either "tool", "recipe", or "collection". A collection is just a special purpose recipe that only contains dependencies for other recipes. Each YAML file also includes the minimum Mussels version required to use the recipe.

Inside of each recipe YAML there is:
- A recipe name.
- A recipe version number.
- A URL for downloading the source code,
- For each `platform` (OS):
  - For each `target` supported on that OS:
    - Recipe dependencies that must be built before this recipe.
    - Tools dependencies that must be present to build this recipe.
    - (*optional*) Build scripts to "configure", "make", and "install" for this target.
    - (*optional*) A list of additional files that will be copied from the work directory to the install directory after the "install" script has run.
    - (*optional*) A directory name next to the recipe file that contains patches that that will be applied to the source code before running the "configure" script.

On Linux/UNIX systems, the default target is `host`. But you can define custom targets for variants of the recipe like `host-static`, or `host-static-debug`. On Windows the default target is either `x86` or `x64` depending on your current OS architecture. But you're welcome to use something custom here as well.

Inside of each tool YAML there is:
- A tool name.
- (*optional*) A tool version number.
- Ways to check if the tool exists for each `platform`:
  - (*optional*) Check if one or more names is in the `$PATH`.
  - (*optional*) Check if one or more filepaths exists on disk.
  - (*optional*) Check if the output of running one or more commands (like `clang --version`) matches expectations.

Each `tool` definition is good for one (1) program check. Lets say you wanted to check if a suite of programs exists.  You may check for just one of those tools, but if you need to verify that all of the programs exist, you would need to have a `tool` YAML file for each program.

When assembling the dependency chain, Mussels will only evaluate recipes that all have the same platform and target. That is to say, that if you want to build your recipe with a `host-static` target, then each of your recipe dependencies must also have a `host-static` target defined.

At build time, Mussels will evaluate the dependency chain and verify that (A) all of the recipes in the chain exist for the given platform and architecture and that (B) all of the tools required by the recipes can be found on the system, using methods defined in each tool's YAML file. You can use the `msl build --dry-run` option to do this check without performing an actual build. When not doing a "dry run", the build will proceed to build the dependency chain in reverse order, building the things with no dependencies first, followed by the things that depend on them. The `msl build --dry-run` option will show you that chain if you're curious what it looks like.

Each recipe has 3 stages: "configure", "make", and "install". On Linux/Unix these stages are instructions for bash scripts and on Windows they're instructions for batch scripts. These scripts are written to the `~/.mussels/cache/work/{dependency}` directory and executed.

- `configure`: This is used for Autotools' `./configure` step, or CMake's first call to `cmake .` build system generation step.
  - The "configure" script is only run the first time you build the recipe.

  > _Tip_: If something goes wrong during this stage, like you canceled the build early, all subsequent attempts to build will fail. You can force Mussels to rebuild from scratch using the `--rebuild` (`-r`) option. This will re-build ALL recipes in the dependency chain.

- `make`: This is used for Autotools' `make` step, or CMake's `cmake --build .`
  - Mussels will re-run this step for every dependency in the chain every time you build a recipe. This is usually pretty fast because if the scripts use CMake, Autotools, Meson, etc to do the build... those tools will verify what _actually_ needs to be recompiled.

- `install`: This is used for Autotools' `make install` step, or CMake's `cmake --build . --target install`.
  - Mussels will re-run this step for every dependency in the chain every time you build a recipe.

## Contribute

Mussels is open source and we'd love your help. There are many ways to contribute!

### Community

Join the ClamAV / Mussels community on the [ClamAV Discord chat server](https://discord.gg/6vNAqWnVgw).

### Contribute Recipes

You can contribute to the Mussels community by creating new recipes or improving on existing recipes in the ["scrapbook"](https://github.com/Cisco-Talos/mussels-recipe-scrapbook). Do this by submitting a pull request to that Git repository.

If your project is willing to make your project-specific recipes available to the public, we'd also be happy to add your cookbook repository to the Mussels [bookshelf](mussels/bookshelf.py). Do this submitting a pull request to this Git repository. As noted above, each cookbook's license must be compatible with the Apache v2.0 license used by Mussels in order to be included in the bookshelf.

To learn more about how to read & write Mussels recipe and tool definitions, check out the following:

- [Recipe guide](docs/recipes.md)
- [Tool guide](docs/tools.md)

### Report issues

If you find an issue with Mussels or the Mussels documentation, please submit an issue to our [GitHub issue tracker](https://github.com/Cisco-Talos/Mussels/issues).  Before you submit, please check to if someone else has already reported the issue.

### Mussels Development

If you find a bug and you're able to craft a fix yourself, consider submitting the fix in a [pull request](https://github.com/Cisco-Talos/Mussels/pulls). Your help will be greatly appreciated.

If you want to contribute to the project and don't have anything specific in mind, please check out our [issue tracker](https://github.com/Cisco-Talos/Mussels/issues).  Perhaps you'll be able to fix a bug or add a cool new feature.

_By submitting a contribution to the Mussels project, you acknowledge and agree to assign Cisco Systems, Inc the copyright for the contribution. If you submit a significant contribution such as a new feature or capability or a large amount of code, you may be asked to sign a contributors license agreement comfirming that Cisco will have copyright license and patent license and that you are authorized to contribute the code._

#### Mussels Development Set-up

The following steps are intended to help users that wish to contribute to development of the Mussels project get started.

1. Create a fork of the [Mussels git repository](https://github.com/Cisco-Talos/Mussels), and then clone your fork to a local directory.

    For example:

    > `git clone https://github.com/<your username>/Mussels.git`

2. Make user Mussels is not already installed.  If it is, remove it.

    > `python3 -m pip uninstall mussels`

3. Use pip to install Mussels in "edit" mode.

    > `python3 -m pip install -e --user ./Mussels`

Once installed in "edit" mode, any changes you make to your clone of the Mussels code will be immediately usable simply by running the `mussels` / `msl` commands.

### Conduct

This project has not selected a specific Code-of-Conduct document at this time. However, contributors are expected to behave in professional and respectful manner. Disrespectful or inappropriate behavior will not be tolerated.

## License

Mussels is licensed under the Apache License, Version 2.0 (the "License"). You may not use the Mussels project except in compliance with the License.

A copy of the license is located [here](LICENSE), and is also available online at [apache.org](http://www.apache.org/licenses/LICENSE-2.0).

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
