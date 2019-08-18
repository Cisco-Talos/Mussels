#!/usr/bin/env python

r"""
  __    __     __  __     ______     ______     ______     __         ______
 /\ "-./  \   /\ \/\ \   /\  ___\   /\  ___\   /\  ___\   /\ \       /\  ___\
 \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \___  \  \ \  __\   \ \ \____  \ \___  \
  \ \_\ \ \_\  \ \_____\  \/\_____\  \/\_____\  \ \_____\  \ \_____\  \/\_____\
   \/_/  \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/

A tool to download, build, and assemble application dependencies.
                                    Brought to you by the Clam AntiVirus Team.

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
coloredlogs.install(level="DEBUG")
module_logger.setLevel(logging.DEBUG)

#
# CLI Interface
#
@click.group(cls=MusselsModifier, epilog=__doc__)
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
    my_mussels = Mussels()

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
    my_mussels = Mussels()

    my_mussels.show_cookbook(cookbook, verbose)


@cookbook.command("update")
def cookbook_update():
    """
    Update the cookbooks from the internet.
    """
    my_mussels = Mussels()

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
    my_mussels = Mussels()

    if yes != True:
        print(
            f"\nDisclaimer: There is a non-zero risk when running code downloaded from the internet.\n"
        )
        response = input(
            f"Are you sure you would like to trust recipes from cookbook '{cookbook}'? [N/y]\n"
        )
        response = response.strip().lower()

        if response != "y":
            return

    my_mussels.config_trust_cookbook(cookbook)


@cookbook.command("add")
@click.argument("cookbook", required=True)
@click.option(
    "--author", "-a", default="", help="Author. [required for non-interactive modes]"
)
@click.option(
    "--url",
    "-u",
    default="",
    help="Git repository URL. [required for non-interactive modes]",
)
@click.option(
    "--yes",
    "-y",
    is_flag=True,
    default=False,
    help="Confirm trust. [required for non-interactive modes]",
)
def cookbook_add(cookbook, author, url, yes):
    """
    Add a cookbook to the list of known cookbooks.
    """
    my_mussels = Mussels()

    my_mussels.config_add_cookbook(cookbook, author, url)


@cookbook.command("remove")
@click.argument("cookbook", required=True)
def cookbook_remove(cookbook):
    """
    Remove a cookbook from the list of known cookbooks.
    """
    my_mussels = Mussels()

    my_mussels.config_remove_cookbook(cookbook)


@cli.group(cls=ShortNames, help="Commands that operate on recipes.")
def recipe():
    pass


@recipe.command("list")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
def recipe_list(verbose: bool):
    """
    Print the list of all known recipes.
    An asterisk indicates default (highest) version.
    """
    my_mussels = Mussels()

    my_mussels.list_recipes(verbose)


@recipe.command("show")
@click.argument("recipe", required=True)
@click.option("--version", "-v", default="", help="Version. [optional]")
@click.option(
    "--verbose", "-V", is_flag=True, default=False, help="Verbose output. [optional]"
)
def recipe_show(recipe: str, version: str, verbose: bool):
    """
    Show details about a specific recipe.
    """
    my_mussels = Mussels()

    my_mussels.show_recipe(recipe, version, verbose)


@recipe.command("build")
@click.argument("recipe", required=False, default="all")
@click.option(
    "--version",
    "-v",
    default="",
    help="Version of recipe to build. May not be combined with @version in recipe name. [optional]",
)
@click.option(
    "--cookbook", "-c", default="", help="Specific cookbook to use . [optional]"
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
def recipe_build(recipe: str, version: str, cookbook: str, dry_run: bool):
    """
    Download, extract, build, and install a recipe.
    """

    my_mussels = Mussels()

    results = []

    success = my_mussels.build_recipe(recipe, version, cookbook, results, dry_run)
    if success == False:
        sys.exit(1)

    sys.exit(0)


#
# Command Aliases
#
@cli.command("build")
@click.argument("recipe", required=False, default="all")
@click.option(
    "--version",
    "-v",
    default="",
    help="Version of recipe to build. May not be combined with @version in recipe name. [optional]",
)
@click.option(
    "--cookbook", "-c", default="", help="Specific cookbook to use . [optional]"
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
@click.pass_context
def build_alias(ctx, recipe: str, version: str, cookbook: str, dry_run: bool):
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
def list_alias(ctx, verbose: bool):
    """
    List all known recipes.

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
def show_alias(ctx, recipe: str, version: str, verbose: bool):
    """
    Show details about a specific recipe.

    This is just an alias for `recipe show`.
    """
    ctx.forward(recipe_show)


@cli.command("update")
@click.pass_context
def update_alias(ctx):
    """
    Show details about a specific recipe.

    This is just an alias for `recipe show`.
    """
    ctx.forward(cookbook_update)


if __name__ == "__main__":
    cli(sys.argv[1:])
