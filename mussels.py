r'''
  __    __     __  __     ______     ______     ______     __         ______
 /\ "-./  \   /\ \/\ \   /\  ___\   /\  ___\   /\  ___\   /\ \       /\  ___\
 \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \___  \  \ \  __\   \ \ \____  \ \___  \
  \ \_\ \ \_\  \ \_____\  \/\_____\  \/\_____\  \ \_____\  \ \_____\  \/\_____\
   \/_/  \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/

A tool to download, build, and assemble application dependencies.
                                    Brought to you by the Clam AntiVirus Team.

Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
'''

'''
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
'''

from collections import defaultdict
import datetime
import json
import logging
import os
import pkgutil
import platform
import shutil
import sys
import time

import click
import coloredlogs

logging.basicConfig()
module_logger = logging.getLogger('mussels')
coloredlogs.install(level='DEBUG')
module_logger.setLevel(logging.DEBUG)

__all__ = []

RECIPES = defaultdict(dict)
SORTED_RECIPES = defaultdict(list)

TOOLS = defaultdict(dict)
SORTED_TOOLS = defaultdict(list)

def version_keys(s):
    import re
    keys = []
    for u in s.split('.'):
        for v in re.split(r'(\d+)',u):
            try:
                val = int(v)
            except:
                val = str(v)
            keys.append(val)
    return keys


def collect_recipes(recipe_path):
    '''
    Collect all Recipes in directory.
    '''
    global __all__
    global RECIPES
    global SORTED_RECIPES

    for loader, module_name, _ in pkgutil.walk_packages([recipe_path]):
        __all__.append(module_name)
        _module = loader.find_module(module_name).load_module(module_name)
        globals()[module_name] = _module
        if "Recipe" in dir(_module):
            RECIPES[_module.Recipe.name][_module.Recipe.version] = _module.Recipe

    # Sort the recipes, and determine the highest versions.
    for recipe in RECIPES:
        versions_list = list(RECIPES[recipe].keys())
        versions_list.sort(key=version_keys)
        versions_list.reverse()
        for version in versions_list:
            SORTED_RECIPES[recipe].append(version)

def collect_tools(tool_path):
    '''
    Collect all Tools in directory.
    '''
    global __all__
    global TOOLS
    global SORTED_TOOLS

    for loader, module_name, _ in pkgutil.walk_packages([tool_path]):
        __all__.append(module_name)
        _module = loader.find_module(module_name).load_module(module_name)
        globals()[module_name] = _module
        if "Tool" in dir(_module):
            TOOLS[_module.Tool.name][_module.Tool.version] = _module.Tool

    # Sort the recipes, and determine the highest versions.
    for tool in TOOLS:
        versions_list = list(TOOLS[tool].keys())
        versions_list.sort(key=version_keys)
        versions_list.reverse()
        for version in versions_list:
            SORTED_TOOLS[tool].append(version)

# Collect all Recipes provided by Mussels recipes directory.
collect_recipes(os.path.join(os.path.split(__file__)[0], "recipes", platform.system()))
# Collect all Recipes in cwd/mussels/recipes/<platform> directory.
collect_recipes(os.path.join(os.getcwd(), "mussels", "recipes", platform.system()))

# Collect all Tools provided by Mussels tools directory.
collect_tools(os.path.join(os.path.split(__file__)[0], "tools", platform.system()))
# Collect all Tools in cwd/mussels/tools/<platform> directory.
collect_tools(os.path.join(os.getcwd(), "mussels", "tools", platform.system()))

def build_recipe(recipe: str, version: str, tempdir: str, toolchain: dict) -> dict:
    '''
    Build a specific recipe.
    '''
    result = {
        'name' : recipe,
        'version' : version,
        'success' : False
    }

    start = time.time()

    module_logger.info(f"Attempting to build {recipe}...")

    if version == "":
        # Use the default (highest) version
        try:
            version = SORTED_RECIPES[recipe][0]
        except KeyError:
            module_logger.error(f"FAILED to find recipe: {recipe}!")
            result['time elapsed'] = time.time() - start
            return result

    try:
        builder = RECIPES[recipe][version](toolchain, tempdir)
    except KeyError:
        module_logger.error(f"FAILED to find recipe: {recipe}-{version}!")
        result['time elapsed'] = time.time() - start
        return result

    if builder.build() == False:
        module_logger.error(f"FAILURE: {recipe}-{version} build failed!\n")
    else:
        module_logger.info(f"Success: {recipe}-{version} build succeeded. :)\n")
        result['success'] = True

    result['time elapsed'] = time.time() - start

    return result

