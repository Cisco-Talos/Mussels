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
    Recipe to build libssl.
    """

    name = "openssl"
    version = "1.1.1c"
    url = "https://www.openssl.org/source/openssl-1.1.1c.tar.gz"
    install_paths = {
        "x86": {
            "include": [os.path.join("include", "openssl")],
            "lib": [
                os.path.join("libssl-1_1.dll"),
                os.path.join("libssl.lib"),
                os.path.join("libcrypto-1_1.dll"),
                os.path.join("libcrypto.lib"),
            ],
        },
        "x64": {
            "include": [os.path.join("include", "openssl")],
            "lib": [
                os.path.join("libssl-1_1-x64.dll"),
                os.path.join("libssl.lib"),
                os.path.join("libcrypto-1_1-x64.dll"),
                os.path.join("libcrypto.lib"),
            ],
        },
    }
    dependencies = ["zlib"]
    required_tools = ["nasm", "perl", "visualstudio>=2017"]
    build_script = {
        "x86": """
            CALL vcvarsall.bat x86 -vcvars_ver=14.1
            CALL perl Configure VC-WIN32 zlib --with-zlib-include="{includes}" --with-zlib-lib="{libs}/zlibstatic.lib"
            CALL nmake
        """,
        "x64": """
            CALL vcvarsall.bat amd64 -vcvars_ver=14.1
            CALL perl Configure VC-WIN64A zlib --with-zlib-include="{includes}" --with-zlib-lib="{libs}/zlibstatic.lib"
            CALL nmake
        """,
    }
