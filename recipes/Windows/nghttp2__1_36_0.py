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
    Recipe to build nghttp2.
    '''
    name = "nghttp2"
    version = "1.36.0"
    url = "https://github.com/nghttp2/nghttp2/archive/v1.36.0.zip"
    archive_name_change = ("v", "nghttp2-")
    install_paths = {
        "x86" : {
            "include" : [os.path.join("lib", "includes", "nghttp2")],
            "lib" : [
                os.path.join("lib", "Release", "nghttp2.dll"),
                os.path.join("lib", "Release", "nghttp2.lib"),
            ],
        },
        "x64" : {
            "include" : [os.path.join("lib", "includes", "nghttp2")],
            "lib" : [
                os.path.join("lib", "Release", "nghttp2.dll"),
                os.path.join("lib", "Release", "nghttp2.lib"),
            ],
        },
    }
    dependencies = ["openssl>=1.0.1", "zlib>=1.2.3"]
    toolchain = ["cmake", "vs2017"]
    build_script = {
        'x86' : '''
            CALL cmake.exe -G "Visual Studio 15 2017" \
                -DCMAKE_CONFIGURATION_TYPES=Release \
                -DBUILD_SHARED_LIBS=ON \
                -DOPENSSL_ROOT_DIR="{install}" \
                -DOPENSSL_INCLUDE_DIR="{includes}" \
                -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                -DZLIB_ROOT="{includes}" \
                -DZLIB_LIBRARY="{libs}/zlib.lib"
            CALL cmake.exe --build . --config Release
        ''',
        'x64' : '''
            CALL cmake.exe -G "Visual Studio 15 2017 Win64" \
                -DCMAKE_CONFIGURATION_TYPES=Release \
                -DBUILD_SHARED_LIBS=ON \
                -DOPENSSL_ROOT_DIR="{install}" \
                -DOPENSSL_INCLUDE_DIR="{includes}" \
                -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                -DZLIB_ROOT="{includes}" \
                -DZLIB_LIBRARY="{libs}/zlib.lib"
            CALL cmake.exe --build . --config Release
        ''',
    }