def compare_versions(version_a: str, version_b: str) -> int:
    '''
    Evaluate version strings of two versions.
    Compare if version A against version B.
    :return: -1  if A < B
    :return: 0   if A == B
    :return: 1   if A > B
    '''
    if version_a == version_b:
        return 0

    versions_list = [version_a, version_b]

    versions_list.sort(key=version_keys)

    if versions_list[0] == version_a:
        return -1
    else:
        return 1

def get_item_version(item: str, sorted_items: dict) -> tuple:
    '''
    Convert a item name in the format to a (name, version) tuple:

        name[ >=, <=, >, <, (==|=|@) version ]

    Examples:
        - meepioux
        - blarghus>=1.2.3
        - wheeple@0.2.0
        - pyplo==5.1.0g

    The highest available version will be selected if one is not specified.
    Version requirements will whittle down the list of available versions
    in the sorted_items list.

    If a specific version is specified, all other versions will be disqualified.

    If no versions remain that satisfy build qualifications, an exception will be raised.

    :return: tuple of:
        - the sorted_items and
        - a tuple of the item (name,version) with the highest qualified version.
    '''
    if ">=" in item:
        # GTE requirement found.
        name, version = item.split(">=")
        for i,ver in enumerate(sorted_items[name]):
            cmp = compare_versions(ver, version)
            if (cmp < 0):
                # Version is too low. Remove it, and subsequent versions.
                sorted_items[name] = sorted_items[name][:i]
                break

    elif ">" in item:
        # GT requirement found.
        name, version = item.split(">")
        for i,ver in enumerate(sorted_items[name]):
            cmp = compare_versions(ver, version)
            if (cmp <= 0):
                # Version is too low. Remove it, and subsequent versions.
                sorted_items[name] = sorted_items[name][:i]
                break

    elif "<=" in item:
        # LTE requirement found.
        name, version = item.split("<=")
        try:
            first = sorted_items[name][0]
        except:
            raise Exception(f"No versions available to satisfy requirement for {item}")
        while compare_versions(first, version) > 0:
            # Remove a version from the sorted_items.
            sorted_items[name].remove(first)

            try:
                first = sorted_items[name][0]
            except:
                raise Exception(f"No versions available to satisfy requirement for {item}")

    elif "<" in item:
        # LT requirement found.
        name, version = item.split("<")
        try:
            first = sorted_items[name][0]
        except:
            raise Exception(f"No versions available to satisfy requirement for {item}")
        while compare_versions(first, version) >= 0:
            # Remove a version from the sorted_items.
            sorted_items[name].remove(first)

            try:
                first = sorted_items[name][0]
            except:
                raise Exception(f"No versions available to satisfy requirement for {item}")
    else:
        eq_cond = False
        if ("==" in item):
            name, version = item.split("==")
            eq_cond = True
        elif ("=" in item):
            name, version = item.split("=")
            eq_cond = True
        elif ("-" in item):
            name, version = item.split("-")
            eq_cond = True
        elif ("@" in item):
            name, version = item.split("@")
            eq_cond = True

        if eq_cond == True:
            # EQ requirement found.
            # Try to find the specific version, and remove all others.
            if not version in sorted_items[name]:
                raise Exception(f"No versions available to satisfy requirement for {item}")
            sorted_items[name] = [version]

        else:
            # No version requirement found.
            name = item

    try:
        selected_version = sorted_items[name][0]
    except:
        raise Exception(f"No versions available to satisfy requirement for {item}")

    return (sorted_items, (name, selected_version))

