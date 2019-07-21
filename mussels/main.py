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

from collections import defaultdict
import datetime
import json
import logging
import os
from pathlib import Path
import platform
import shutil
import sys
import time

import click
import coloredlogs

import mussels.bookshelf
from mussels.utils import read
from mussels.utils.versions import sort_by_version, compare_versions, get_item_version
from mussels.utils.click import MusselsModifier, ShortNames

logging.basicConfig()
module_logger = logging.getLogger("mussels")
coloredlogs.install(level="DEBUG")
module_logger.setLevel(logging.DEBUG)


class Mussels:
    """
    The Mussels class provides context required for all Mussels features.
    """

    cookbooks = defaultdict(list)

    recipes = defaultdict(dict)
    sorted_recipes = defaultdict(list)

    tools = defaultdict(dict)
    sorted_tools = defaultdict(list)

    def __init__(self, temp_dir: str = ""):

        self.app_data_dir = os.path.join(str(Path.home()), ".mussels")

        if temp_dir != "":
            self.temp_dir = temp_dir
        else:
            self.temp_dir = os.path.join(self.app_data_dir, "tmp")

    def read_cookbook(self, cookbook, cookbook_path):
        """
        Load the recipes and tools from a single cookbook.
        """
        sorted_recipes = defaultdict(list)
        sorted_tools = defaultdict(list)

        self.cookbooks[cookbook] = {}

        # Load the recipes and collections
        recipes = read.recipes(os.path.join(cookbook_path, "recipes"))
        recipes.update(read.recipes(os.path.join(cookbook_path, "collections")))
        sort_by_version(recipes, sorted_recipes)

        self.cookbooks[cookbook]["recipes"] = sorted_recipes
        for recipe in recipes.keys():
            if recipes[recipe]["version"] not in self.recipes[recipe].keys():
                self.recipes[recipe][recipes[recipe]["version"]] = []
            self.recipes[recipe][recipes[recipe]["version"]].append(
                {"cookbook": cookbook, "recipe": recipes[recipe]}
            )

        # Load the tools
        tools = read.tools(os.path.join(cookbook_path, "tools"))
        sort_by_version(tools, sorted_tools)

        self.cookbooks[cookbook]["tools"] = sorted_tools
        for tool in tools.keys():
            if tools[tool]["version"] not in self.tools[tool].keys():
                self.tools[tool][tools[tool]["version"]] = []
            self.tools[tool][tools[tool]["version"]].append(
                {"cookbook": cookbook, "tool": tools[tool]}
            )

    def read_bookshelf(self):
        """
        Load the recipes and tools from:
        - cookbooks in ~/.mussels/bookshelf
        - local "mussels" directory
        """
        # Load the recipes and tools from all cookbooks in ~/.mussels/bookshelf
        bookshelf = os.path.join(self.app_data_dir, "bookshelf")
        if os.path.isdir(bookshelf):
            for cookbook in os.listdir(bookshelf):
                cookbook_path = os.path.join(
                    os.path.join(self.app_data_dir, "bookshelf"), cookbook
                )
                if os.path.isdir(cookbook_path):
                    self.read_cookbook(cookbook, cookbook_path)

        # Load recipes and tools from `cwd`/mussels directory, if any exist.
        local_recipes = os.path.join(os.getcwd(), "mussels")
        if os.path.isdir(local_recipes):
            self.read_cookbook("local_recipes", local_recipes)

        # Sort the recipes
        sort_by_version(self.recipes, self.sorted_recipes)
        sort_by_version(self.tools, self.sorted_tools)

    def update_bookshelf(self):
        """
        Attempt to update each cookbook in the bookshelf using `git pull`

        If `git` is available, clone each of the cookbooks.
        If it isn't, warn the user they should probably install Git and add it to their PATH.
        """
        # Check for git.

        # Get url for each cookbook from the
        for book in mussels.bookshelf.cookbooks:
            self.cookbooks[book]["url"] = mussels.bookshelf.cookbooks[book]["url"]

        # Create ~/.mussels/bookshelf if it doesn't already exist.
        if not os.path.exists(os.path.join(self.app_data_dir, "bookshelf")):
            os.makedirs(os.path.join(self.app_data_dir, "bookshelf"))

    def build_recipe(self, recipe: str, version: str, toolchain: dict) -> dict:
        """
        Build a specific recipe.

        Args:
            recipe:     The recipe name with no version information.
            version:    The recipe version.
        """
        result = {"name": recipe, "version": version, "success": False}

        start = time.time()

        module_logger.info(f"Attempting to build {recipe}...")

        if version == "":
            # Use the default (highest) version
            try:
                version = self.sorted_recipes[recipe][0]
            except KeyError:
                module_logger.error(f"FAILED to find recipe: {recipe}!")
                result["time elapsed"] = time.time() - start
                return result

        try:
            builder = self.recipes[recipe][version](toolchain, self.temp_dir)
        except KeyError:
            module_logger.error(f"FAILED to find recipe: {recipe}-{version}!")
            result["time elapsed"] = time.time() - start
            return result

        if builder.__build() == False:
            module_logger.error(f"FAILURE: {recipe}-{version} build failed!\n")
        else:
            module_logger.info(f"Success: {recipe}-{version} build succeeded. :)\n")
            result["success"] = True

        result["time elapsed"] = time.time() - start

        return result

    def get_recipe_version(self, recipe: str) -> tuple:
        """
        Select recipe version based on version requirements.
        Eliminate recipe versions and sorted tools versions based on
        these requirements, and the required_tools requirements of remaining recipes.

        Args:
            recipe:     A specific recipe.
        """
        self.sorted_recipes, recipe_version = get_item_version(
            recipe, self.sorted_recipes
        )

        for name in self.sorted_recipes:
            for version in self.sorted_recipes[name]:
                for tool in self.recipes[name][version].required_tools:
                    try:
                        self.sorted_tools, _ = get_item_version(tool, self.sorted_tools)
                    except:
                        raise Exception(
                            f"No {tool} version available to satisfy requirement for build."
                        )

        return recipe_version

    def get_all_recipes(self, recipe: str, chain: list) -> list:
        """
        Identify all recipes that must be built given a specific recipe.

        Args:
            recipe:     A specific recipe to build.
            chain:      (in,out) A dependency chain starting from the first
                        recursive call used to identify circular dependencies.
        """
        name, version = self.get_recipe_version(recipe)

        if (len(chain) > 0) and (name == chain[0]):
            raise ValueError(f"Circular dependencies found! {chain}")
        chain.append(name)

        recipes = []

        recipes.append(recipe)

        dependencies = self.recipes[name][version].dependencies
        for dependency in dependencies:
            recipes += self.get_all_recipes(dependency, chain)

        return recipes

    def get_build_batches(self, recipes: list) -> list:
        """
        Get list of build batches that can be built concurrently.

        Args:
            recipes:    A list of recipes to build.
        """

        def get_all_recipes_from_list(recipes: list) -> set:
            """
            Identify all recipes (dependencies) that must be built given a list
            of recipes that the user desires to build.
            """
            all_recipes = []
            for recipe in recipes:
                all_recipes += self.get_all_recipes(recipe, [])

            return set(all_recipes)

        # Identify all recipes that must be built given list of desired builds.
        all_recipes = get_all_recipes_from_list(recipes)

        # Build a map of recipes (name,version) tuples to sets of dependency (name,version) tuples
        name_to_deps = {}
        for recipe in all_recipes:
            name, version = self.get_recipe_version(recipe)
            dependencies = self.recipes[name][version].dependencies
            name_to_deps[name] = set(
                [self.get_recipe_version(dependency)[0] for dependency in dependencies]
            )

        batches = []

        # While there are dependencies to solve...
        while name_to_deps:

            # Get all recipes with no dependencies
            ready = {recipe for recipe, deps in name_to_deps.items() if not deps}

            # If there aren't any, we have a loop in the graph
            if not ready:
                msg = "Circular dependencies found!\n"
                msg += json.dumps(name_to_deps, indent=4)
                raise ValueError(msg)

            # Remove them from the dependency graph
            for recipe in ready:
                del name_to_deps[recipe]
            for deps in name_to_deps.values():
                deps.difference_update(ready)

            # Add the batch to the list
            batches.append(ready)

        # Return the list of batches
        return batches

    def perform_build(
        self, recipe: str, version: str, results: list, dryrun: bool = False
    ) -> bool:
        """
        Execute a build of a recipe.

        Args:
            recipe:     The recipe to build. Use "all" to build newest version of all recipes.
            version:    A specific version to build.  Leave empty ("") to build the newest.
            results:    (out) A list of dictionaries describing the results of the build.
            dryrun:     (optional) Don't actually build, just print the build chain.
        """

        def print_results(results: list):
            """
            Print the build results in a pretty way.

            Args:
                results:    (out) A list of dictionaries describing the results of the build.
            """
            for result in results:
                if result["success"] == True:
                    module_logger.info(
                        f"Successful build of {result['name']}-{result['version']} completed in {datetime.timedelta(0, result['time elapsed'])}."
                    )
                else:
                    module_logger.error(
                        f"Failure building {result['name']}-{result['version']}, terminated after {datetime.timedelta(0, result['time elapsed'])}"
                    )

        batches = []

        if recipe == "all":
            batches = self.get_build_batches(self.recipes.keys())
        else:
            if version == "":
                batches = self.get_build_batches([recipe])
            else:
                batches = self.get_build_batches([f"{recipe}=={version}"])

        #
        # Validate toolchain
        #
        # Collect set of required tools for entire build.
        toolchain = {}
        preferred_tool_versions = set()
        for i, bundle in enumerate(batches):
            for j, recipe in enumerate(bundle):
                for tool in self.recipes[recipe][
                    self.sorted_recipes[recipe][0]
                ].required_tools:
                    _, tool_version = get_item_version(tool, self.sorted_tools)
                    preferred_tool_versions.add(tool_version)

        # Check if required tools are installed
        missing_tools = []
        for preferred_tool_version in preferred_tool_versions:
            tool_found = False
            prefered_tool = self.tools[preferred_tool_version[0]][
                preferred_tool_version[1]
            ](self.temp_dir)

            if prefered_tool.detect() == True:
                # Preferred tool version is available.
                tool_found = True
                toolchain[preferred_tool_version[0]] = prefered_tool
                module_logger.info(
                    f"    {preferred_tool_version[0]}-{preferred_tool_version[1]} found."
                )
            else:
                # Check if non-prefered (older, but compatible) version is available.
                module_logger.warning(
                    f"    {preferred_tool_version[0]}-{preferred_tool_version[1]} not found."
                )

                if len(self.sorted_tools[preferred_tool_version[0]]) > 1:
                    module_logger.warning(
                        f"        Checking for alternative versions..."
                    )
                    alternative_versions = self.sorted_tools[preferred_tool_version[0]][
                        1:
                    ]

                    for alternative_version in alternative_versions:
                        alternative_tool = self.tools[preferred_tool_version[0]][
                            alternative_version
                        ](self.temp_dir)

                        if alternative_tool.detect() == True:
                            # Found a compatible version to use.
                            tool_found = True
                            toolchain[preferred_tool_version[0]] = alternative_tool
                            # Select the version so it will be the default.
                            self.sorted_tools, _ = get_item_version(
                                f"{preferred_tool_version[0]}={alternative_version}",
                                self.sorted_tools,
                            )
                            module_logger.info(
                                f"    Alternative version {preferred_tool_version[0]}-{alternative_version} found."
                            )
                        else:
                            module_logger.warning(
                                f"    Alternative version {preferred_tool_version[0]}-{alternative_version} not found."
                            )

                if tool_found == False:
                    # Tool is missing.  Build will fail.
                    missing_tools.append(preferred_tool_version)

        if len(missing_tools) > 0:
            module_logger.warning("")
            module_logger.warning(
                "The following tools are missing and must be installed for this build to continue:"
            )
            for tool_version in missing_tools:
                module_logger.warning(f"    {tool_version[0]}-{tool_version[1]}")
                # TODO: Provide an option to install the missing tools automatically.

            sys.exit(1)

        module_logger.info("Toolchain:")
        for tool in toolchain:
            module_logger.info(f"   {tool}-{toolchain[tool].version}")

        #
        # Perform Build
        #
        if dryrun:
            module_logger.warning("")
            module_logger.warning(r"    ___   ___   _         ___   _     _    ")
            module_logger.warning(r"   | | \ | |_) \ \_/     | |_) | | | | |\ |")
            module_logger.warning(r"   |_|_/ |_| \  |_|      |_| \ \_\_/ |_| \|")
            module_logger.warning("")
            module_logger.info("Build-order of requested recipes:")

        idx = 0
        failure = False
        for i, bundle in enumerate(batches):
            for j, recipe in enumerate(bundle):
                idx += 1

                if dryrun:
                    module_logger.info(
                        f"   {idx:2} [{i}:{j:2}]: {recipe}-{self.sorted_recipes[recipe][0]}"
                    )
                    module_logger.debug(f"      Tool(s):")
                    for tool in self.recipes[recipe][
                        self.sorted_recipes[recipe][0]
                    ].required_tools:
                        _, tool_version = get_item_version(tool, self.sorted_tools)
                        module_logger.debug(
                            f"        {tool_version[0]}-{tool_version[1]}"
                        )
                    continue

                if failure:
                    module_logger.warning(
                        f"Skipping {recipe} build due to prior failure."
                    )
                else:
                    result = build_recipe(
                        recipe, self.sorted_recipes[recipe][0], toolchain
                    )
                    results.append(result)
                    if result["success"] == False:
                        failure = True

        if not dryrun:
            print_results(results)

        if failure:
            return False
        return True

    def list_recipes(self):
        """
        Print out a list of all recipes and all collections.
        """
        module_logger.info("Recipes:")
        for recipe in self.sorted_recipes:
            if self.recipes[recipe][self.sorted_recipes[recipe][0]].collection == False:
                outline = f"    {recipe:10} ["
                for i, version in enumerate(self.sorted_recipes[recipe]):
                    if i == 0:
                        outline += f" {version}*"
                    else:
                        outline += f", {version}"
                outline += " ]"
                module_logger.info(outline)

        module_logger.info("")
        module_logger.info("Collections:")
        for recipe in self.sorted_recipes:
            if self.recipes[recipe][self.sorted_recipes[recipe][0]].collection == True:
                outline = f"    {recipe:10} ["
                for i, version in enumerate(self.sorted_recipes[recipe]):
                    if i == 0:
                        outline += f" {version}*"
                    else:
                        outline += f", {version}"
                outline += " ]"
                module_logger.info(outline)


