"""
Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

This module provides an assortment of helper functions that Mussels depends on.

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


def version_keys(s):
    """
    `key` function enabling python's `sort` function to sort version strings.
    """
    import re

    keys = []
    for u in s.split("."):
        for v in re.split(r"(\d+)", u):
            try:
                val = int(v)
            except:
                val = str(v)
            keys.append(val)
    return keys


def sort_cookbook_by_version(items) -> defaultdict:
    """
    Sort items, and determine the highest versions.
    """
    sorted_items = defaultdict(list)

    for item in items:
        versions_list = list(items[item].keys())
        versions_list.sort(key=version_keys)
        versions_list.reverse()
        for version in versions_list:
            sorted_items[item].append(version)

    return sorted_items


def sort_all_recipes_by_version(items) -> defaultdict:
    """
    Sort items, and determine the highest versions.
    """
    sorted_items = defaultdict(list)

    for item in items:
        versions_list = list(items[item].keys())
        versions_list.sort(key=version_keys)
        versions_list.reverse()
        for version in versions_list:
            item_version = {
                "version": version,
                "cookbooks": list(items[item][version].keys()),
            }
            sorted_items[item].append(item_version)

    return sorted_items


def compare_versions(version_a: str, version_b: str) -> int:
    """
    Evaluate version strings of two versions.
    Compare if version A against version B.
    :return: -1  if A < B
    :return: 0   if A == B
    :return: 1   if A > B
    """
    if version_a == version_b:
        return 0

    versions_list = [version_a, version_b]

    versions_list.sort(key=version_keys)

    if versions_list[0] == version_a:
        return -1
    else:
        return 1


def get_item_version(item_name: str, sorted_items: dict) -> dict:
    """
    Convert a item name in the below format to a (name, version) tuple:

        [cookbook:]name[>=,<=,>,<,(==|=|@)version]

    Examples:
        - meepioux
        - blarghus>=1.2.3
        - wheeple@0.2.0
        - pyplo==5.1.0g
        - scrapbook:sasquatch<2.0.0
        - scrapbook: minnow < 0.1.12

    The highest available version will be selected if one is not specified.
    Version requirements will whittle down the list of available versions
    in the sorted_items list.

    If a specific version is specified, all other versions will be disqualified (pruned).

    If no versions remain that satisfy build qualifications, an exception will be raised.

    :return: dict describing the highest qualified version:
        {
            name"->str,
            "version"->str,
            "cookbook"->str
        }
    """

    nvc = {"name": "", "version": "", "cookbook": ""}

    requested_item = item_name
    item_selected = False

    # Identify cookbook name, if provided.
    if ":" in item_name:
        cookbook, item = item_name.split(":")
        nvc["cookbook"] = cookbook.strip()
        item_name = item.strip()

    if ">=" in item_name:
        # GTE requirement found.
        name, version = item_name.split(">=")
        nvc["name"] = name.strip()
        version = version.strip()
        for i, item_version in enumerate(sorted_items[name]):
            cmp = compare_versions(item_version["version"], version)
            if cmp >= 0:
                # Version is good.
                if item_selected != True:
                    if nvc["cookbook"] == "":
                        # Any cookbook will do.
                        for cookbook in item_version["cookbooks"]:
                            nvc["version"] = item_version["version"]
                            nvc["cookbook"] = cookbook
                            item_selected = True
                            break
                    else:
                        # Check for requested cookbook.
                        for cookbook in item_version["cookbooks"]:
                            if cookbook == nvc["cookbook"]:
                                nvc["version"] = item_version["version"]
                                item_selected = True
                                break
            else:
                # Version is too low. Remove it, and subsequent versions.
                sorted_items[name] = sorted_items[name][:i]
                break

    elif ">" in item_name:
        # GT requirement found.
        name, version = item_name.split(">")
        nvc["name"] = name.strip()
        version = version.strip()
        for i, item_version in enumerate(sorted_items[name]):
            cmp = compare_versions(item_version["version"], version)
            if cmp > 0:
                # Version is good.
                if item_selected != True:
                    if nvc["cookbook"] == "":
                        # Any cookbook will do.
                        for cookbook in item_version["cookbooks"]:
                            nvc["version"] = item_version["version"]
                            nvc["cookbook"] = cookbook
                            item_selected = True
                            break
                    else:
                        # Check for requested cookbook.
                        for cookbook in item_version["cookbooks"]:
                            if cookbook == nvc["cookbook"]:
                                nvc["version"] = item_version["version"]
                                item_selected = True
                                break
            else:
                # Version is too low. Remove it, and subsequent versions.
                sorted_items[name] = sorted_items[name][:i]
                break

    elif "<=" in item_name:
        # LTE requirement found.
        name, version = item_name.split("<=")
        nvc["name"] = name.strip()
        version = version.strip()
        try:
            first = sorted_items[name][0]
        except:
            raise Exception(
                f"No versions available to satisfy requirement for {item_name}"
            )
        while (compare_versions(first["version"], version) > 0) or (
            nvc["cookbook"] != "" and nvc["cookbook"] not in first["cookbooks"]
        ):
            # Remove a version from the sorted_items.
            sorted_items[name].remove(first)

            try:
                first = sorted_items[name][0]
            except:
                raise Exception(
                    f"No versions available to satisfy requirement for {requested_item}"
                )
        try:
            nvc["version"] = sorted_items[name][0]["version"]
            if nvc["cookbook"] == "":
                nvc["cookbook"] = sorted_items[name][0]["cookbooks"][0]
        except:
            raise Exception(
                f"No versions available to satisfy requirement for {item_name}"
            )
        item_selected = True

    elif "<" in item_name:
        # LT requirement found.
        name, version = item_name.split("<")
        nvc["name"] = name.strip()
        version = version.strip()
        try:
            first = sorted_items[name][0]
        except:
            raise Exception(
                f"No versions available to satisfy requirement for {requested_item}"
            )
        while (compare_versions(first["version"], version) >= 0) or (
            nvc["cookbook"] != "" and nvc["cookbook"] not in first["cookbooks"]
        ):
            # Remove a version from the sorted_items.
            sorted_items[name].remove(first)

            try:
                first = sorted_items[name][0]
            except:
                raise Exception(
                    f"No versions available to satisfy requirement for {requested_item}"
                )
        try:
            nvc["version"] = sorted_items[name][0]["version"]
            if nvc["cookbook"] == "":
                nvc["cookbook"] = sorted_items[name][0]["cookbooks"][0]
        except:
            raise Exception(
                f"No versions available to satisfy requirement for {requested_item}"
            )
        item_selected = True

    else:
        eq_cond = False
        if "==" in item_name:
            name, version = item_name.split("==")
            eq_cond = True
        elif "=" in item_name:
            name, version = item_name.split("=")
            eq_cond = True
        elif "-" in item_name:
            name, version = item_name.split("-")
            eq_cond = True
        elif "@" in item_name:
            name, version = item_name.split("@")
            eq_cond = True

        if eq_cond == True:
            nvc["name"] = name.strip()
            nvc["version"] = version.strip()
            # EQ requirement found.
            # Try to find the specific version, and remove all others.
            item_selected = False
            for item_version in sorted_items[nvc["name"]]:
                if version == item_version["version"]:
                    if nvc["cookbook"] == "":
                        for cookbook in item_version["cookbooks"]:
                            item_selected = True
                            nvc["cookbook"] = cookbook
                            sorted_items[nvc["name"]] = [item_version]
                            break
                    else:
                        if nvc["cookbook"] in item_version["cookbooks"]:
                            item_selected = True
                            item_version["cookbooks"] = [nvc["cookbook"]]
                            sorted_items[nvc["name"]] = [item_version]
                            break
                if item_selected:
                    break

        else:
            # No version requirement found.
            nvc["name"] = item_name.strip()

            if nvc["cookbook"] == "":
                # No specific cookbook requirement foud either.
                for item_version in sorted_items[nvc["name"]]:
                    for cookbook in item_version["cookbooks"]:
                        item_selected = True
                        nvc["version"] = item_version["version"]
                        nvc["cookbook"] = cookbook
                        break
                    if nvc["cookbook"] != "":
                        break
            else:
                # Try to find a version provided by the requested cookbook
                for item_version in sorted_items[nvc["name"]]:
                    for cookbook in item_version["cookbooks"]:
                        if cookbook == nvc["cookbook"]:
                            item_selected = True
                            nvc["version"] = item_version["version"]
                            nvc["cookbook"] = cookbook
                            break
                    if nvc["cookbook"] != "":
                        break

    if not item_selected:
        raise Exception(
            f"No versions available to satisfy requirement for {requested_item}"
        )

    return nvc
