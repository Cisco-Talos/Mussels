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
    """

    name = "bzip2-dev"
    version = "1.1.0"
    url = "https://gitlab.com/federicomenaquintero/bzip2/-/archive/master/bzip2-master.tar.gz"
    install_paths = {
        "host": {
            "include": ["bzlib.h"],
            "lib": [
                os.path.join("libbz2.1.1.0.dylib"),
                os.path.join("libbz2.1.dylib"),
                os.path.join("libbz2.a"),
            ],
            "bin": [
                os.path.join("bunzip2"),
                os.path.join("bzcat"),
                os.path.join("bzcmp"),
                os.path.join("bzdiff"),
                os.path.join("bzegrep"),
                os.path.join("bzfgrep"),
                os.path.join("bzip2"),
                os.path.join("bzip2recover"),
                os.path.join("bzless"),
                os.path.join("bzmore"),
            ],
        }
    }
    platform = ["Darwin"]
    dependencies = []
    required_tools = ["cmake", "clang"]
    build_script = {
        "host": """
            cmake .
            cmake --build . --config Release
        """
    }