#
# CLI Interface
#
@click.group(cls=MusselsModifier, epilog=__doc__)
def cli():
    pass


@cli.group(cls=ShortNames, help="Commands that operate on recipes.")
def recipe():
    pass


@recipe.command("list")
def recipe_list():
    """
    Print the list of all known recipes.
    An asterisk indicates default (highest) version.
    """
    my_mussels = Mussels()

    my_mussels.read_bookshelf()

    my_mussels.list_recipes()


@recipe.command("build")
@click.argument("recipe", required=False, default="all")
@click.option(
    "--version",
    "-v",
    default="",
    help="Version of recipe to build. May not be combined with @version in recipe name. [optional]",
)
@click.option(
    "--tempdir",
    "-t",
    default="out",
    help="Build in a specific directory instead of a temp directory. [optional]",
)
@click.option(
    "--dryrun",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
def recipe_build(recipe: str, version: str, tempdir: str, dryrun: bool):
    """
    Download, extract, build, and install a recipe.
    """

    my_mussels = Mussels(temp_dir=os.path.abspath(tempdir))

    my_mussels.read_bookshelf()

    results = []

    success = my_mussels.perform_build(recipe, version, results, dryrun)
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
    "--tempdir",
    "-t",
    default="out",
    help="Build in a specific directory instead of a temp directory. [optional]",
)
@click.option(
    "--dryrun",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
@click.pass_context
def build_alias(ctx, recipe: str, version: str, tempdir: str, dryrun: bool):
    """
    Download, extract, build, and install a recipe.

    This is just an alias for `recipe build`.
    """
    ctx.forward(recipe_build)


@cli.command("list")
@click.pass_context
def list_alias(ctx):
    """
    List all known recipes.

    This is just an alias for `recipe list`.
    """
    ctx.forward(recipe_list)


if __name__ == "__main__":
    cli(sys.argv[1:])
