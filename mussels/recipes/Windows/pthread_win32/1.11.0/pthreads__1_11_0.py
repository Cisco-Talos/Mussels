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
import shutil

from mussels.recipe import BaseRecipe


class Recipe(BaseRecipe):
    """
    Recipe to build pthreads-win32.
    """

    name = "pthreads"
    version = "1.11.0"
    url = "ftp://sourceware.org/pub/pthreads-win32/pthreads-w32-1-11-0-release.tar.gz"
    patches = os.path.join(os.path.split(os.path.abspath(__file__))[0], "patches")
    install_paths = {
        "x86": {
            "include": ["pthread.h", "sched.h"],
            "lib": ["pthreadVC1.dll", "pthreadVC1.lib"],
        },
        "x64": {
            "include": ["pthread.h", "sched.h"],
            "lib": ["pthreadVC1.dll", "pthreadVC1.lib"],
        },
    }
    dependencies = []
    required_tools = ["visualstudio>=2017"]
    build_script = {
        "x86": """
            CALL vcvarsall.bat x86 -vcvars_ver=14.1
            CALL nmake clean VC
        """,
        "x64": """
            CALL vcvarsall.bat amd64 -vcvars_ver=14.1
            CALL nmake clean VC
        """,
    }
