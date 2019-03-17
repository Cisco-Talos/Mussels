'''
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
'''

import os

from recipes.builder import Builder

class Recipe(Builder):
    '''
    Recipe to build zlib.
    '''
    name = "zlib"
    version = "1.2.11"
    url = "https://www.zlib.net/zlib-1.2.11.tar.gz"
    install_paths = {
        "include" : {
            "x86" : ["zlib.h"],
            "x64" : ["zlib.h"],
        },
        "lib" : {
            "x86" : [os.path.join("Release", "zlib.dll"),],
            "x64" : [os.path.join("Release" ,"zlib.dll"),],
        },
    }
    dependencies = []
    toolchain = ["cmake", "vs2017"]
    build_cmds = {
        'x86' : [
            f'cmake.exe -G "Visual Studio 15 2017"',
            f'cmake.exe --build . --config Release',
        ],
        'x64' : [
            f'cmake.exe -G "Visual Studio 15 2017 Win64"',
            f'cmake.exe --build . --config Release',
        ]
    }

