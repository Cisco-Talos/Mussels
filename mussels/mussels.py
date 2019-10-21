"""
Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

This module provides the core Mussels class, used by the CLI interface defined in __main__.py

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
from pathlib import Path

import datetime
import fnmatch
import json
import logging
import os
import platform
import shutil
import sys
import time
from typing import *

if platform.system() == "Windows":
    if not r"c:\program files\git\cmd" in os.environ["PATH"].lower():
        os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files\Git\cmd"
    if not r"c:\program files\git\mingw64\bin" in os.environ["PATH"].lower():
        os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files\Git\mingw64\bin"
    if not r"c:\program files\git\usr\bin" in os.environ["PATH"].lower():
        os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files\Git\usr\bin"
    if not r"c:\program files\git\bin" in os.environ["PATH"].lower():
        os.environ["PATH"] = os.environ["PATH"] + r";C:\Program Files\Git\bin"
import git
import yaml

import mussels.bookshelf
import mussels.recipe
import mussels.tool
from mussels.utils.versions import (
    NVC,
    nvc_str,
    sort_cookbook_by_version,
    version_keys,
    get_item_version,
    platform_is,
    platform_matches,
    pick_platform,
)


class Mussels:
    config: dict = {}
    cookbooks: defaultdict = defaultdict(dict)

    recipes: defaultdict = defaultdict(dict)
    sorted_recipes: dict = {}

    tools: defaultdict = defaultdict(dict)
    sorted_tools: dict = {}

    def __init__(
        self,
        load_all_recipes: bool = False,
        data_dir: str = os.path.join(str(Path.home()), ".mussels"),
        log_file: str = os.path.join(
            str(Path.home()), ".mussels", "logs", "mussels.log"
        ),
        log_level: str = "DEBUG",
    ) -> None:
        """
        Mussels class.

        Args:
            data_dir:   path where ClamAV should be installed.
            log_file:   path output log.
            log_level:  log level ("DEBUG", "INFO", "WARNING", "ERROR").
        """
        self.log_file = log_file
        self._init_logging(log_level)

        self.app_data_dir = data_dir

        self._load_config("cookbooks.json", self.cookbooks)
        self._load_recipes(all=load_all_recipes)

    def _init_logging(self, level="DEBUG"):
        """
        Initializes the logging parameters

        Returns:    nothing
        """
        levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARN": logging.WARNING,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
        }

        self.logger = logging.getLogger("Mussels")
        self.logger.setLevel(levels[level])

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s:  %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

        if not os.path.exists(os.path.split(self.log_file)[0]):
            os.makedirs(os.path.split(self.log_file)[0])
        self.filehandler = logging.FileHandler(filename=self.log_file)
        self.filehandler.setLevel(levels[level])
        self.filehandler.setFormatter(formatter)

        self.logger.addHandler(self.filehandler)

    def _load_config(self, filename, config) -> bool:
        """
        Load the cache.
        """
        # load config, if exists.
        try:
            with open(
                os.path.join(self.app_data_dir, "config", filename), "r"
            ) as config_file:
                config.update(json.load(config_file))
        except Exception:
            # No existing config to load, that's probaby ok, but return false to indicate the failure.
            return False

        return True

    def _store_config(self, filename, config) -> bool:
        """
        Update the cache.
        """
        try:
            if not os.path.isdir(os.path.join(self.app_data_dir, "config")):
                os.makedirs(os.path.join(self.app_data_dir, "config"))
        except Exception as exc:
            self.logger.warning(f"Failed to create config directory.  Exception: {exc}")
            return False

        try:
            with open(
                os.path.join(self.app_data_dir, "config", filename), "w"
            ) as config_file:
                json.dump(config, config_file, indent=4)
        except Exception as exc:
            self.logger.warning(f"Failed to update config.  Exception: {exc}")
            return False

        return True

    def load_directory(self, cookbook: str, load_path: str) -> tuple:
        """
        Load all recipes and tools in a directory.
        This function reads in YAML files and assigns each to a new Recipe or Tool class, accordingly.
        The classes are returned in a tuple.
        """
        minimum_version = "0.1"
        recipes = defaultdict(dict)
        tools = defaultdict(dict)

        if not os.path.exists(load_path):
            return recipes, tools

        for root, dirs, filenames in os.walk(load_path):
            for fname in filenames:
                if not fname.endswith(".yaml"):
                    continue
                fpath = os.path.abspath(os.path.join(root, fname))
                with open(fpath, "r") as fd:
                    try:
                        yaml_file = yaml.load(fd.read(), Loader=yaml.SafeLoader)
                    except Exception as exc:
                        self.logger.warning(f"Failed to load YAML file: {fpath}")
                        self.logger.warning(f"Exception occured: \n{exc}")
                        continue
                    if yaml_file == None:
                        continue

                    if (
                        "mussels_version" in yaml_file
                        and yaml_file["mussels_version"] >= minimum_version
                    ):
                        if not "type" in yaml_file:
                            self.logger.warning(f"Failed to load recipe: {fpath}")
                            self.logger.warning(f"Missing required 'type' field.")
                            continue

                        if (
                            yaml_file["type"] == "recipe"
                            or yaml_file["type"] == "collection"
                        ):
                            if not "name" in yaml_file:
                                self.logger.warning(f"Failed to load recipe: {fpath}")
                                self.logger.warning(f"Missing required 'name' field.")
                                continue
                            name = f"{cookbook}__{yaml_file['name']}"

                            if not "version" in yaml_file:
                                self.logger.warning(f"Failed to load recipe: {fpath}")
                                self.logger.warning(
                                    f"Missing required 'version' field."
                                )
                                continue
                            else:
                                name = f"{name}_{yaml_file['version']}"

                            recipe_class = type(
                                name,
                                (mussels.recipe.BaseRecipe,),
                                {"__doc__": f"{yaml_file['name']} recipe class."},
                            )

                            recipe_class.module_file = fpath

                            recipe_class.name = yaml_file["name"]

                            recipe_class.version = yaml_file["version"]

                            if yaml_file["type"] == "collection":
                                recipe_class.is_collection = True
                            else:
                                recipe_class.is_collection = False

                                if not "url" in yaml_file:
                                    self.logger.warning(
                                        f"Failed to load recipe: {fpath}"
                                    )
                                    self.logger.warning(
                                        f"Missing required 'url' field."
                                    )
                                    continue
                                else:
                                    recipe_class.url = yaml_file["url"]

                            if "archive_name_change" in yaml_file:
                                recipe_class.archive_name_change = (
                                    yaml_file["archive_name_change"][0],
                                    yaml_file["archive_name_change"][1],
                                )

                            if not "platforms" in yaml_file:
                                self.logger.warning(f"Failed to load recipe: {fpath}")
                                self.logger.warning(
                                    f"Missing required 'platforms' field."
                                )
                                continue
                            else:
                                recipe_class.platforms = yaml_file["platforms"]

                            recipes[recipe_class.name][
                                recipe_class.version
                            ] = recipe_class

                        elif yaml_file["type"] == "tool":
                            if not "name" in yaml_file:
                                self.logger.warning(f"Failed to load tool: {fpath}")
                                self.logger.warning(f"Missing required 'name' field.")
                                continue
                            name = f"{cookbook}__{yaml_file['name']}"

                            if "version" in yaml_file:
                                name = f"{name}_{yaml_file['version']}"

                            tool_class = type(
                                name,
                                (mussels.tool.BaseTool,),
                                {"__doc__": f"{yaml_file['name']} tool class."},
                            )

                            tool_class.module_file = fpath

                            tool_class.name = yaml_file["name"]

                            if "version" in yaml_file:
                                tool_class.version = yaml_file["version"]

                            if not "platforms" in yaml_file:
                                self.logger.warning(f"Failed to load tool: {fpath}")
                                self.logger.warning(
                                    f"Missing required 'platforms' field."
                                )
                                continue
                            else:
                                tool_class.platforms = yaml_file["platforms"]

                            tools[tool_class.name][tool_class.version] = tool_class

        return recipes, tools

    def _read_cookbook(self, cookbook: str, cookbook_path: str) -> bool:
        """
        Load the recipes and tools from a single cookbook.
        """

        sorted_recipes: defaultdict = defaultdict(list)
        sorted_tools: defaultdict = defaultdict(list)

        # Load the recipes and the tools
        recipes, tools = self.load_directory(
            cookbook=cookbook, load_path=os.path.join(cookbook_path)
        )

        # Sort the recipes
        sorted_recipes = sort_cookbook_by_version(recipes)

        if len(sorted_recipes) > 0:
            self.cookbooks[cookbook]["recipes"] = sorted_recipes
            for recipe in recipes.keys():
                for version in recipes[recipe]:
                    if version not in self.recipes[recipe].keys():
                        self.recipes[recipe][version] = {}
                    self.recipes[recipe][version][cookbook] = recipes[recipe][version]

        # Sort the tools
        sorted_tools = sort_cookbook_by_version(tools)

        if len(sorted_tools) > 0:
            self.cookbooks[cookbook]["tools"] = sorted_tools
            for tool in tools.keys():
                for version in tools[tool]:
                    if version not in self.tools[tool].keys():
                        self.tools[tool][version] = {}
                    self.tools[tool][version][cookbook] = tools[tool][version]

        if len(recipes) == 0 and len(tools) == 0:
            return False

        if "trusted" not in self.cookbooks[cookbook]:
            self.cookbooks[cookbook]["trusted"] = False

        return True

    def _read_bookshelf(self) -> bool:
        """
        Load the recipes and tools from cookbooks in ~/.mussels/cookbooks
        """
        bookshelf = os.path.join(self.app_data_dir, "cookbooks")
        if os.path.isdir(bookshelf):
            for cookbook in os.listdir(bookshelf):
                cookbook_path = os.path.join(
                    os.path.join(self.app_data_dir, "cookbooks"), cookbook
                )
                if os.path.isdir(cookbook_path):
                    if not self._read_cookbook(cookbook, cookbook_path):
                        self.logger.warning(
                            f"Failed to read any recipes or tools from cookbook: {cookbook}"
                        )

            self._store_config("cookbooks.json", self.cookbooks)

        return True

    def _read_local_recipes(self) -> bool:
        """
        Load the recipes and tools from local "mussels" directory
        """
        # Load recipes and tools from `cwd` directory, if any exist.
        local_recipes = os.path.join(os.getcwd())
        if os.path.isdir(local_recipes):
            if not self._read_cookbook("local", local_recipes):
                return False

            self.cookbooks["local"]["url"] = ""
            self.cookbooks["local"]["path"] = local_recipes
            self.cookbooks["local"]["trusted"] = True

        return True

    def _sort_items_by_version(
        self, items: defaultdict, all: bool, has_target: bool = False
    ) -> dict:
        """
        Sort recipes, and determine the highest versions.
        Only includes trusted recipes for current platform.
        """
        sorted_items: dict = {}

        for item in items:
            versions_list = list(items[item].keys())
            versions_list.sort(key=version_keys)
            versions_list.reverse()

            sorted_item_list = []

            for version in versions_list:
                found_good_version = False
                item_version = {"version": version, "cookbooks": {}}

                for each_cookbook in items[item][version].keys():
                    if not all and not self.cookbooks[each_cookbook]["trusted"]:
                        continue

                    cookbook: dict = {}

                    for each_platform in items[item][version][each_cookbook].platforms:
                        if not all and not platform_is(each_platform):
                            continue

                        if has_target:
                            cookbook[each_platform] = [
                                target
                                for target in items[item][version][each_cookbook]
                                .platforms[each_platform]
                                .keys()
                            ]
                        else:
                            cookbook[each_platform] = []

                        found_good_version = True

                    item_version["cookbooks"][each_cookbook] = cookbook

                if found_good_version:
                    sorted_item_list.append(item_version)

            if len(sorted_item_list) > 0:
                sorted_items[item] = sorted_item_list

        return sorted_items

    def _load_recipes(self, all: bool = False) -> bool:
        """
        Load the recipes and tools.
        """
        # If the cache is empty, try reading from the local bookshelf.
        if len(self.recipes) == 0 or len(self.tools) == 0:
            self._read_bookshelf()

        # Load recipes from the local mussels directory, if those exists.
        if not self._read_local_recipes() and "local" in self.cookbooks:
            self.cookbooks.pop("local")

        if len(self.recipes) == 0:
            return False

        self.sorted_recipes = self._sort_items_by_version(
            self.recipes, all=all, has_target=True
        )
        self.sorted_tools = self._sort_items_by_version(self.tools, all=all)

        if len(self.sorted_recipes) == 0 or len(self.sorted_tools) == 0:
            return False

        return True

    def _build_recipe(
        self,
        recipe: str,
        version: str,
        cookbook: str,
        platform: str,
        target: str,
        toolchain: dict,
        clean: bool = False,
    ) -> dict:
        """
        Build a specific recipe.

        Args:
            recipe:     The recipe name with no version information.
            version:    The recipe version.

        Returns:    A dictionary of build results
        """
        result = {"name": recipe, "version": version, "success": False}

        if not self.cookbooks[cookbook]["trusted"]:
            self.logger.error(
                f"Unable to build {recipe}={version} from '{cookbook}'. You have not elected to trust '{cookbook}'"
            )
            self.logger.error(
                f"Building recipes involve downloading and executing code from the internet, which carries some risk."
            )
            self.logger.error(
                f"Please review the recipes provided by '{cookbook}' at: {self.cookbooks[cookbook]['url']}."
            )
            self.logger.error(
                f"If you're comfortable with the level of risk, run the following command to trust all recipes from '{cookbook}':"
            )
            self.logger.error(f"")
            self.logger.error(f"    mussels cookbook trust {cookbook}")
            self.logger.error(f"")
            self.logger.error(
                f"Alternatively, you may consider cloning only the recipe you need for your own cookbook."
            )
            self.logger.error(
                f"This is a safer option, though you are still encouraged to review the recipe before using it."
            )
            self.logger.error(
                f"To clone the recipe {recipe}={version} from '{cookbook}', run the following command:"
            )
            self.logger.error(f"")
            self.logger.error(
                f"    mussels recipe clone {recipe} -v {version} -c {cookbook}"
            )
            return result

        start = time.time()

        self.logger.info(f"Attempting to build {recipe}...")

        if version == "":
            # Use the default (highest) version
            try:
                version = self.sorted_recipes[recipe][0]
            except KeyError:
                self.logger.error(f"FAILED to find recipe: {recipe}!")
                result["time elapsed"] = time.time() - start
                return result

        try:
            recipe_class = self.recipes[recipe][version][cookbook]
        except KeyError:
            self.logger.error(f"FAILED to find recipe: {nvc_str(recipe, version)}!")
            result["time elapsed"] = time.time() - start
            return result

        recipe_object = recipe_class(
            toolchain=toolchain,
            platform=platform,
            target=target,
            data_dir=self.app_data_dir,
        )

        if not recipe_object._build(clean):
            self.logger.error(f"FAILURE: {nvc_str(recipe, version)} build failed!\n")
        else:
            self.logger.info(
                f"Success: {nvc_str(recipe, version)} build succeeded. :)\n"
            )
            result["success"] = True

        result["time elapsed"] = time.time() - start

        return result

    def _get_recipe_version(self, recipe: str, platform: str, target: str) -> NVC:
        """
        Select recipe version based on version requirements.
        Eliminate recipe versions and sorted tools versions based on
        these requirements, and the required_tools requirements of remaining recipes.

        Args:
            recipe:     A specific recipe string, which may include version information.
            cookbook:   The preferred cookbook to select the recipe from.

        :return: named tuple describing the highest qualified version:
            NVC(
                "name"->str,
                "version"->str,
                "cookbook"->str,
            )
        """
        # Select the recipe
        nvc = get_item_version(recipe, self.sorted_recipes, target)

        # Use "get_item_version()" to prune the list of sorted_tools based on the required tools for the selected recipe.
        for name in self.sorted_recipes:
            for i, each_ver in enumerate(self.sorted_recipes[name]):
                version = each_ver["version"]
                for cookbook in each_ver["cookbooks"].keys():
                    recipe_class = self.recipes[name][version][cookbook]

                    for each_platform in recipe_class.platforms:
                        if platform_matches(each_platform, platform):
                            variant = recipe_class.platforms[each_platform]
                            if target in variant.keys():
                                build_target = variant[target]

                                if "required_tools" in build_target.keys():
                                    for tool in build_target["required_tools"]:
                                        try:
                                            get_item_version(tool, self.sorted_tools)
                                        except Exception:
                                            raise Exception(
                                                f'No tool definition "{tool}" found. Required by {nvc_str(name, version, cookbook)}.'
                                            )
                                break
        return nvc

    def _identify_build_recipes(
        self, recipe: str, chain: list, platform: str, target: str
    ) -> list:
        """
        Identify all recipes that must be built given a specific recipe.

        Args:
            recipe:     A specific recipe to build.
            chain:      (in,out) A dependency chain starting from the first
                        recursive call used to identify circular dependencies.
        """
        recipe_nvc = self._get_recipe_version(recipe, platform, target)

        if (len(chain) > 0) and (recipe_nvc.name == chain[0]):
            raise ValueError(f"Circular dependencies found! {chain}")
        chain.append(recipe_nvc.name)

        recipes = []

        recipes.append(recipe)

        # Verify that recipe supports current platform.
        platform_options = self.recipes[recipe_nvc.name][recipe_nvc.version][
            recipe_nvc.cookbook
        ].platforms.keys()
        matching_platform = pick_platform(platform, platform_options)
        if matching_platform == "":
            # recipe doesn't support current platform.
            # TODO: see if next recipe does.
            pass

        # verify that recipe supports requested target architecture

        if (
            "dependencies"
            in self.recipes[recipe_nvc.name][recipe_nvc.version][
                recipe_nvc.cookbook
            ].platforms[matching_platform][target]
        ):
            dependencies = self.recipes[recipe_nvc.name][recipe_nvc.version][
                recipe_nvc.cookbook
            ].platforms[matching_platform][target]["dependencies"]
            for dependency in dependencies:
                if ":" not in dependency:
                    # If the cookbook isn't explicitly specified for the dependency,
                    # select the recipe from the current cookbook.
                    dependency = f"{recipe_nvc.cookbook}:{dependency}"

                recipes += self._identify_build_recipes(
                    dependency, chain, platform, target
                )

        return recipes

    def _get_build_batches(self, recipe: str, platform: str, target: str) -> list:
        """
        Get list of build batches that can be built concurrently.

        Args:
            recipe:    A recipes string in the format [cookbook:]recipe[==version].
        """
        # Identify all recipes that must be built given list of desired builds.
        all_recipes = set(self._identify_build_recipes(recipe, [], platform, target))

        # Build a map of recipes (name,version) tuples to sets of dependency (name,version,cookbook) tuples
        nvc_to_deps = {}
        for recipe in all_recipes:
            recipe_nvc = self._get_recipe_version(recipe, platform, target)
            platform_options = self.recipes[recipe_nvc.name][recipe_nvc.version][
                recipe_nvc.cookbook
            ].platforms.keys()
            matching_platform = pick_platform(platform, platform_options)

            if (
                "dependencies"
                in self.recipes[recipe_nvc.name][recipe_nvc.version][
                    recipe_nvc.cookbook
                ].platforms[matching_platform][target]
            ):
                dependencies = self.recipes[recipe_nvc.name][recipe_nvc.version][
                    recipe_nvc.cookbook
                ].platforms[matching_platform][target]["dependencies"]
            else:
                dependencies = []
            nvc_to_deps[recipe_nvc] = set(
                [
                    self._get_recipe_version(dependency, platform, target)
                    for dependency in dependencies
                ]
            )

        batches = []

        # While there are dependencies to solve...
        while nvc_to_deps:

            # Get all recipes with no dependencies
            ready = {recipe for recipe, deps in nvc_to_deps.items() if not deps}

            # If there aren't any, we have a loop in the graph
            if not ready:
                msg = "Circular dependencies found!\n"
                msg += json.dumps(nvc_to_deps, indent=4)
                raise ValueError(msg)

            # Remove them from the dependency graph
            for recipe in ready:
                del nvc_to_deps[recipe]
            for deps in nvc_to_deps.values():
                deps.difference_update(ready)

            # Add the batch to the list
            batches.append(ready)

        # Return the list of batches
        return batches

    def _select_cookbook(
        self, recipe: str, recipe_version: dict, preferred_book: str = ""
    ) -> str:
        """
        Return the cookbook name, if only one cookbook provides the recipe-version.
        If more then one cookbook provides the recipe-version, explain the options and return an empty string.
        """
        cookbook = ""

        num_cookbooks = len(recipe_version["cookbooks"].keys())
        if num_cookbooks == 0:
            self.logger.error(
                f"Recipe {nvc_str(recipe, recipe_version['version'])} not provided by any cookbook!(?!)"
            )

        elif num_cookbooks == 1:
            cookbook = next(iter(recipe_version["cookbooks"]))

        else:
            if "local" in recipe_version["cookbooks"]:
                # Always prefer to use a local recipe.
                cookbook = "local"
            elif preferred_book != "" and preferred_book in recipe_version["cookbooks"]:
                # 2nd choice is the "preferred" cookbook, which was probably the same cookbook as the target recipe.
                cookbook = preferred_book
            else:
                # More than one option exists, but no good excuse to choose one over another.
                # Bail out and ask for more specific instructions.
                self.logger.error(
                    f'Failed to select a cookbook for {nvc_str(recipe, recipe_version["version"])}'
                )
                self.logger.error(
                    f"No cookbook specified, no local recipe exists, and no recipe exists in the same cookbook as the primary build target recipe."
                )
                self.logger.error(
                    f"However, multiple cookbooks do provide the recipe. Please retry with a specific cookbook using the `-c` / `--cookbook` options"
                )
                self.logger.info(f"")

                self.print_recipe_details(
                    recipe, recipe_version, verbose=True, all=True
                )

        return cookbook

    def check_tool(
        self,
        tool: str,
        version: str,
        cookbook: str,
        results: list,
    ) -> bool:
        """
        Check if a tool exists. Will check all tools if tool arg is "".

        Args:
            recipe:     The recipe to build.
            version:    A specific version to build.  Leave empty ("") to build the newest.
            cookbook:   A specific cookbook to use.  Leave empty ("") if there's probably only one.
            results:    (out) A list of dictionaries describing the results of the build.
        """
        found_tool = False

        for each_tool in self.sorted_tools:
            if tool == "" or tool == each_tool:
                for each_version in self.sorted_tools[each_tool]:
                    if version == "" or version == each_version["version"]:
                        for each_cookbook in each_version["cookbooks"]:
                            if cookbook == "" or cookbook == each_cookbook:
                                found_tool = True

                                tool_object = self.tools[each_tool][each_version["version"]][each_cookbook](self.app_data_dir)

                                if tool_object.detect():
                                    # Found!
                                    self.logger.warning(
                                        f"    {nvc_str(each_tool, each_version['version'], each_cookbook)} FOUND."
                                    )
                                else:
                                    # Not found.
                                    self.logger.error(
                                        f"    {nvc_str(each_tool, each_version['version'], each_cookbook)} NOT found."
                                    )
        if not found_tool:
            self.logger.warning(
                f"    Unable to find tool definition matching: {nvc_str(tool, version, cookbook)}."
            )

    def build_recipe(
        self,
        recipe: str,
        version: str,
        cookbook: str,
        target: str,
        results: list,
        dry_run: bool = False,
        clean: bool = False,
    ) -> bool:
        """
        Execute a build of a recipe.

        Args:
            recipe:     The recipe to build.
            version:    A specific version to build.  Leave empty ("") to build the newest.
            cookbook:   A specific cookbook to use.  Leave empty ("") if there's probably only one.
            target:     The target architecture to build.
            results:    (out) A list of dictionaries describing the results of the build.
            dry_run:    (optional) Don't actually build, just print the build chain.
        """

        def print_results(results: list):
            """
            Print the build results in a pretty way.

            Args:
                results:    (out) A list of dictionaries describing the results of the build.
            """
            for result in results:
                if result["success"]:
                    self.logger.info(
                        f"Successful build of {nvc_str(result['name'], result['version'])} completed in {datetime.timedelta(0, result['time elapsed'])}."
                    )
                else:
                    self.logger.error(
                        f"Failure building {nvc_str(result['name'], result['version'])}, terminated after {datetime.timedelta(0, result['time elapsed'])}"
                    )

        if not recipe in self.sorted_recipes:
            self.logger.error(f"The recipe does not exist, or at least does not exist for the current platform ({platform.system()}")
            self.logger.error(f"To available recipes for your platform, run:   msl list")
            self.logger.error(f"To all recipes for all platforms, run:         msl list -a")
            self.logger.error(f"To download the latest recipes, run:           msl update")
            return False


        batches: List[dict] = []

        recipe_str = nvc_str(recipe, version, cookbook)

        if target == "":
            if platform.system() == "Windows":
                target = (
                    "x64" if os.environ["PROCESSOR_ARCHITECTURE"] == "AMD64" else "x86"
                )
            else:
                target = "host"

        batches = self._get_build_batches(
            recipe_str, platform=platform.system(), target=target
        )

        #
        # Validate toolchain
        #
        # Collect set of required tools for entire build.
        toolchain = {}
        preferred_tool_versions = set()
        for i, bundle in enumerate(batches):
            for j, recipe_nvc in enumerate(bundle):
                recipe_class = self.recipes[recipe_nvc.name][recipe_nvc.version][
                    recipe_nvc.cookbook
                ]

                for each_platform in recipe_class.platforms:
                    if platform_is(each_platform):
                        if (
                            "required_tools"
                            in recipe_class.platforms[each_platform][target].keys()
                        ):
                            for tool in recipe_class.platforms[each_platform][target][
                                "required_tools"
                            ]:
                                tool_nvc = get_item_version(tool, self.sorted_tools)
                                preferred_tool_versions.add(tool_nvc)

        # Check if required tools are installed
        missing_tools = []
        for tool_nvc in preferred_tool_versions:
            tool_found = False
            preferred_tool = self.tools[tool_nvc.name][tool_nvc.version][
                tool_nvc.cookbook
            ](self.app_data_dir)

            if preferred_tool.detect():
                # Preferred tool version is available.
                tool_found = True
                toolchain[tool_nvc.name] = preferred_tool
                self.logger.info(
                    f"    {nvc_str(tool_nvc.name, tool_nvc.version, tool_nvc.cookbook)} found."
                )
            else:
                # Check if non-preferred (older, but compatible) version is available.
                self.logger.warning(
                    f"    {nvc_str(tool_nvc.name, tool_nvc.version, tool_nvc.cookbook)} not found."
                )

                if len(self.sorted_tools[tool_nvc.name]) > 1:
                    self.logger.warning(f"        Checking for alt versions...")
                    alt_versions = self.sorted_tools[tool_nvc.name][1:]

                    for alt_version in alt_versions:
                        alt_version_cookbook = self._select_cookbook(
                            tool_nvc.name, alt_version, cookbook
                        )
                        alt_tool = self.tools[tool_nvc.name][alt_version["version"]][
                            alt_version_cookbook
                        ](self.app_data_dir)

                        if alt_tool.detect():
                            # Found a compatible version to use.
                            tool_found = True
                            toolchain[tool_nvc.name] = alt_tool

                            # Select the exact version (pruning all other options) so it will be the default.
                            get_item_version(
                                f"{nvc_str(tool_nvc.name, alt_version['version'], alt_version_cookbook)}",
                                self.sorted_tools,
                            )
                            self.logger.info(
                                f"    Alternative version {nvc_str(tool_nvc.name, alt_version['version'], alt_version_cookbook)} found."
                            )
                        else:
                            self.logger.warning(
                                f"    Alternative version {nvc_str(tool_nvc.name, alt_version['version'], alt_version_cookbook)} not found."
                            )

                if not tool_found:
                    # Tool is missing.  Build will fail.
                    missing_tools.append(tool_nvc)

        if len(missing_tools) > 0:
            self.logger.warning("")
            self.logger.warning(
                "The following tools are missing and must be installed for this build to continue:"
            )
            for tool_version in missing_tools:
                self.logger.warning(f"    {nvc_str(tool_version.name, tool_version.version)}")

            sys.exit(1)

        self.logger.info("Toolchain:")
        for tool in toolchain:
            self.logger.info(f"   {nvc_str(tool, toolchain[tool].version)}")

        #
        # Perform Build
        #
        if dry_run:
            self.logger.warning("")
            self.logger.warning(r"    ___   ___   _         ___   _     _    ")
            self.logger.warning(r"   | | \ | |_) \ \_/     | |_) | | | | |\ |")
            self.logger.warning(r"   |_|_/ |_| \  |_|      |_| \ \_\_/ |_| \|")
            self.logger.warning("")
            self.logger.info("Build-order of requested recipes:")

        idx = 0
        failure = False
        for i, bundle in enumerate(batches):
            for j, recipe_nvc in enumerate(bundle):
                idx += 1

                platform_options = self.recipes[recipe_nvc.name][recipe_nvc.version][
                    recipe_nvc.cookbook
                ].platforms.keys()
                matching_platform = pick_platform(platform.system(), platform_options)

                if dry_run:
                    self.logger.info(
                        f"   {idx:2} [{i}:{j:2}]: {nvc_str(recipe_nvc.name, recipe_nvc.version, recipe_nvc.cookbook)}"
                    )
                    if (
                        "required_tools"
                        in self.recipes[recipe_nvc.name][recipe_nvc.version][
                            recipe_nvc.cookbook
                        ].platforms[matching_platform][target]
                    ):
                        self.logger.debug(f"      Tool(s):")
                        for tool in self.recipes[recipe_nvc.name][recipe_nvc.version][
                            recipe_nvc.cookbook
                        ].platforms[matching_platform][target]["required_tools"]:
                            tool_nvc = get_item_version(tool, self.sorted_tools)
                            self.logger.debug(
                                f"        {nvc_str(tool_nvc.name, tool_nvc.version, tool_nvc.cookbook)}"
                            )
                        continue

                if failure:
                    self.logger.warning(
                        f"Skipping  {nvc_str(recipe_nvc.name, recipe_nvc.version, recipe_nvc.cookbook)} build due to prior failure."
                    )
                else:
                    result = self._build_recipe(
                        recipe_nvc.name,
                        recipe_nvc.version,
                        recipe_nvc.cookbook,
                        matching_platform,
                        target,
                        toolchain,
                        clean,
                    )
                    results.append(result)
                    if not result["success"]:
                        failure = True

        if not dry_run:
            print_results(results)

        if failure:
            return False
        return True

    def print_recipe_details(
        self, recipe: str, version: dict, verbose: bool, all: bool
    ):
        """
        Print recipe information.
        """
        version_num = version["version"]
        cookbooks = version["cookbooks"].keys()
        self.logger.info(f"    {nvc_str(recipe, version_num)};  provided by cookbook(s): {list(cookbooks)}")

        if verbose:
            self.logger.info("")
            for cookbook in cookbooks:
                self.logger.info(f"      Cookbook: {cookbook}")

                book_recipe = self.recipes[recipe][version_num][cookbook]

                if book_recipe.is_collection:
                    self.logger.info(f"        Collection: Yes")
                else:
                    self.logger.info(f"        Collection: No")

                self.logger.info(f"        Platforms:")
                for each_platform in book_recipe.platforms:
                    if all or platform_is(each_platform):
                        self.logger.info(f"          Host platform: {each_platform}")

                        variant = book_recipe.platforms[each_platform]
                        for arch in variant.keys():
                            self.logger.info(f"            Target architecture: {arch}")
                            self.logger.info(
                                f"              Dependencies:      {', '.join(variant[arch]['dependencies'])}"
                            )
                            self.logger.info(
                                f"              Required tools:    {', '.join(variant[arch]['required_tools'])}"
                            )

                        if not all:
                            break
            self.logger.info("")

    def show_recipe(self, recipe_match: str, version_match: str, verbose: bool = False):
        """
        Search recipes for a specific recipe and print recipe details.
        """

        found = False

        if version_match == "":
            self.logger.info(f'Searching for recipe matching name: "{recipe_match}"...')
        else:
            self.logger.info(
                f'Searching for recipe matching name: "{recipe_match}", version: "{version_match}"...'
            )
        # Attempt to match the recipe name
        for recipe in self.sorted_recipes:
            if fnmatch.fnmatch(recipe, recipe_match):
                if version_match == "":
                    found = True

                    # Show info for every version
                    for version in self.sorted_recipes[recipe]:
                        self.print_recipe_details(recipe, version, verbose, all)
                    break
                else:
                    # Attempt to match the version too
                    for version in self.sorted_recipes[recipe]:
                        if fnmatch.fnmatch(version, version_match):
                            found = True

                            self.print_recipe_details(recipe, version, verbose, all)
                            break
                    if found:
                        break
        if not found:
            if version_match == "":
                self.logger.warning(f'No recipe matching name: "{recipe_match}"')
            else:
                self.logger.warning(
                    f'No recipe matching name: "{recipe_match}", version: "{version_match}"'
                )

    def clone_recipe(self, recipe: str, version: str, cookbook: str, destination: str):
        """
        Search recipes for a specific recipe and copy the file to the CWD.
        """

        def get_cookbook(recipe: str, recipe_version: dict) -> str:
            """
            Return the cookbook name, if only one cookbook provides the recipe-version.
            If more then one cookbook provides the recipe-version, explain the options and return an empty string.
            """
            cookbook = ""

            num_cookbooks = len(recipe_version["cookbooks"].keys())
            if num_cookbooks == 0:
                self.logger.error(
                    f"Recipe {nvc_str(recipe, version)} not provided by any cookbook!(?!)"
                )

            elif num_cookbooks == 1:
                cookbook = next(iter(recipe_version["cookbooks"]))

            else:
                self.logger.error(
                    f'Clone failed: No cookbook specified, and multiple cookbooks provide recipe "{nvc_str(recipe, recipe_version["version"])}"'
                )
                self.logger.error(
                    f"Please retry with a specific cookbook using the `-c` or `--cookbook` option:"
                )
                self.logger.info(f"")

                self.print_recipe_details(
                    recipe, recipe_version, verbose=True, all=True
                )

            return cookbook

        found = False

        self.logger.info(
            f'Attempting to clone recipe: "{nvc_str(recipe, version, cookbook)}"...'
        )

        try:
            recipe_versions = self.sorted_recipes[recipe]
        except KeyError:
            self.logger.error(f'Clone failed: No such recipe "{recipe}"')
            return False

        # Identify highest available version, for future reference.
        highest_recipe_version = recipe_versions[0]

        #
        # Now repeat the above if/else logic to select the exact recipe requested.
        #

        if version == "":
            if cookbook == "":
                # neither version nor cookbook was specified.
                self.logger.info(
                    f"No version or cookbook specified, will select highest available version."
                )
                version = highest_recipe_version["version"]

                cookbook = get_cookbook(recipe, highest_recipe_version)

                if cookbook == "":
                    return False

            else:
                # cookbook specified, but version wasn't.
                self.logger.info(
                    f'No version specified, will select highest version provided by cookbook: "{cookbook}".'
                )

                selected_recipe_version = {}

                for recipe_version in recipe_versions:
                    if cookbook in recipe_version["cookbooks"].keys():
                        selected_recipe_version = recipe_version
                        break

                if selected_recipe_version == {}:
                    self.logger.error(
                        f'Clone failed: Requested recipe "{recipe}" could not be found in cookbook: "{cookbook}".'
                    )
                    return False

                version = selected_recipe_version["version"]

                if (
                    selected_recipe_version["version"]
                    != highest_recipe_version["version"]
                ):
                    self.logger.warning(
                        f'The version selected from cookbook "{cookbook}" is not the highest version available.'
                    )
                    self.logger.warning(
                        f"A newer version appears to be available from other sources:"
                    )
                    self.logger.info(f"")
                    self.print_recipe_details(
                        recipe, highest_recipe_version, verbose=True, all=True
                    )

        else:
            # version specified
            if cookbook == "":
                self.logger.info(
                    f"No cookbook specified, will select recipe only if version is provided by only one cookbook."
                )

                selected_recipe_version = {}

                for recipe_version in recipe_versions:
                    if version == recipe_version["version"]:

                        cookbook = get_cookbook(recipe, recipe_version)
                        break

                if cookbook == "":
                    return False

            else:
                # version and cookbook specified.
                pass

        if destination == "":
            destination = os.getcwd()

        try:
            recipe_class = self.recipes[recipe][version][cookbook]
        except KeyError:
            self.logger.error(
                f'Clone failed: Requested recipe "{nvc_str(recipe, version, cookbook)}" could not be found.'
            )
            return False

        recipe_basename = os.path.basename(recipe_class.module_file)
        clone_path = os.path.join(destination, recipe_basename)

        try:
            shutil.copyfile(
                recipe_class.module_file, os.path.join(destination, recipe_basename)
            )

            patch_dirs_copied: list = []
            for each_platform in recipe_class.platforms:
                for target in recipe_class.platforms[each_platform]:
                    if (
                        "patches" in recipe_class.platforms[each_platform][target]
                        and recipe_class.platforms[each_platform][target]["patches"] != ""
                    ):
                        patch_dir = os.path.join(
                            os.path.split(recipe_class.module_file)[0],
                            recipe_class.platforms[each_platform][target]["patches"],
                        )
                        if patch_dir in patch_dirs_copied:
                            # Already got this one,
                            continue

                        if not os.path.exists(patch_dir):
                            self.logger.warning(
                                f"Unable to clone referenced patch directory: {patch_dir}"
                            )
                            self.logger.warning(f"Directory does not exist.")
                        else:
                            patches_basename = os.path.basename(patch_dir)
                            shutil.copytree(
                                patch_dir, os.path.join(destination, patches_basename)
                            )
                        patch_dirs_copied.append(patch_dir)
        except Exception as exc:
            self.logger.error(f"Clone failed.  Exception: {exc}")
            return False

        self.logger.info(
            f'Successfully cloned recipe "{nvc_str(recipe, version, cookbook)}" to:'
        )
        self.logger.info(f"    {clone_path}")

        return True

    def list_recipes(self, verbose: bool = False):
        """
        Print out a list of all recipes and all collections.
        """
        has_collections = False

        if len(self.sorted_recipes) == 0:
            if len(self.cookbooks) > 0:
                self.logger.warning(f"No recipes available from trusted cookbooks.")
                self.logger.warning(f"Recipes from \"untrusted\" cookbooks are hidden by default.\n")
                self.logger.info(f"Run the this to view that which cookbooks are available:")
                self.logger.info(f"    mussels cookbook list -V\n")
                self.logger.info(f"Run this to view recipes & tools from a specific cookbook:")
                self.logger.info(f"    mussels cookbook show <name> -V\n")
                self.logger.info(f"To view ALL recipes, use:")
                self.logger.info(f"    mussels recipe list -a")
                return
            else:
                self.logger.warning(f"Failed to load any recipes.\n")
                self.logger.info(f"Re-run Mussels from a directory containing Mussels recipe & tool definitions,")
                self.logger.info(f" or use `mussels update` to download recipes from the public cookbooks.")
                return

        self.logger.info("Recipes:")
        for recipe in self.sorted_recipes:
            newest_version = self.sorted_recipes[recipe][0]["version"]
            cookbooks = list(self.recipes[recipe][newest_version].keys())
            if not self.recipes[recipe][newest_version][cookbooks[0]].is_collection:
                if not verbose:
                    outline = f"    {recipe:10} "
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            outline += f" {version['version']}"
                            if len(self.sorted_recipes[recipe]) > 1:
                                outline += "*"
                        else:
                            outline += f", {version['version']}"
                    outline += ""
                    self.logger.info(outline)
                else:
                    outline = f"    {recipe:10} "
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            outline += f" {version['version']} {version['cookbooks']}"
                            if len(self.sorted_recipes[recipe]) > 1:
                                outline += "*"
                        else:
                            outline += f", {version['version']} {version['cookbooks']}"
                    outline += ""
                    self.logger.info(outline)

        for recipe in self.sorted_recipes:
            newest_version = self.sorted_recipes[recipe][0]["version"]
            cookbooks = list(self.recipes[recipe][newest_version].keys())
            if self.recipes[recipe][newest_version][cookbooks[0]].is_collection:
                if not has_collections:
                    self.logger.info("")
                    self.logger.info("Collections:")
                    has_collections = True

                if not verbose:
                    outline = f"    {recipe:10} "
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            outline += f" {version['version']}"
                            if len(self.sorted_recipes[recipe]) > 1:
                                outline += "*"
                        else:
                            outline += f", {version['version']}"
                    outline += ""
                    self.logger.info(outline)
                else:
                    outline = f"    {recipe:10} "
                    for i, version in enumerate(self.sorted_recipes[recipe]):
                        if i == 0:
                            outline += f" {version['version']} {version['cookbooks']}"
                            if len(self.sorted_recipes[recipe]) > 1:
                                outline += "*"
                        else:
                            outline += f", {version['version']} {version['cookbooks']}"
                    outline += ""
                    self.logger.info(outline)

    def print_tool_details(
        self, tool: str, version: dict, verbose: bool, all: bool
    ):
        """
        Print tool information.
        """
        version_num = version["version"]
        cookbooks = version["cookbooks"].keys()
        self.logger.info(f"    {nvc_str(tool, version_num)};  provided by cookbook(s): {list(cookbooks)}")

        if verbose:
            self.logger.info("")
            for cookbook in cookbooks:
                self.logger.info(f"      Cookbook: {cookbook}")

                book_tool = self.tools[tool][version_num][cookbook]

                self.logger.info(f"        Platforms:")
                for each_platform in book_tool.platforms:
                    if all or platform_is(each_platform):
                        self.logger.info(f"          Host platform: {each_platform}")

                        details = yaml.dump(book_tool.platforms[each_platform], indent=4)
                        for detail in details.split('\n'):
                            self.logger.info("            " + detail)

                        if not all:
                            break
            self.logger.info("")

    def show_tool(self, tool_match: str, version_match: str, verbose: bool = False):
        """
        Search tools for a specific tool and print tool details.
        """

        found = False

        if version_match == "":
            self.logger.info(f'Searching for tool matching name: "{tool_match}"...')
        else:
            self.logger.info(
                f'Searching for tool matching name: "{tool_match}", version: "{version_match}"...'
            )
        # Attempt to match the tool name
        for tool in self.sorted_tools:
            if fnmatch.fnmatch(tool, tool_match):
                if version_match == "":
                    found = True

                    # Show info for every version
                    for version in self.sorted_tools[tool]:
                        self.print_tool_details(tool, version, verbose, all)
                    break
                else:
                    # Attempt to match the version too
                    for version in self.sorted_tools[tool]:
                        if fnmatch.fnmatch(version, version_match):
                            found = True

                            self.print_tool_details(tool, version, verbose, all)
                            break
                    if found:
                        break
        if not found:
            if version_match == "":
                self.logger.warning(f'No tool matching name: "{tool_match}"')
            else:
                self.logger.warning(
                    f'No tool matching name: "{tool_match}", version: "{version_match}"'
                )

    def clone_tool(self, tool: str, version: str, cookbook: str, destination: str):
        """
        Search tools for a specific tool and copy the file to the CWD.
        """

        def get_cookbook(tool: str, tool_version: dict) -> str:
            """
            Return the cookbook name, if only one cookbook provides the tool-version.
            If more then one cookbook provides the tool-version, explain the options and return an empty string.
            """
            cookbook = ""

            num_cookbooks = len(tool_version["cookbooks"].keys())
            if num_cookbooks == 0:
                self.logger.error(
                    f"tool {nvc_str(tool, version)} not provided by any cookbook!(?!)"
                )

            elif num_cookbooks == 1:
                cookbook = next(iter(tool_version["cookbooks"]))

            else:
                self.logger.error(
                    f'Clone failed: No cookbook specified, and multiple cookbooks provide tool "{nvc_str(tool, tool_version["version"])}"'
                )
                self.logger.error(
                    f"Please retry with a specific cookbook using the `-c` or `--cookbook` option:"
                )
                self.logger.info(f"")

                self.print_tool_details(
                    tool, tool_version, verbose=True, all=True
                )

            return cookbook

        found = False

        self.logger.info(
            f'Attempting to clone tool: "{nvc_str(tool, version, cookbook)}"...'
        )

        try:
            tool_versions = self.sorted_tools[tool]
        except KeyError:
            self.logger.error(f'Clone failed: No such tool "{tool}"')
            return False

        # Identify highest available version, for future reference.
        highest_tool_version = tool_versions[0]

        #
        # Now repeat the above if/else logic to select the exact tool requested.
        #

        if version == "":
            if cookbook == "":
                # neither version nor cookbook was specified.
                self.logger.info(
                    f"No version or cookbook specified, will select highest available version."
                )
                version = highest_tool_version["version"]

                cookbook = get_cookbook(version, highest_tool_version)

                if cookbook == "":
                    return False

            else:
                # cookbook specified, but version wasn't.
                self.logger.info(
                    f'No version specified, will select highest version provided by cookbook: "{cookbook}".'
                )

                selected_tool_version = {}

                for tool_version in tool_versions:
                    if cookbook in tool_version["cookbooks"].keys():
                        selected_tool_version = tool_version
                        break

                if selected_tool_version == {}:
                    self.logger.error(
                        f'Clone failed: Requested tool "{tool}" could not be found in cookbook: "{cookbook}".'
                    )
                    return False

                version = selected_tool_version["version"]

                if (
                    selected_tool_version["version"]
                    != highest_tool_version["version"]
                ):
                    self.logger.warning(
                        f'The version selected from cookbook "{cookbook}" is not the highest version available.'
                    )
                    self.logger.warning(
                        f"A newer version appears to be available from other sources:"
                    )
                    self.logger.info(f"")
                    self.print_tool_details(
                        tool, highest_tool_version, verbose=True, all=True
                    )

        else:
            # version specified
            if cookbook == "":
                self.logger.info(
                    f"No cookbook specified, will select tool only if version is provided by only one cookbook."
                )

                selected_tool_version = {}

                for tool_version in tool_versions:
                    if version == tool_version["version"]:

                        cookbook = get_cookbook(tool, tool_version)
                        break

                if cookbook == "":
                    return False

            else:
                # version and cookbook specified.
                pass

        if destination == "":
            destination = os.getcwd()

        try:
            tool_class = self.tools[tool][version][cookbook]
        except KeyError:
            self.logger.error(
                f'Clone failed: Requested tool "{nvc_str(tool, version, cookbook)}" could not be found.'
            )
            return False

        tool_basename = os.path.basename(tool_class.module_file)
        clone_path = os.path.join(destination, tool_basename)

        try:
            shutil.copyfile(
                tool_class.module_file, os.path.join(destination, tool_basename)
            )
        except Exception as exc:
            self.logger.error(f"Clone failed.  Exception: {exc}")
            return False

        self.logger.info(
            f'Successfully cloned tool "{nvc_str(tool, version, cookbook)}" to:'
        )
        self.logger.info(f"    {clone_path}")

        return True

    def list_tools(self, verbose: bool = False):
        """
        Print out a list of all tools and all collections.
        """
        has_collections = False

        if len(self.sorted_tools) == 0:
            if len(self.cookbooks) > 0:
                self.logger.warning(f"No tools available from trusted cookbooks.")
                self.logger.warning(f"Tools from \"untrusted\" cookbooks are hidden by default.\n")
                self.logger.info(f"Run the this to view that which cookbooks are available:")
                self.logger.info(f"    mussels cookbook list -V\n")
                self.logger.info(f"Run this to view recipes & tools from a specific cookbook:")
                self.logger.info(f"    mussels cookbook show <name> -V\n")
                self.logger.info(f"To view ALL tools, use:")
                self.logger.info(f"    mussels tool list -a")
                return
            else:
                self.logger.warning(f"Failed to load any tools.\n")
                self.logger.info(f"Re-run Mussels from a directory containing Mussels recipe & tool definitions,")
                self.logger.info(f" or use `mussels update` to download recipes from the public cookbooks.")
                return

        self.logger.info("Tools:")
        for tool in self.sorted_tools:
            newest_version = self.sorted_tools[tool][0]["version"]
            cookbooks = list(self.tools[tool][newest_version].keys())

            if not verbose:
                outline = f"    {tool:10} "
                for i, version in enumerate(self.sorted_tools[tool]):
                    if i == 0:
                        outline += f" {version['version']}"
                        if len(self.sorted_tools[tool]) > 1:
                            outline += "*"
                    else:
                        outline += f", {version['version']}"
                outline += ""
                self.logger.info(outline)
            else:
                outline = f"    {tool:10} "
                for i, version in enumerate(self.sorted_tools[tool]):
                    if i == 0:
                        outline += f" {version['version']} {version['cookbooks']}"
                        if len(self.sorted_tools[tool]) > 1:
                            outline += "*"
                    else:
                        outline += f", {version['version']} {version['cookbooks']}"
                outline += ""
                self.logger.info(outline)

    def update_cookbooks(self) -> None:
        """
        Attempt to update each cookbook in using Git to clone or pull each repo.
        If git isn't available, warn the user they should probably install Git and add it to their PATH.
        """
        # Create ~/.mussels/bookshelf if it doesn't already exist.
        os.makedirs(os.path.join(self.app_data_dir, "cookbooks"), exist_ok=True)

        # Get url for each cookbook from the mussels bookshelf.
        for book in mussels.bookshelf.cookbooks:
            repo_dir = os.path.join(self.app_data_dir, "cookbooks", book)
            self.cookbooks[book]["path"] = repo_dir
            self.cookbooks[book]["url"] = mussels.bookshelf.cookbooks[book]["url"]
            if "trusted" not in self.cookbooks[book]:
                self.cookbooks[book]["trusted"] = False

        for book in self.cookbooks:
            repo_dir = os.path.join(self.app_data_dir, "cookbooks", book)

            if "url" in self.cookbooks[book] and self.cookbooks[book]["url"] != "":
                if not os.path.isdir(repo_dir):
                    repo = git.Repo.clone_from(self.cookbooks[book]["url"], repo_dir)
                else:
                    repo = git.Repo(repo_dir)
                    repo.git.pull()

            self._read_cookbook(book, repo_dir)

        self._store_config("cookbooks.json", self.cookbooks)

    def list_cookbooks(self, verbose: bool = False):
        """
        Print out a list of all cookbooks.
        """

        if len(self.cookbooks) == 0:
            self.logger.warning(f"Failed to load any cookbooks.\n")
            self.logger.info(f"Re-run Mussels from a directory containing Mussels recipe & tool definitions,")
            self.logger.info(f" or use `mussels update` to download recipes from the public cookbooks.")
            return

        self.logger.info("Cookbooks:")
        for cookbook in self.cookbooks:
            self.logger.info(f"    {cookbook}")

            if verbose:
                if cookbook == "local":
                    self.logger.info(f"        url:     n/a")
                else:
                    self.logger.info(
                        f"        url:     {self.cookbooks[cookbook]['url']}"
                    )
                self.logger.info(f"        path:    {self.cookbooks[cookbook]['path']}")
                self.logger.info(
                    f"        trusted: {self.cookbooks[cookbook]['trusted']}"
                )
                self.logger.info(f"")

    def show_cookbook(self, cookbook_match: str, verbose: bool):
        """
        Search cookbooks for a specific cookbook and print the details.
        """
        found = False

        self.logger.info(f'Searching for cookbook matching name: "{cookbook_match}"...')

        # Attempt to match the cookbook name
        for cookbook in self.cookbooks:
            if fnmatch.fnmatch(cookbook, cookbook_match):
                found = True

                self.logger.info(f"    {cookbook}")
                if cookbook == "local":
                    self.logger.info(f"        url:     n/a")
                else:
                    self.logger.info(
                        f"        url:     {self.cookbooks[cookbook]['url']}"
                    )
                self.logger.info(f"        path:    {self.cookbooks[cookbook]['path']}")
                self.logger.info(
                    f"        trusted: {self.cookbooks[cookbook]['trusted']}"
                )

                if verbose:
                    self.logger.info(f"")
                    if len(self.cookbooks[cookbook]["recipes"].keys()) > 0:
                        self.logger.info(f"    Recipes:")
                        for recipe in self.cookbooks[cookbook]["recipes"]:
                            self.logger.info(
                                f"        {recipe} : {self.cookbooks[cookbook]['recipes'][recipe]}"
                            )
                        self.logger.info(f"")
                    if len(self.cookbooks[cookbook]["tools"].keys()) > 0:
                        self.logger.info(f"    Tools:")
                        for tool in self.cookbooks[cookbook]["tools"]:
                            self.logger.info(
                                f"        {tool} : {self.cookbooks[cookbook]['tools'][tool]}"
                            )

        if not found:
            self.logger.warning(f'No cookbook matching name: "{cookbook_match}"')

    def clean_cache(self):
        """
        Clear the cache files.
        """
        self.logger.info(
            f"Clearing cache directory ( {os.path.join(self.app_data_dir, 'cache')} )..."
        )

        if os.path.exists(os.path.join(self.app_data_dir, "cache")):
            shutil.rmtree(os.path.join(self.app_data_dir, "cache"))
            self.logger.info(f"Cache directory cleared.")
        else:
            self.logger.info(f"No cache directory to clear.")

    def clean_install(self):
        """
        Clear the install files.
        """
        self.logger.info(
            f"Clearing install directory ( {os.path.join(self.app_data_dir, 'install')} )..."
        )

        if os.path.exists(os.path.join(self.app_data_dir, "install")):
            shutil.rmtree(os.path.join(self.app_data_dir, "install"))
            self.logger.info(f"Install directory cleared.")
        else:
            self.logger.info(f"No install directory to clear.")

    def clean_logs(self):
        """
        Clear the log files.
        """
        self.logger.info(
            f"Clearing logs directory ( {os.path.join(self.app_data_dir, 'logs')} )..."
        )

        self.filehandler.close()
        self.logger.removeHandler(self.filehandler)

        if os.path.exists(os.path.join(self.app_data_dir, "logs")):
            shutil.rmtree(os.path.join(self.app_data_dir, "logs"))
            self.logger.info(f"Logs directory cleared.")
        else:
            self.logger.info(f"No logs directory to clear.")

    def clean_all(self):
        """
        Clear all Mussels files.
        """
        self.clean_cache()
        self.clean_install()
        self.clean_logs()

        self.logger.info(
            f"Clearing Mussels directory ( {os.path.join(self.app_data_dir)} )..."
        )

        if os.path.exists(os.path.join(self.app_data_dir)):
            shutil.rmtree(os.path.join(self.app_data_dir))
            self.logger.info(f"Mussels directory cleared.")
        else:
            self.logger.info(f"No Mussels directory to clear.")

    def config_trust_cookbook(self, cookbook):
        """
        Update config to indicate that a given cookbook is trusted.
        """
        if cookbook not in self.cookbooks:
            self.logger.error(
                f"Can't trust cookbook '{cookbook}'. Cookbook is unknown."
            )

        self.logger.info(f"'{cookbook}' cookbook is now trusted.")

        self.cookbooks[cookbook]["trusted"] = True

        self._store_config("cookbooks.json", self.cookbooks)

    def config_add_cookbook(self, cookbook, author, url, trust=False):
        """
        Update config to indicate that a given cookbook is trusted.
        """
        self.cookbooks[cookbook]["author"] = author
        self.cookbooks[cookbook]["url"] = url
        self.cookbooks[cookbook]["trusted"] = trust

        self._store_config("cookbooks.json", self.cookbooks)

    def config_remove_cookbook(self, cookbook):
        self.cookbooks.pop(cookbook)

        self._store_config("cookbooks.json", self.cookbooks)