def get_recipe_version(recipe: str) -> tuple:
    '''
    Select recipe version based on version requirements.
    Eliminate recipe versions and sorted tools versions based on
    these requirements, and the required_tools requirements of remaining recipes.
    '''
    global SORTED_RECIPES
    global SORTED_TOOLS

    SORTED_RECIPES, recipe_version = get_item_version(recipe, SORTED_RECIPES)

    for name in SORTED_RECIPES:
        for version in SORTED_RECIPES[name]:
            for tool in RECIPES[name][version].required_tools:
                try:
                    SORTED_TOOLS, _ = get_item_version(tool, SORTED_TOOLS)
                except:
                    raise Exception(f"No {tool} version available to satisfy requirement for build.")

    return recipe_version

def get_all_recipes(recipe: str, chain: list) -> list:
    '''
    Identify all recipes that must be built given a specific recipe.
    '''
    name, version = get_recipe_version(recipe)

    if (len(chain) > 0) and (name == chain[0]):
        raise ValueError(f"Circular dependencies found! {chain}")
    chain.append(name)

    recipes = []

    recipes.append(recipe)

    dependencies = RECIPES[name][version].dependencies
    for dependency in dependencies:
        recipes += get_all_recipes(dependency, chain)

    return recipes

def get_all_recipes_from_list(recipes: list) -> set:
    '''
    Identify all recipes that must be built given a list of recipes.
    '''
    all_recipes = []
    for recipe in recipes:
        all_recipes += get_all_recipes(recipe, [])

    return set(all_recipes)

def get_build_batches(recipes: list) -> list:
    '''
    Get list of build batches that can be built concurrently.
    '''
    # Identify all recipes that must be built given list of desired builds.
    all_recipes = get_all_recipes_from_list(recipes)

    # Build a map of recipes (name,version) tuples to sets of dependency (name,version) tuples
    name_to_deps = {}
    for recipe in all_recipes:
        name, version = get_recipe_version(recipe)
        dependencies = RECIPES[name][version].dependencies
        name_to_deps[name] = set([get_recipe_version(dependency)[0] for dependency in dependencies])

    batches = []

    # While there are dependencies to solve...
    while name_to_deps:

        # Get all recipes with no dependencies
        ready = {recipe for recipe, deps in name_to_deps.items() if not deps}

        # If there aren't any, we have a loop in the graph
        if not ready:
            msg  = "Circular dependencies found!\n"
            msg += json.dumps(name_to_deps, indent=4)
            raise ValueError(msg)

        # Remove them from the dependency graph
        for recipe in ready:
            del name_to_deps[recipe]
        for deps in name_to_deps.values():
            deps.difference_update(ready)

        # Add the batch to the list
        batches.append( ready )

    # Return the list of batches
    return batches

def print_results(results: list):
    '''
    Print the build results in a pretty way.
    '''
    for result in results:
        if result["success"] == True:
            module_logger.info(f"Successful build of {result['name']}-{result['version']} completed in {datetime.timedelta(0, result['time elapsed'])}.")
        else:
            module_logger.error(f"Failure building {result['name']}-{result['version']}, terminated after {datetime.timedelta(0, result['time elapsed'])}")

class SpecialEpilog(click.Group):
    def format_epilog(self, ctx, formatter):
        if self.epilog:
            print(self.epilog)

# Tell click to use our epilog formatter
@click.group(cls=SpecialEpilog, epilog=__doc__, chain=True)
def cli():
    print(__doc__)

@cli.command()
@click.option('--recipe', '-r', required=False,
              type=click.Choice(list(RECIPES.keys()) + ["all"]),
              default="all",
              help='Recipe to build. Format: recipe[@version]')
@click.option('--version', '-v', default="",
              help='Version of recipe to build. May not be combined with @version in recipe name. [optional]')
@click.option('--tempdir', '-t', default="out",
              help='Build in a specific directory instead of a temp directory. [optional]')
@click.option('--dryrun', '-d', is_flag=True,
              help='Print out the version dependency graph without actually doing a build. [optional]')
