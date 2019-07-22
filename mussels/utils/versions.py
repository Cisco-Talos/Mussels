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


def sort_by_version(items) -> defaultdict:
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


def get_item_version(item: str, sorted_items: dict) -> tuple:
    """
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
    """
    if ">=" in item:
        # GTE requirement found.
        name, version = item.split(">=")
        for i, ver in enumerate(sorted_items[name]):
            cmp = compare_versions(ver, version)
            if cmp < 0:
                # Version is too low. Remove it, and subsequent versions.
                sorted_items[name] = sorted_items[name][:i]
                break

    elif ">" in item:
        # GT requirement found.
        name, version = item.split(">")
        for i, ver in enumerate(sorted_items[name]):
            cmp = compare_versions(ver, version)
            if cmp <= 0:
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
                raise Exception(
                    f"No versions available to satisfy requirement for {item}"
                )

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
                raise Exception(
                    f"No versions available to satisfy requirement for {item}"
                )
    else:
        eq_cond = False
        if "==" in item:
            name, version = item.split("==")
            eq_cond = True
        elif "=" in item:
            name, version = item.split("=")
            eq_cond = True
        elif "-" in item:
            name, version = item.split("-")
            eq_cond = True
        elif "@" in item:
            name, version = item.split("@")
            eq_cond = True

        if eq_cond == True:
            # EQ requirement found.
            # Try to find the specific version, and remove all others.
            if not version in sorted_items[name]:
                raise Exception(
                    f"No versions available to satisfy requirement for {item}"
                )
            sorted_items[name] = [version]

        else:
            # No version requirement found.
            name = item

    try:
        selected_version = sorted_items[name][0]
    except:
        raise Exception(f"No versions available to satisfy requirement for {item}")

    return (sorted_items, (name, selected_version))
