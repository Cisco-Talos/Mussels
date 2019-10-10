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

    mussels_version = "0.1"

    name = "zlib"
    version = "1.2.11"
    url = "https://www.zlib.net/zlib-1.2.11.tar.gz"
    platforms = {
        "Windows": {
            "x86": {
                # "patches": "patches_windows", # (optional) Apply a patch set in this directory before the "configure" build step
                "install_paths": {
                    "license/zlib": ["README"],
                    "include": ["zlib.h", "zconf.h"],
                    "lib": [
                        # os.path.join("Release", "zlib1.dll"),
                        os.path.join("Release", "zlibstatic.lib")
                    ],
                },
                "dependencies": [],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
                            CALL vcvarsall.bat x86 -vcvars_ver=14.1
                            CALL cmake.exe -G "Visual Studio 15 2017" -T v141
                        """,
                    "make": """
                            CALL vcvarsall.bat x86 -vcvars_ver=14.1
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
            "x64": {
                # "patches": "patches_windows",
                "install_paths": {
                    "license/zlib": ["README"],
                    "include": ["zlib.h", "zconf.h"],
                    "lib": [
                        # os.path.join("Release", "zlib1.dll"),
                        os.path.join("Release", "zlibstatic.lib")
                    ],
                },
                "dependencies": [],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
                            CALL vcvarsall.bat amd64 -vcvars_ver=14.1
                            CALL cmake.exe -G "Visual Studio 15 2017 Win64" -T v141
                        """,
                    "make": """
                            CALL vcvarsall.bat amd64 -vcvars_ver=14.1
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
        },
        "Darwin": {
            "host": {
                "install_paths": {"license/zlib": ["README"]},
                "dependencies": [],
                "required_tools": ["cmake", "make", "clang"],
                "build_script": {
                    "configure": """
                            cmake . \
                                -DCMAKE_INSTALL_PREFIX="{install}/{target}"
                        """,
                    "make": """
                            cmake --build . --config Release
                        """,
                    "install": """
                            make install
                        """,
                },
            }
        },
    }

