#!/usr/bin/env python

r"""
  __    __     __  __     ______     ______     ______     __         ______
 /\ "-./  \   /\ \/\ \   /\  ___\   /\  ___\   /\  ___\   /\ \       /\  ___\
 \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \___  \  \ \  __\   \ \ \____  \ \___  \
  \ \_\ \ \_\  \ \_____\  \/\_____\  \/\_____\  \ \_____\  \ \_____\  \/\_____\
   \/_/  \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/
"""

_description = """
A tool to download, build, and assemble application dependencies.
                                    Brought to you by the Clam AntiVirus Team.
"""
_copyright = """
Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
"""

"""
Author: Micah Snyder

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import os
import sys

import click
import coloredlogs

from mussels.mussels import Mussels
from mussels.utils.click import MusselsModifier, ShortNames

logging.basicConfig()
module_logger = logging.getLogger("mussels")
coloredlogs.install(level="DEBUG", fmt="%(asctime)s %(name)s %(levelname)s %(message)s")
module_logger.setLevel(logging.DEBUG)

from colorama import Fore, Back, Style

#
# CLI Interface
#
@click.group(
    cls=MusselsModifier,
    epilog=Fore.BLUE
    + __doc__
    + Fore.GREEN
    + _description
    + Style.RESET_ALL
    + _copyright,
)
def cli():
    pass


@cli.group(cls=ShortNames, help="Commands that operate on cookbooks.")
def cookbook():
    pass


@cookbook.command("list")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
def cookbook_list(verbose: bool):
    """
    Print the list of all known cookbooks.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.list_cookbooks(verbose)


@cookbook.command("show")
@click.argument("cookbook", required=True)
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
def cookbook_show(cookbook: str, verbose: bool):
    """
    Show details about a specific cookbook.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.show_cookbook(cookbook, verbose)


@cookbook.command("update")
def cookbook_update():
    """
    Update the cookbooks from the internet.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.update_cookbooks()


@cookbook.command("trust")
@click.argument("cookbook", required=True)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Confirm trust. [required for non-interactive modes]",
)
def cookbook_trust(cookbook, yes):
    """
    Trust a cookbook.
    """
    my_mussels = Mussels(load_all_recipes=True)

    if yes != True:
        print(
            f"\nDisclaimer: There is a non-zero risk when running code downloaded from the internet.\n"
        )
        response = input(
            f"Are you sure you would like to trust recipes from cookbook '{cookbook}'? [N/y] "
        )
        response = response.strip().lower()

        if response != "y" and response != "yes":
            return

    my_mussels.config_trust_cookbook(cookbook)


@cookbook.command("add")
@click.argument("cookbook", required=True)
@click.option("--author", "-a", default="", help="Author or company name")
@click.option("--url", "-u", default="", help="Git repository URL")
@click.option(
    "--trust",
    "-t",
    is_flag=True,
    default=False,
    help="Add as a trusted cookbook, enabling you to build directly from this cookbook.",
)
def cookbook_add(cookbook, author, url, trust):
    """
    Add a cookbook to the list of known cookbooks.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.config_add_cookbook(cookbook, author, url, trust=trust)


@cookbook.command("remove")
@click.argument("cookbook", required=True)
def cookbook_remove(cookbook):
    """
    Remove a cookbook from the list of known cookbooks.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.config_remove_cookbook(cookbook)


@cli.group(cls=ShortNames, help="Commands that operate on recipes.")
def recipe():
    pass


@recipe.command("list")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    default=False,
    help="List all recipes, including those for other platforms. [optional]",
)
def recipe_list(verbose: bool, all: bool):
    """
    Print the list of all known recipes.
    An asterisk indicates default (highest) version.
    """
    my_mussels = Mussels(load_all_recipes=all)

    my_mussels.list_recipes(verbose)


@recipe.command("show")
@click.argument("recipe", required=True)
@click.option("--version", "-v", default="", help="Version. [optional]")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    default=False,
    help="Show all recipe variants, including those for other platforms. [optional]",
)
def recipe_show(recipe: str, version: str, verbose: bool, all: bool):
    """
    Show details about a specific recipe.
    """
    my_mussels = Mussels(load_all_recipes=all)

    my_mussels.show_recipe(recipe, version, verbose)


