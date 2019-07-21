"""
Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

This module provides utility functions to load recipe and tool Python modules from a given directory.

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
import pkgutil
import os


def recipes(recipe_path):
    """
    Collect all Recipes in a directory.
    """
    recipes = defaultdict(dict)

    if not os.path.exists(recipe_path):
        return recipes

    for root, dirs, _ in os.walk(recipe_path):
        for directory in dirs:
            for loader, module_name, _ in pkgutil.walk_packages(
                [os.path.join(root, directory)]
            ):
                _module = loader.find_module(module_name).load_module(module_name)
                globals()[module_name] = _module
                if "Recipe" in dir(_module):
                    recipes[_module.Recipe.name][
                        _module.Recipe.version
                    ] = _module.Recipe

    return recipes


def tools(tool_path):
    """
    Collect all Tools in a directory.
    """
    tools = defaultdict(dict)

    if not os.path.exists(tool_path):
        return tools

    for root, dirs, _ in os.walk(tool_path):
        for directory in dirs:
            for loader, module_name, _ in pkgutil.walk_packages(
                [os.path.join(root, directory)]
            ):
                _module = loader.find_module(module_name).load_module(module_name)
                globals()[module_name] = _module
                if "Tool" in dir(_module):
                    tools[_module.Tool.name][_module.Tool.version] = _module.Tool

    return tools
