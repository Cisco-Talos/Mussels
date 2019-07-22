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
import fnmatch
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
import git

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

    cookbooks = defaultdict(dict)

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

        # load config, if exists.
        try:
            with open(os.path.join(self.app_data_dir, "config.json"), "r") as cache_file:
                self.tools = json.dump(cache_file)
        except:
            module_logger.debug(f"No mussels config found.")

    def read_cookbook(self, cookbook: str, cookbook_path: str) -> bool:
        """
        Load the recipes and tools from a single cookbook.
        """
        sorted_recipes = defaultdict(list)
        sorted_tools = defaultdict(list)

        self.cookbooks[cookbook] = {}

        # Load the recipes and collections
        recipes = read.recipes(os.path.join(cookbook_path, "recipes"))
        recipes.update(read.recipes(os.path.join(cookbook_path, "collections")))
        sorted_recipes = sort_by_version(recipes)

        self.cookbooks[cookbook]["recipes"] = sorted_recipes
        for recipe in recipes.keys():
            for version in recipes[recipe]:
                if version not in self.recipes[recipe].keys():
                    self.recipes[recipe][version] = {}
                self.recipes[recipe][version][cookbook] = recipes[recipe][version]

        # Load the tools
        tools = read.tools(os.path.join(cookbook_path, "tools"))
        sorted_tools = sort_by_version(tools)

        self.cookbooks[cookbook]["tools"] = sorted_tools
        for tool in tools.keys():
            for version in tools[tool]:
                if version not in self.tools[tool].keys():
                    self.tools[tool][version] = {}
                self.tools[tool][version][cookbook] = tools[tool][version]

        if len(recipes) == 0 and len(tools) == 0:
            return False

        return True

    def read_bookshelf(self) -> bool:
        """
        Load the recipes and tools from cookbooks in ~/.mussels/bookshelf
        """
        # Load the recipes and tools from all cookbooks in ~/.mussels/bookshelf
        bookshelf = os.path.join(self.app_data_dir, "bookshelf")
        if os.path.isdir(bookshelf):
            for cookbook in os.listdir(bookshelf):
                cookbook_path = os.path.join(
                    os.path.join(self.app_data_dir, "bookshelf"), cookbook
                )
                if os.path.isdir(cookbook_path):
                    if self.read_cookbook(cookbook, cookbook_path) == False:
                        module_logger.warning(f"Failed to read any recipes or tools from cookbook: {cookbook}")

            # Update the cache files in ~/.mussels/recipe_cache
            try:
                if not os.path.isdir(os.path.join(self.app_data_dir, "recipe_cache")):
                    os.makedirs(os.path.join(self.app_data_dir, "recipe_cache"))
                with open(os.path.join(self.app_data_dir, "recipe_cache", "bookshelf.json"), "wx") as cache_file:
                    json.dump(self.cookbooks, cache_file)
                with open(os.path.join(self.app_data_dir, "recipe_cache", "recipes.json"), "wx") as cache_file:
                    json.dump(self.recipes, cache_file)
                with open(os.path.join(self.app_data_dir, "recipe_cache", "tools.json"), "wx") as cache_file:
                    json.dump(self.tools, cache_file)
            except Exception as exc:
                module_logger.warning(f"Failed to update recipe_cache.  Exception: {exc}")
                return False

        return True

    def read_local_recipes(self) -> bool:
        """
        Load the recipes and tools from local "mussels" directory
        """
        # Load recipes and tools from `cwd`/mussels directory, if any exist.
        local_recipes = os.path.join(os.getcwd(), "mussels")
        if os.path.isdir(local_recipes):
            if self.read_cookbook("local", local_recipes) == False:
                return False

            self.cookbooks["local"]["url"] = ""
            self.cookbooks["local"]["path"] = local_recipes

        return True

    def load_recipe_cache(self) -> bool:
        '''
        Load recipes from the cache.
        '''
        try:
            with open(os.path.join(self.app_data_dir, "recipe_cache", "bookshelf.json"), "r") as cache_file:
                self.cookbooks = json.dump(cache_file)
            with open(os.path.join(self.app_data_dir, "recipe_cache", "recipes.json"), "r") as cache_file:
                self.recipes = json.dump(cache_file)
            with open(os.path.join(self.app_data_dir, "recipe_cache", "tools.json"), "r") as cache_file:
                self.tools = json.dump(cache_file)
        except:
            module_logger.debug(f"Unable to load recipe cache.")
            return False

        return True

    def load_recipes(self) -> bool:
        """
        Load the recipes.
        """
        # Clear the in-memory cache.
        self.cookbooks = defaultdict(dict)
        self.recipes = defaultdict(dict)
        self.sorted_recipes = defaultdict(list)
        self.tools = defaultdict(dict)
        self.sorted_tools = defaultdict(list)

        # Load bookshelf from the cache, if exists.
        if self.load_recipe_cache() == False:
            # Else load by reading the cookbooks in the bookshelf, if that exists.
            self.read_bookshelf()

        # Load recipes from the local mussels directory, if those exists.
        if self.read_local_recipes() == False:
            module_logger.warning(f"Local `mussels` directory found, but failed to load any recipes or tools.")

        self.sorted_recipes = sort_by_version(self.recipes)
        self.sorted_tools = sort_by_version(self.tools)

        if len(self.sorted_recipes) == 0:
            module_logger.warning(f"Failed to find any recipes.")
            module_logger.warning(f"Local recipes must be stored under a `./mussels` directory.")
            module_logger.warning(f"To update your local bookshelf of public cookbooks, run `mussels update`.")
            return False

        return True

    def update_cookbooks(self) -> bool:
        """
        Attempt to update each cookbook in using Git to clone or pull each repo.
        If git isn't available, warn the user they should probably install Git and add it to their PATH.
        """
        # Get url for each cookbook from the
        for book in mussels.bookshelf.cookbooks:
            self.cookbooks[book]["url"] = mussels.bookshelf.cookbooks[book]["url"]

        # Create ~/.mussels/bookshelf if it doesn't already exist.
        os.makedirs(os.path.join(self.app_data_dir, "bookshelf"), exist_ok=True)

        for book in self.cookbooks:
            repo_dir = os.path.join(self.app_data_dir, "bookshelf", book)

            if self.cookbooks[book]["url"] != "":
                if not os.path.isdir(repo_dir):
                    repo = git.Repo.clone_from(self.cookbooks[book]["url"], repo_dir)
                else:
                    repo = git.Repo(repo_dir)
                    out = repo.git.pull()


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
        self, recipe: str, version: str, results: list, dry_run: bool = False
    ) -> bool:
        """
        Execute a build of a recipe.

        Args:
            recipe:     The recipe to build. Use "all" to build newest version of all recipes.
            version:    A specific version to build.  Leave empty ("") to build the newest.
            results:    (out) A list of dictionaries describing the results of the build.
            dry_run:     (optional) Don't actually build, just print the build chain.
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
        if dry_run:
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

                if dry_run:
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

        if not dry_run:
            print_results(results)

        if failure:
            return False
        return True

    def show_recipe(self, recipe_match: str, version_match: str, verbose: bool = False):
        """
        Search recipes for a specific recipe and print recipe details.
        """

        def print_recipe_details(recipe: str, version: str):
            """
            Print recipe information.
            """
            cookbooks = list(self.recipes[recipe][version].keys())
            module_logger.info(f"    {recipe} v{version};  from: {cookbooks}")

            if verbose:
                module_logger.info("")
                for cookbook in cookbooks:
                    module_logger.info(f"        Cookbook: {cookbook}")

                    book_recipe = self.recipes[recipe][version][cookbook]
                    module_logger.info(
                        f"            dependencies:   {book_recipe.dependencies}"
                    )
                    module_logger.info(
                        f"            required tools: {book_recipe.required_tools}"
                    )
                    module_logger.info(
                        f"            target arch:    {list(book_recipe.build_script.keys())}"
                    )

                module_logger.info("")

        found = False

        if version_match == "":
            module_logger.info(
                f'Searching for recipe matching name: "{recipe_match}"...'
            )
        else:
            module_logger.info(
                f'Searching for recipe matching name: "{recipe_match}", version: "{version_match}"...'
            )
        # Attempt to match the recipe name
        for recipe in self.sorted_recipes:
            if fnmatch.fnmatch(recipe, recipe_match):
                if version_match == "":
                    found = True

                    # Show info for every version
                    for version in self.sorted_recipes[recipe]:
                        print_recipe_details(recipe, version)
                    break
                else:
                    # Attempt to match the version too
                    for version in self.sorted_recipes[recipe]:
                        cookbooks = list(self.recipes[recipe][version].keys())
                        if fnmatch.fnmatch(version, version_match):
                            found = True

                            print_recipe_details(recipe, version)
                            break
                    if found:
                        break
        if not found:
            if version_match == "":
                module_logger.warning(f'No recipe matching name: "{recipe_match}"')
            else:
                module_logger.warning(
                    f'No recipe matching name: "{recipe_match}", version: "{version_match}"'
                )

    def list_recipes(self, verbose: bool = False):
        """
        Print out a list of all recipes and all collections.
        """
        has_collections = False

        module_logger.info("Recipes:")
        for recipe in self.sorted_recipes:
            newest_version = self.sorted_recipes[recipe][0]
            cookbooks = list(self.recipes[recipe][newest_version].keys())
            if self.recipes[recipe][newest_version][cookbooks[0]].collection == False:
                if not verbose:
                    outline = f"    {recipe:10} ["
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            outline += f" {version}*"
                        else:
                            outline += f", {version}"
                    outline += " ]"
                    module_logger.info(outline)
                else:
                    module_logger.info(f"    {recipe}")
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            cookbooks = list(self.recipes[recipe][version].keys())
                            module_logger.info(
                                f"       *{version:10} ( provided by: {cookbooks} )"
                            )
                        else:
                            module_logger.info(
                                f"        {version:10} ( provided by: {cookbooks} )"
                            )

        for recipe in self.sorted_recipes:
            newest_version = self.sorted_recipes[recipe][0]
            cookbooks = list(self.recipes[recipe][newest_version].keys())
            if self.recipes[recipe][newest_version][cookbooks[0]].collection == True:
                if not has_collections:
                    module_logger.info("")
                    module_logger.info("Collections:")
                    has_collections = True

                if not verbose:
                    outline = f"    {recipe:10} ["
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            outline += f" {version}*"
                        else:
                            outline += f", {version}"
                    outline += " ]"
                    module_logger.info(outline)
                else:
                    module_logger.info(f"    {recipe}")
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            module_logger.info(
                                f"       *{version:10} ( provided by: {cookbooks} )"
                            )
                        else:
                            module_logger.info(
                                f"        {version:10} ( provided by: {cookbooks} )"
                            )

    def list_cookbooks(self, verbose: bool = False):
        """
        Print out a list of all cookbooks.
        """
        module_logger.info("Cookbooks:")
        for cookbook in self.cookbooks:
            module_logger.info(f"    {cookbook}")
            if cookbook == "local":
                module_logger.info(f"        url:  n/a")
            else:
                module_logger.info(f"        url:  {self.cookbooks[cookbook]['url']}")
            module_logger.info(f"        path: {self.cookbooks[cookbook]['path']}")
            module_logger.info(f"")

    def show_cookbook(self, cookbook_match: str, verbose: bool):
        """
        Search cookbooks for a specific cookbook and print the details.
        """
        found = False

        module_logger.info(f'Searching for cookbook matching name: "{cookbook_match}"...')

        # Attempt to match the cookbook name
        for cookbook in self.cookbooks:
            if fnmatch.fnmatch(cookbook, cookbook_match):
                found = True

                module_logger.info(f"    {cookbook}")
                if cookbook == "local":
                    module_logger.info(f"        url:  n/a")
                else:
                    module_logger.info(f"        url:  {self.cookbooks[cookbook]['url']}")
                module_logger.info(f"        path: {self.cookbooks[cookbook]['path']}")

                if verbose:
                    module_logger.info(f"")
                    if len(self.cookbooks[cookbook]["recipes"].keys()) > 0:
                        module_logger.info(f"    Recipes:")
                        for recipe in self.cookbooks[cookbook]["recipes"]:
                            module_logger.info(f"        {recipe} : {self.cookbooks[cookbook]['recipes'][recipe]}")
                    if len(self.cookbooks[cookbook]["tools"].keys()) > 0:
                        module_logger.info(f"    Tools:")
                        for tool in self.cookbooks[cookbook]["tools"]:
                            module_logger.info(f"        {tool} : {self.cookbooks[cookbook]['tools'][tool]}")

        if not found:
            module_logger.warning(f'No cookbook matching name: "{cookbook_match}"')



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

    my_mussels.load_recipes()

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

    my_mussels.load_recipes()

    my_mussels.show_cookbook(cookbook, verbose)

@cookbook.command("update")
def cookbook_update():
    """
    Update the cookbooks from the internet.
    """
    my_mussels = Mussels()

    my_mussels.load_recipes()

    my_mussels.update_cookbooks()




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

    my_mussels.load_recipes()

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

    my_mussels.load_recipes()

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
    "--tempdir",
    "-t",
    default="out",
    help="Build in a specific directory instead of a temp directory. [optional]",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
def recipe_build(recipe: str, version: str, tempdir: str, dry_run: bool):
    """
    Download, extract, build, and install a recipe.
    """

    my_mussels = Mussels(temp_dir=os.path.abspath(tempdir))

    my_mussels.load_recipes()

    results = []

    success = my_mussels.perform_build(recipe, version, results, dry_run)
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
    "--dry-run",
    "-d",
    is_flag=True,
    help="Print out the version dependency graph without actually doing a build. [optional]",
)
@click.pass_context
def build_alias(ctx, recipe: str, version: str, tempdir: str, dry_run: bool):
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


if __name__ == "__main__":
    cli(sys.argv[1:])
