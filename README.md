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
<a href="https://discord.gg/My6Mqxt">
<img src="https://img.shields.io/discord/636014317892009985.svg?logo=discord" height="18"/>
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

## Contribute

Mussels is open source and we'd love your help. There are many ways to contribute!

### Community

Join the Mussels community on the [Mussels Discord chat server](https://discord.gg/My6Mqxt).

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
