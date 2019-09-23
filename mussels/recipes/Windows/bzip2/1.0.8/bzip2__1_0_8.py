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
    Recipe to build bzip2.
    Patches shamelessly copied from: https://github.com/philr/bzip2-windows
    Copyright (c) 2015-2016 Philip Ross.
    Licence: MIT
    """

    name = "bzip2"
    version = "1.0.8"
    url = "https://sourceware.org/pub/bzip2/bzip2-1.0.8.tar.gz"
    install_paths = {
        "x86": {
            "license/bzip2": ["LICENSE"],
            "include": ["bzlib.h"],
            "lib": ["libbz2.dll", "libbz2.lib"],
        },
        "x64": {
            "license/bzip2": ["LICENSE"],
            "include": ["bzlib.h"],
            "lib": ["libbz2.dll", "libbz2.lib"],
        },
    }
    platform = ["Windows"]
    dependencies = []
    required_tools = ["visualstudio==2017"]
    build_script = {
        "x86": {
            "make" : """
                CALL vcvarsall.bat x86 -vcvars_ver=14.1
                CALL nmake -f makefile.msc all
            """
        },
        "x64": {
            "make" : """
                CALL vcvarsall.bat amd64 -vcvars_ver=14.1
                CALL nmake -f makefile.msc all
            """
        },
    }
