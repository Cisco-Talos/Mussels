'''
Copyright (C)2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

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
    Recipe to build libssl.
    '''
    name = "openssl"
    version = "1.1.1b"
    url = "https://www.openssl.org/source/openssl-1.1.1b.tar.gz"
    install_paths = {
        "include" : {
            "x86" : [
                os.path.join("include", "openssl"),
            ],
            "x64" : [
                os.path.join("include", "openssl"),
            ],
        },
        "lib" : {
            "x86" : [
                os.path.join("libssl-1_1.dll"), 
                os.path.join("libcrypto-1_1.dll"),
            ],
            "x64" : [
                os.path.join("libssl-1_1-x64.dll"), 
                os.path.join("libcrypto-1_1-x64.dll"),
            ],
        },
    }
    dependencies = []
    build_cmds = {
        'x86' : [
            f'vcvarsall.bat x86',
            f'perl Configure VC-WIN32',
            f'nmake',
        ],
        'x64' : [
            f'vcvarsall.bat amd64',
            f'perl Configure VC-WIN64A',
            f'nmake',
        ]
    }
