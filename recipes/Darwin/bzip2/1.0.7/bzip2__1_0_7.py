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
    '''
    name = "bzip2"
    version = "1.0.7"
    url = "https://sourceware.org/pub/bzip2/bzip2-1.0.7.tar.gz"
    install_paths = {
        "host" : {
            "include" : ["install/include/bzlib.h"],
            "lib" : [
                os.path.join("install/lib/libbz2.a"),
            ],
            "bin" : [
                os.path.join("install/bin/bunzip2"),
                os.path.join("install/bin/bzcat"),
                os.path.join("install/bin/bzcmp"),
                os.path.join("install/bin/bzdiff"),
                os.path.join("install/bin/bzegrep"),
                os.path.join("install/bin/bzfgrep"),
                os.path.join("install/bin/bzip2"),
                os.path.join("install/bin/bzip2recover"),
                os.path.join("install/bin/bzless"),
                os.path.join("install/bin/bzmore"),
            ],
        },
    }
    dependencies = []
    required_tools = ["make", "clang"]
    build_script = {
        'host' : '''
            ./configure
            make
            make install PREFIX=`pwd`/install
        ''',
    }
