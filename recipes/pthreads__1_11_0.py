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
    Recipe to build pthreads-win32.
    '''
    name = "pthreads"
    version = "1.11.0"
    url = "ftp://sourceware.org/pub/pthreads-win32/pthreads-w32-1-11-0-release.tar.gz"
    install_paths = {
        "include" : {
            "x86" : "include",
            "x64" : "include",
        },
        "lib" : {
            "x86" : [os.path.join("win32", "pthreads.dll"),],
            "x64" : [os.path.join("x64", "pthreads.dll"),],
        },
    }
    dependencies = []
