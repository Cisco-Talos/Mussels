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

from mussels.recipe import BaseRecipe


class Recipe(BaseRecipe):
    """
    Recipe to build zlib.
    """

    name = "zlib"
    version = "1.2.11"
    url = "https://www.zlib.net/zlib-1.2.11.tar.gz"
    install_paths = {
        "x86": {
            "include": ["zlib.h", "zconf.h"],
            "lib": [
                # os.path.join("Release", "zlib1.dll"),
                os.path.join("Release", "zlibstatic.lib")
            ],
        },
        "x64": {
            "include": ["zlib.h", "zconf.h"],
            "lib": [
                # os.path.join("Release", "zlib1.dll"),
                os.path.join("Release", "zlibstatic.lib")
            ],
        },
    }
    platform = ["Windows"]
    dependencies = []
    required_tools = ["cmake", "visualstudio>=2017"]
    build_script = {
        "x86": """
            CALL vcvarsall.bat x86 -vcvars_ver=14.1
            CALL cmake.exe -G "Visual Studio 15 2017" -T v141
            CALL cmake.exe --build . --config Release
        """,
        "x64": """
            CALL vcvarsall.bat amd64 -vcvars_ver=14.1
            CALL cmake.exe -G "Visual Studio 15 2017 Win64" -T v141
            CALL cmake.exe --build . --config Release
        """,
    }
