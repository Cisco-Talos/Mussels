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
import shutil
import sys
import time

import click
import coloredlogs

logging.basicConfig()
module_logger = logging.getLogger('mussels')
coloredlogs.install(level='DEBUG')
module_logger.setLevel(logging.DEBUG)

RECIPES = defaultdict(dict)
SORTED_RECIPES = defaultdict(list)

# Collect all Recipes in recipes directory.
__all__ = []
recipe_path = os.path.join(os.path.split(__file__)[0], "recipes")
for loader, module_name, is_pkg in pkgutil.walk_packages([recipe_path]):
    __all__.append(module_name)
    _module = loader.find_module(module_name).load_module(module_name)
    globals()[module_name] = _module
    if "Recipe" in dir(_module):
        RECIPES[_module.Recipe.name][_module.Recipe.version] = _module.Recipe

# Sort the recipes, and determine the highest versions.
for recipe in RECIPES:
    versions_list = list(RECIPES[recipe].keys())
    versions_list.sort(key=lambda s: [str(u) for u in s.split('.')])
    versions_list.reverse()
    for idx,version in enumerate(versions_list):
        SORTED_RECIPES[recipe].append(version)

def build_recipe(recipe: str, version: str, tempdir: str) -> dict:
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
        builder = RECIPES[recipe][version](tempdir)
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
    versions_list.sort(key=lambda s: [str(u) for u in s.split('.')])

    if versions_list[0] == version_a:
        return -1
    else:
        return 1

def get_recipe_version(recipe: str) -> tuple:
    '''
    Convert a recipe name in the format to a (recipe, version) tuple:

        recipe[ >=, <=, >, <, (==|=|@) version ]

    Examples:
        - meepioux
        - blarghus>=1.2.3
        - wheeple@0.2.0
        - pyplo==5.1.0g

    The highest available version will be selected if one is not specified.
    Version requirements will whittle down the list of available versions
    in the global SORTED_RECIPES list.

    If a specific version is specified, all other versions will be disqualified.

    If no versions remain that satisfy build qualifications, an exception will be raised.

    :return: tuple of the recipe (name,version) with the highest qualified version.
    '''
    if ">=" in recipe:
        # GTE requirement found.
        name, version = recipe.split(">=")
        for i,ver in enumerate(SORTED_RECIPES[name]):
            cmp = compare_versions(ver, version)
            if (cmp < 0):
                # Version is too low. Remove it, and subsequent versions.
                SORTED_RECIPES[name] = SORTED_RECIPES[name][:i]
                break

    elif ">" in recipe:
        # GT requirement found.
        name, version = recipe.split(">")
        for i,ver in enumerate(SORTED_RECIPES[name]):
            cmp = compare_versions(ver, version)
            if (cmp <= 0):
                # Version is too low. Remove it, and subsequent versions.
                SORTED_RECIPES[name] = SORTED_RECIPES[name][:i]
                break

    elif "<=" in recipe:
        # LTE requirement found.
        name, version = recipe.split("<=")
        try:
            first = SORTED_RECIPES[name][0]
        except:
            raise Exception(f"No versions available to satisfy requirement for {recipe}")
        while compare_versions(first, version) > 0:
            # Remove a version from the SORTED_RECIPES.
            SORTED_RECIPES[name].remove(first)

            try:
                first = SORTED_RECIPES[name][0]
            except:
                raise Exception(f"No versions available to satisfy requirement for {recipe}")

    elif "<" in recipe:
        # LT requirement found.
        name, version = recipe.split("<")
        try:
            first = SORTED_RECIPES[name][0]
        except:
            raise Exception(f"No versions available to satisfy requirement for {recipe}")
        while compare_versions(first, version) >= 0:
            # Remove a version from the SORTED_RECIPES.
            SORTED_RECIPES[name].remove(first)

            try:
                first = SORTED_RECIPES[name][0]
            except:
                raise Exception(f"No versions available to satisfy requirement for {recipe}")
    else:
        eq_cond = False
        if ("==" in recipe):
            name, version = recipe.split("==")
            eq_cond = True
        elif ("=" in recipe):
            name, version = recipe.split("=")
            eq_cond = True
        elif ("@" in recipe):
            name, version = recipe.split("@")
            eq_cond = True

        if eq_cond == True:
            # EQ requirement found.
            # Try to find the specific version, and remove all others.
            if not version in  SORTED_RECIPES[name]:
                raise Exception(f"No versions available to satisfy requirement for {recipe}")
            SORTED_RECIPES[name] = [version]

        else:
            # No version requirement found.
            name = recipe

    try:
        selected_version = SORTED_RECIPES[name][0]
    except:
        raise Exception(f"No versions available to satisfy requirement for {recipe}")

    return (name, selected_version)

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
    all_recipes = get_all_recipes_from_list(recipes)

    # Build a map of recipes (name,version) tuples to sets of dependency (name,version) tuples
    name_to_deps = {}
    for recipe in all_recipes:
        name, version = get_recipe_version(recipe)
        dependencies = RECIPES[name][version].dependencies
        name_to_deps[name] = set([get_recipe_version(recipe)[0] for recipe in dependencies])

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
@click.option('--tempdir', '-t', default="",
              help='Build in a specific directory instead of a temp directory. [optional]')
@click.option('--dryrun', '-d', is_flag=True,
              help='Print out the version dependency graph without actually doing a build. [optional]')
def build(recipe: str, version: str, tempdir: str, dryrun: bool):
    '''
    Download, extract, build, and install the recipe.
    '''
    if not dryrun:
        # Only need a temp directory for a real build.
        if tempdir == "":
            # Create a temporary directory to work in.
            tempdir = os.path.abspath("out")
        else:
            # Use the directory provided by the caller.
            tempdir = os.path.abspath(os.path.join(tempdir))

    os.makedirs(tempdir, exist_ok=True)

    batches = []
    results = []

    if recipe == "all":
        batches = get_build_batches(RECIPES.keys())
    else:
        if version == "":
            batches = get_build_batches([recipe])
        else:
            batches = get_build_batches([f"{recipe}=={version}"])

    if dryrun:
        module_logger.info("Dry-run: Build-order of requested recipes:")

    idx = 0
    failure = False
    for i, bundle in enumerate(batches):
        for j, recipe in enumerate(bundle):
            idx += 1

            if dryrun:
                module_logger.info(f"   {idx:2} [{i}:{j:2}]: {recipe}-{SORTED_RECIPES[recipe][0]}")
                continue

            if failure:
                module_logger.warning(f"Skipping {recipe} build due to prior failure.")
            else:
                result = build_recipe(recipe, SORTED_RECIPES[recipe][0], tempdir)
                results.append(result)
                if result['success'] == False:
                    failure = True

    if not dryrun:
        print_results(results)

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
