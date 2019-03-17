r'''
  __    __     __  __     ______     ______     ______     __         ______    
 /\ "-./  \   /\ \/\ \   /\  ___\   /\  ___\   /\  ___\   /\ \       /\  ___\   
 \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \___  \  \ \  __\   \ \ \____  \ \___  \  
  \ \_\ \ \_\  \ \_____\  \/\_____\  \/\_____\  \ \_____\  \ \_____\  \/\_____\ 
   \/_/  \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/ 

A tool to download, build, and assemble application dependencies.
                                    Brought to you by the Clam AntiVirus Team.

Copyright (C)2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.
'''

'''
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
import logging
import os
import pkgutil
import sys

import click

logging.basicConfig()
module_logger = logging.getLogger('mussels')
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
    for idx,version in enumerate(versions_list):
        SORTED_RECIPES[recipe].append(version)

def build_recipe(recipe: str, version: str, tempdir: str):
    '''
    Build a specific recipe.
    '''
    module_logger.info(f"Attempting to build {recipe}...")

    if version == "":
        # Use the default (highest) version
        version = SORTED_RECIPES[recipe][0]

    try:
        builder = RECIPES[recipe][version](tempdir)
    except KeyError:
        module_logger.error(f" !! Failed to find recipe for: {recipe} @ {version}")
        return None

    if builder.build() == False:
        module_logger.error(f" !! {recipe} build Failed !!\n")
    else:
        module_logger.info(f" :) {recipe} build Succeeded (:\n")
        builder.install()

    return builder

def print_results(results: list):
    '''
    Print the build results in a pretty way.
    '''
    pass

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
              type=click.Choice(list(RECIPES.keys())),
              help='Recipe to build.')
@click.option('--version', '-v', default="",
              help='Version of recipe to build. [optional]')
@click.option('--tempdir', '-t', default="",
              help='Build in a specific directory instead of a temp directory. [optional]')
def build(recipe: str, version: str, tempdir: str):
    '''
    Download, extract, build, and install the recipe.
    '''
    if tempdir == "":
        # Create a temporary directory to work in.
        tempdir = os.path.join(os.getcwd(), "clamdeps_" + str(datetime.datetime.now()).replace(' ', '_').replace(':', '-'))
        os.mkdir(tempdir)
    else:
        # Use the current working directory.
        tempdir = os.path.join(os.getcwd(), tempdir)

    if recipe == "all":
        results = [build_recipe(key, version, tempdir) for key in RECIPES.keys()]
    else:
        results = [build_recipe(recipe, version, tempdir),]

    print_results(results)

@cli.command()
def ls():
    '''
    Print the list of all known recipes.
    An asterisk indicates default (highest) version.
    '''
    print("Recipes:")
    for recipe in SORTED_RECIPES:
        outline = f"\t{recipe} ["
        for i,version in enumerate(SORTED_RECIPES[recipe]):
            if i == 0:
                outline += f" {version}*"
            else:
                outline += f", {version}"
        outline += " ]"
        print(outline)

if __name__ == '__main__':
    cli(sys.argv[1:])