def build(recipe: str, version: str, tempdir: str, dryrun: bool):
    '''
    Download, extract, build, and install the recipe.
    '''
    global RECIPES
    global SORTED_RECIPES
    global TOOLS
    global SORTED_TOOLS

    tempdir = os.path.abspath(tempdir)

    batches = []
    results = []

    if recipe == "all":
        batches = get_build_batches(RECIPES.keys())
    else:
        if version == "":
            batches = get_build_batches([recipe])
        else:
            batches = get_build_batches([f"{recipe}=={version}"])

    #
    # Validate toolchain
    #
    # Collect set of required tools for entire build.
    toolchain = {}
    preferred_tool_versions = set()
    for i, bundle in enumerate(batches):
        for j, recipe in enumerate(bundle):
            for tool in RECIPES[recipe][SORTED_RECIPES[recipe][0]].required_tools:
                _, tool_version = get_item_version(tool, SORTED_TOOLS)
                preferred_tool_versions.add(tool_version)

    # Check if required tools are installed
    missing_tools = []
    for preferred_tool_version in preferred_tool_versions:
        tool_found = False
        prefered_tool = TOOLS[preferred_tool_version[0]][preferred_tool_version[1]](tempdir)

        if prefered_tool.detect() == True:
            # Preferred tool version is available.
            tool_found = True
            toolchain[preferred_tool_version[0]] = prefered_tool
            module_logger.info(f"    {preferred_tool_version[0]}-{preferred_tool_version[1]} found.")
        else:
            # Check if non-prefered (older, but compatible) version is available.
            module_logger.warning(f"    {preferred_tool_version[0]}-{preferred_tool_version[1]} not found.")

            if len(SORTED_TOOLS[preferred_tool_version[0]]) > 1:
                module_logger.warning(f"        Checking for alternative versions...")
                alternative_versions = SORTED_TOOLS[preferred_tool_version[0]][1:]

                for alternative_version in alternative_versions:
                    alternative_tool = TOOLS[preferred_tool_version[0]][alternative_version](tempdir)

                    if alternative_tool.detect() == True:
                        # Found a compatible version to use.
                        tool_found = True
                        toolchain[preferred_tool_version[0]] = alternative_tool
                        # Select the version so it will be the default.
                        SORTED_TOOLS, _ = get_item_version(f"{preferred_tool_version[0]}={alternative_version}",
                                                           SORTED_TOOLS)
                        module_logger.info(f"    Alternative version {preferred_tool_version[0]}-{alternative_version} found.")
                    else:
                        module_logger.warning(f"    Alternative version {preferred_tool_version[0]}-{alternative_version} not found.")

            if tool_found == False:
                # Tool is missing.  Build will fail.
                missing_tools.append(preferred_tool_version)

    if len(missing_tools) > 0:
        module_logger.warning("")
        module_logger.warning("The following tools are missing and must be installed for this build to continue:")
        for tool_version in missing_tools:
            module_logger.warning(f"    {tool_version[0]}-{tool_version[1]}")
            # TODO: Provide an option to install the missing tools automatically.

        sys.exit(1)

    module_logger.info("")
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
                module_logger.info(f"   {idx:2} [{i}:{j:2}]: {recipe}-{SORTED_RECIPES[recipe][0]}")
                module_logger.debug(f"      Tool(s):")
                for tool in RECIPES[recipe][SORTED_RECIPES[recipe][0]].required_tools:
                    _, tool_version = get_item_version(tool, SORTED_TOOLS)
                    module_logger.debug(f"        {tool_version[0]}-{tool_version[1]}")
                continue

            if failure:
                module_logger.warning(f"Skipping {recipe} build due to prior failure.")
            else:
                result = build_recipe(recipe,
                                      SORTED_RECIPES[recipe][0],
                                      tempdir,
                                      toolchain)
                results.append(result)
                if result['success'] == False:
                    failure = True

    if not dryrun:
        print_results(results)

    if failure == True:
        sys.exit(1)

    sys.exit(0)

@cli.command()
def ls():
    '''
    Print the list of all known recipes.
    An asterisk indicates default (highest) version.
    '''
    module_logger.info("Recipes:")
    for recipe in SORTED_RECIPES:
        outline = f"    {recipe:10} ["
        for i,version in enumerate(SORTED_RECIPES[recipe]):
            if i == 0:
                outline += f" {version}*"
            else:
                outline += f", {version}"
        outline += " ]"
        module_logger.info(outline)

if __name__ == '__main__':
    cli(sys.argv[1:])
