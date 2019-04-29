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

from recipes.recipe import BaseRecipe

class Recipe(BaseRecipe):
    '''
    Recipe to build bzip2.
    Patches shamelessly copied from: https://github.com/philr/bzip2-windows
    Copyright (c) 2015-2016 Philip Ross.
    Licence: MIT
    '''
    name = "bzip2"
    version = "1.0.6"
    url = "https://downloads.sourceforge.net/project/bzip2/bzip2-1.0.6.tar.gz"
    patches = os.path.join(os.path.split(os.path.abspath(__file__))[0], "patches")
    install_paths = {
        "x86" : {
            "include" : ["bzlib.h"],
            "lib" : [
                os.path.join("libbz2.dll"),
                os.path.join("libbz2.lib"),
            ],
        },
        "x64" : {
            "include" : ["bzlib.h"],
            "lib" : [
                os.path.join("libbz2.dll"),
                os.path.join("libbz2.lib"),
            ],
        },
    }
    dependencies = []
    required_tools = ["visualstudio>=2017"]
    build_script = {
        'x86' : '''
            CALL vcvarsall.bat x86
            CALL nmake -f makefile.msc all
        ''',
        'x64' : '''
            CALL vcvarsall.bat amd64
            CALL nmake -f makefile.msc all
        ''',
    }