@recipe.command("clone")
@click.argument("recipe", required=True)
@click.option(
    "--version", "-v", default="", help="Specific version to clone. [optional]"
)
@click.option(
    "--cookbook", "-c", default="", help="Specific cookbook to clone. [optional]"
)
@click.option("--dest", "-d", default="", help="Destination directory. [optional]")
def recipe_clone(recipe: str, version: str, cookbook: str, dest: str):
    """
    Copy a recipe to the current directory or to a specific directory.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.clone_recipe(recipe, version, cookbook, dest)


@recipe.command("build")
@click.argument("recipe", required=True)
@click.option(
    "--version",
    "-v",
    default="",
    help="Version of recipe to build. May not be combined with @version in recipe name. [optional]",
)
@click.option(
    "--cookbook", "-c", default="", help="Specific cookbook to use. [optional]"
)
@click.option("--target", "-t", default="", help="Target architecture. [optional]")
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
@click.option(
    "--clean",
    "-c",
    is_flag=True,
    help="Re-build a recipe, even if already built. [optional]",
)
def recipe_build(
    recipe: str, version: str, cookbook: str, target: str, dry_run: bool, clean: bool
):
    """
    Download, extract, build, and install a recipe.
    """

    my_mussels = Mussels()

    results = []

    success = my_mussels.build_recipe(
        recipe, version, cookbook, target, results, dry_run, clean
    )
    if success == False:
        sys.exit(1)

    sys.exit(0)


@cli.group(cls=ShortNames, help="Commands that operate on tools.")
def tool():
    pass


@tool.command("list")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    default=False,
    help="List all tools, including those for other platforms. [optional]",
)
def tool_list(verbose: bool, all: bool):
    """
    Print the list of all known tools.
    An asterisk indicates default (highest) version.
    """
    my_mussels = Mussels(load_all_recipes=all)

    my_mussels.list_tools(verbose)


@tool.command("show")
@click.argument("tool", required=True)
@click.option("--version", "-v", default="", help="Version. [optional]")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    default=False,
    help="Show all tool variants, including those for other platforms. [optional]",
)
def tool_show(tool: str, version: str, verbose: bool, all: bool):
    """
    Show details about a specific tool.
    """
    my_mussels = Mussels(load_all_recipes=all)

    my_mussels.show_tool(tool, version, verbose)


@tool.command("clone")
@click.argument("tool", required=True)
@click.option(
    "--version", "-v", default="", help="Specific version to clone. [optional]"
)
@click.option(
    "--cookbook", "-c", default="", help="Specific cookbook to clone. [optional]"
)
@click.option("--dest", "-d", default="", help="Destination directory. [optional]")
def tool_clone(tool: str, version: str, cookbook: str, dest: str):
    """
    Copy a tool to the current directory or to a specific directory.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.clone_tool(tool, version, cookbook, dest)


@tool.command("check")
@click.argument("tool", required=False, default="")
@click.option(
    "--version",
    "-v",
    default="",
    help="Version of tool to check. May not be combined with @version in tool name. [optional]",
)
@click.option(
    "--cookbook", "-c", default="", help="Specific cookbook to use. [optional]"
)
def tool_check(tool: str, version: str, cookbook: str):
    """
    Check if a tool is installed.
    """

    my_mussels = Mussels()

    results = []

    success = my_mussels.check_tool(tool, version, cookbook, results)
    if success == False:
        sys.exit(1)

    sys.exit(0)


@cli.group(cls=ShortNames, help="Commands to clean up.")
def clean():
    pass


@clean.command("cache")
def clean_cache():
    """
    Clear the cache files.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.clean_cache()


@clean.command("install")
def clean_install():
    """
    Clear the install files.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.clean_install()


@clean.command("logs")
def clean_logs():
    """
    Clear the logs files.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.clean_logs()


@clean.command("all")
def clean_all():
    """
    Clear the all files.
    """
    my_mussels = Mussels(load_all_recipes=True)

    my_mussels.clean_all()


#
# Command Aliases
#
@cli.command("build")
@click.argument("recipe", required=True)
@click.option(
    "--version",
    "-v",
    default="",
    help="Version of recipe to build. May not be combined with @version in recipe name. [optional]",
)
@click.option(
    "--cookbook", "-c", default="", help="Specific cookbook to use. [optional]"
)
@click.option("--target", "-t", default="", help="Target architecture. [optional]")
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
@click.option(
    "--clean",
    "-c",
    is_flag=True,
    help="Re-build a recipe, even if already built. [optional]",
)
@click.pass_context
def build_alias(
    ctx,
    recipe: str,
    version: str,
    cookbook: str,
    target: str,
    dry_run: bool,
    clean: bool,
):
    """
    Download, extract, build, and install a recipe.

    This is just an alias for `recipe build`.
    """
    ctx.forward(recipe_build)


@cli.command("list")
@click.pass_context
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    default=False,
    help="List all recipes, including those for other platforms. [optional]",
)
def list_alias(ctx, verbose: bool, all: bool):
    """
    List a list of recipes you can build on this platform.

    This is just an alias for `recipe list`.
    """
    ctx.forward(recipe_list)


@cli.command("show")
@click.pass_context
@click.argument("recipe", required=True)
@click.option("--version", "-v", default="", help="Version. [optional]")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
@click.option(
    "--all",
    "-a",
    is_flag=True,
    default=False,
    help="Show all recipe variants, including those for other platforms. [optional]",
)
def show_alias(ctx, recipe: str, version: str, verbose: bool, all: bool):
    """
    Show details about a specific recipe.

    This is just an alias for `recipe show`.
    """
    ctx.forward(recipe_show)


@cli.command("update")
@click.pass_context
def update_alias(ctx):
    """
    Update local copy of cookbooks (using Git).

    This is just an alias for `recipe show`.
    """
    ctx.forward(cookbook_update)


if __name__ == "__main__":
    sys.argv[0] = "mussels"
    cli(sys.argv[1:])
