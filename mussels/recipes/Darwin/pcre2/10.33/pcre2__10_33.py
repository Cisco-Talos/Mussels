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
    Recipe to build pcre2.
    """

    name = "pcre2"
    version = "10.33"
    url = "https://ftp.pcre.org/pub/pcre/pcre2-10.33.zip"
    install_paths = {"host": {"license/pcre2": ["COPYING"]}}
    platform = ["Darwin"]
    dependencies = ["bzip2", "zlib"]
    required_tools = ["cmake", "clang"]
    build_script = {
        "host": {
            "configure": """
                chmod +x ./configure ./install-sh
                ./configure --prefix="{install}/{target}" --disable-dependency-tracking
            """,
            "make": """
                make
            """,
            "install": """
                make install
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/lib/libpcre2-8.dylib"
            """,
        }
    }