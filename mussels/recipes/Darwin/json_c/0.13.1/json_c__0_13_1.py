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
    Recipe to build json-c.
    Uses ./configure, make, because json-c's CMakeLists.txt for posix, particularly Mac, are bad.
    """

    name = "json_c"
    version = "0.13.1"
    url = "https://s3.amazonaws.com/json-c_releases/releases/json-c-0.13.1.tar.gz"
    install_paths = {
        "host": {
            "include/json-c": [
                os.path.join("arraylist.h"),
                os.path.join("bits.h"),
                os.path.join("debug.h"),
                os.path.join("json.h"),
                os.path.join("json_c_version.h"),
                os.path.join("json_inttypes.h"),
                os.path.join("json_object.h"),
                os.path.join("json_object_iterator.h"),
                os.path.join("json_pointer.h"),
                os.path.join("json_tokener.h"),
                os.path.join("json_util.h"),
                os.path.join("json_visit.h"),
                os.path.join("linkhash.h"),
                os.path.join("printbuf.h"),
                os.path.join("json_config.h"),
            ],
            "lib": [
                os.path.join(".libs", "libjson-c.4.dylib"),
                os.path.join(".libs", "libjson-c.dylib"),
                os.path.join(".libs", "libjson-c.a"),
            ],
        }
    }
    platform = ["Darwin"]
    dependencies = []
    required_tools = ["make", "clang"]
    build_script = {
        "host": """
            ./configure
            make
        """
    }
