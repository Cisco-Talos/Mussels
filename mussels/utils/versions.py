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

from collections import defaultdict, namedtuple
import platform

NVC = namedtuple("NVC", "name version cookbook")


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
    sorted_items: defaultdict = defaultdict(list)

    for item in items:
        versions_list = list(items[item].keys())
        versions_list.sort(key=version_keys)
        versions_list.reverse()
        for version in versions_list:
            sorted_items[item].append(version)

    return sorted_items


PLATFORMS = {
    "posix": [
        "linux",
        "darwin",
        "macos",
        "osx",
        "freebsd",
        "openbsd",
        "sunos",
        "aix",
        "hp-ux",
    ],
    "unix": ["darwin", "macos", "osx", "freebsd", "openbsd", "sunos", "aix", "hp-ux"],
}


def platform_matches(requested_platform: str, specific_platform) -> bool:
    """
    Compare two platforms.
    Common platforms:
    - Windows
    - macos / darwin / osx
    - linux
    - unix (macos, sunos, bsd unix's)
    - *nix / posix (not windows)
    :return: True  if current platform matches requested platform.
    :return: False otherwise.
    """
    specific_platform = specific_platform.lower()
    requested_platform = requested_platform.lower()

    if requested_platform == specific_platform:
        return True

    elif (
        requested_platform == "mac"
        or requested_platform == "macos"
        or requested_platform == "osx"
    ) and specific_platform == "darwin":
        return True

    if (requested_platform == "unix") and (
        specific_platform == "darwin"
        or specific_platform == "sunos"
        or "bsd" in specific_platform
    ):
        return True

    elif requested_platform == "*nix" or requested_platform == "posix":
        if specific_platform != "windows":
            return True

    else:
        return False

    return False


def platform_is(requested_platform: str) -> bool:
    """
    Compare requested platform with current platform.
    Common platforms:
    - Win / Windows
    - Mac / macOS / Darwin
    - Linux
    - Unix (Mac, SunOS, BSD unix's)
    - *nix / posix (Not Windows)
    :return: True  if current platform matches requested platform.
    :return: False otherwise.
    """
    return platform_matches(requested_platform, platform.system())


def pick_platform(requested_platform: str, platform_options: list) -> str:
    """
    Given a list of platforms, pick the one that most closely matches the current platform.
    Prefer exact, allow superset.
    :return: string name of selected platform.
    """
    if requested_platform in platform_options:
        return requested_platform

    for option in platform_options:
        if platform_matches(option, requested_platform):
            return option

    return ""


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


def get_item_version(item_name: str, sorted_items: dict, target: str = "") -> NVC:
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

    :return: named tuple describing the highest qualified version:
        NVC(
            "name"->str,
            "version"->str,
            "cookbook"->str,
        )
    """

    def select_cookbook_version(nvc, item_version, target: str = "") -> bool:
        cookbook_selected = False

        def cookbook_has_build_target(cookbooks_item: dict, target) -> bool:
            if target == "":
                return True

            for each_platform in cookbooks_item:
                # Note: sorted_items has been filtered down to compatible platform.
                #       No need to check with platform_is()
                if target in cookbooks_item[each_platform]:
                    return True
            return False

        # Prefer local over all else, enabling monkey-patching of recipes.
        if "local" in item_version["cookbooks"] and cookbook_has_build_target(
            item_version["cookbooks"]["local"], target
        ):
            nvc["version"] = item_version["version"]
            nvc["cookbook"] = "local"
            cookbook_selected = True
        else:
            if nvc["cookbook"] == "":
                # Any cookbook will do.
                for cookbook in item_version["cookbooks"]:
                    if cookbook_has_build_target(
                        item_version["cookbooks"][cookbook], target
                    ):
                        nvc["version"] = item_version["version"]
                        nvc["cookbook"] = cookbook
                        cookbook_selected = True
                        break
            else:
                # Check for requested cookbook.
                for cookbook in item_version["cookbooks"]:
                    if cookbook == nvc["cookbook"] and cookbook_has_build_target(
                        item_version["cookbooks"][cookbook], target
                    ):
                        nvc["version"] = item_version["version"]
                        cookbook_selected = True
                        break

        # Remove all other cookbooks for this item version.
        if cookbook_selected:
            item_version["cookbooks"] = {
                nvc["cookbook"]: item_version["cookbooks"][nvc["cookbook"]]
            }
        return cookbook_selected

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
                    item_selected = select_cookbook_version(nvc, item_version, target)
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
                    item_selected = select_cookbook_version(nvc, item_version, target)
            else:
                # Version is too low. Remove it, and subsequent versions.
                sorted_items[name] = sorted_items[name][:i]
                break

    elif "<=" in item_name:
        # LTE requirement found.
        name, version = item_name.split("<=")
        nvc["name"] = name.strip()
        version = version.strip()

        # First, prune down to highest tolerable version
        if len(sorted_items[name]) > 0:
            while (
                len(sorted_items[name]) > 0
                and compare_versions(sorted_items[name][0]["version"], version) > 0
            ):
                # Remove a version from the sorted_items.
                sorted_items[name].remove(sorted_items[name][0])

        # Then, prune down to the highest version provided by a the requested cookbook
        if len(sorted_items[name]) > 0:
            while len(sorted_items[name]) > 0 and not item_selected:
                item_selected = select_cookbook_version(
                    nvc, sorted_items[name][0], target
                )

                if not item_selected:
                    # Remove a version from the sorted_items.
                    sorted_items[name].remove(sorted_items[name][0])

    elif "<" in item_name:
        # LT requirement found.
        name, version = item_name.split("<")
        nvc["name"] = name.strip()
        version = version.strip()

        # First, prune down to highest tolerable version
        if len(sorted_items[name]) > 0:
            while (
                len(sorted_items[name]) > 0
                and compare_versions(sorted_items[name][0]["version"], version) >= 0
            ):
                # Remove a version from the sorted_items.
                sorted_items[name].remove(sorted_items[name][0])

        # Then, prune down to the highest version provided by a the requested cookbook
        if len(sorted_items[name]) > 0:
            while len(sorted_items[name]) > 0 and not item_selected:
                item_selected = select_cookbook_version(
                    nvc, sorted_items[name][0], target
                )

                if not item_selected:
                    # Remove a version from the sorted_items.
                    sorted_items[name].remove(sorted_items[name][0])

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
                    item_selected = select_cookbook_version(nvc, item_version, target)
                    if item_selected:
                        sorted_items[nvc["name"]] = [item_version]
                        break

        else:
            # No version requirement found.
            nvc["name"] = item_name.strip()

            for item_version in sorted_items[nvc["name"]]:
                item_selected = select_cookbook_version(nvc, item_version, target)
                if item_selected:
                    break

    if not item_selected:
        if target == "":
            raise Exception(
                f"No versions available to satisfy requirement for {requested_item}"
            )
        else:
            raise Exception(
                f"No versions available to satisfy requirement for {requested_item} ({target})"
            )

    return NVC(nvc["name"], nvc["version"], nvc["cookbook"])


def nvc_str(name, version, cookbook: str = ""):
    def nv_str(name, version):
        if version != "":
            return f"{name}-{version}"
        else:
            return name

    if cookbook != "":
        return f"{cookbook}:{nv_str(name, version)}"
    else:
        return nv_str(name, version)

