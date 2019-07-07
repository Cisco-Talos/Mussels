"""
Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

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

import os

from recipes.recipe import BaseRecipe


class Recipe(BaseRecipe):
    """
    Recipe to build pcre2.
    """

    name = "pcre2"
    version = "10.33"
    url = "https://ftp.pcre.org/pub/pcre/pcre2-10.33.zip"
    patches = os.path.join(os.path.split(os.path.abspath(__file__))[0], "patches")
    install_paths = {
        "x86": {
            "include": [os.path.join("pcre2.h")],
            "lib": [
                os.path.join("Release", "pcre2-8.dll"),
                os.path.join("Release", "pcre2-8.lib"),
            ],
        },
        "x64": {
            "include": [os.path.join("pcre2.h")],
            "lib": [
                os.path.join("Release", "pcre2-8.dll"),
                os.path.join("Release", "pcre2-8.lib"),
            ],
        },
    }
    dependencies = ["bzip2", "zlib"]
    required_tools = ["cmake", "visualstudio>=2017"]
    build_script = {
        "x86": """
            CALL cmake.exe -G "Visual Studio 15 2017" -T v141 \
                -DBUILD_SHARED_LIBS=ON \
                -DZLIB_INCLUDE_DIR="{includes}" \
                -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
                -DBZIP2_INCLUDE_DIR="{includes}" \
                -DBZIP2_LIBRARY_RELEASE="{libs}/libbz2.lib"
            CALL cmake.exe --build . --config Release
        """,
        "x64": """
            CALL cmake.exe -G "Visual Studio 15 2017 Win64" -T v141 \
                -DBUILD_SHARED_LIBS=ON \
                -DZLIB_INCLUDE_DIR="{includes}" \
                -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
                -DBZIP2_INCLUDE_DIR="{includes}" \
                -DBZIP2_LIBRARY_RELEASE="{libs}/libbz2.lib"
            CALL cmake.exe --build . --config Release
        """,
    }
