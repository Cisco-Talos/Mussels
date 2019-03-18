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
import shutil

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
            "x86" : ["pthread.h"],
            "x64" : ["pthread.h"],
        },
        "lib" : {
            "x86" : ["pthreadVC1.dll"],
            "x64" : ["pthreadVC1.dll"],
        },
    }
    dependencies = []
    toolchain = ["vs2015"]
    build_cmds = {
        'x86' : [
            'vcvarsall.bat x86',
            'nmake clean VC'
        ],
        'x64' : [
            'vcvarsall.bat amd64',
            'nmake clean VC'
        ]
    }

    def build(self) -> bool:
        '''
        Override the original build() function to replace some text in pthread.h
        because it is a buggy peice of crap.
        '''
        cwd = os.getcwd()
        os.chdir(self.build_path)

        shutil.copyfile("pthread.h", "pthread.h.bak")
        with open("pthread.h.bak", "r") as pthread_h_bak:
            with open("pthread.h", "w") as pthread_h:
                for line in pthread_h_bak:
                    if "#include <time.h>" in line:
                        pthread_h.write("#define HAVE_STRUCT_TIMESPEC\n")
                    pthread_h.write(line)
        
        os.chdir(cwd)
        return super().build()
