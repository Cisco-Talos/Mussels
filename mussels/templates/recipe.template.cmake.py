"""
Copyright (C) 2019 Your Name or Company

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/COPYING-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from mussels.recipe import BaseRecipe


class Recipe(BaseRecipe):
    """
    Recipe to build template.
    """

    mussels_version = "0.1"

    # TODO: Replace "template" in this file with your project name.
    # Adjust the options as needed so your project will build.

    name = "template"
    version = "1.2.3"
    is_collection = False
    url = "hxxps://www.template.com/releases/v1.2.3.tar.gz"
    # archive_name_change: tuple = ("v", "template-") # (optional) Change a portion of the filename back to what it was when the archive was created.
    platforms = {
        "Windows": {
            "x86": {
                # "patches": "patches_windows", # (optional) Apply a patch set in this directory before the "configure" build step
                "install_paths": {
                    "license/template": ["COPYING"],
                    "include": ["template.h"],
                    "lib": ["template.dll", "template.lib"],
                },
                "dependencies": [],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
                            CALL cmake.exe -G "Visual Studio 15 2017" -T v141
                        """,
                    "make": """
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
            "x64": {
                # "patches": "patches_windows",
                "install_paths": {
                    "license/template": ["COPYING"],
                    "include": ["template.h"],
                    "lib": ["template.dll", "template.lib"],
                },
                "dependencies": [],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
                            CALL cmake.exe -G "Visual Studio 15 2017 Win64" -T v141
                        """,
                    "make": """
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
        },
        "Darwin": {
            "host": {
                "install_paths": {"license/template": ["COPYING"]},
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
                            install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/lib/template.dylib"
                        """,
                },
            }
        },
        "Linux": {
            "host": {
                "install_paths": {"license/template": ["COPYING"]},
                "dependencies": [],
                "required_tools": ["cmake", "make", "gcc"],
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
                            patchelf --set-rpath /path/to/lib:/other/path my-program
                           # install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/lib/template.dylib"
                        """,
                },
            }
        },
        "FreeBSD": {
            "host": {
                "install_paths": {"license/template": ["COPYING"]},
                "dependencies": [],
                "required_tools": ["cmake", "gmake", "gcc"],
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
                            install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/lib/template.dylib"
                        """,
                },
            }
        },
    }

