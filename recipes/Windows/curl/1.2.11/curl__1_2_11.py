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
    Recipe to build libcurl.
    '''
    name = "curl"
    version = "7.64.0"
    url = "https://curl.haxx.se/download/curl-7.64.0.zip"
    install_paths = {
        "x86" : {
            "include" : [os.path.join("include", "curl")],
            "lib" : [
                os.path.join("lib", "Release", "libcurl.dll"),
                os.path.join("lib", "Release", "libcurl_imp.lib"),
            ],
        },
        "x64" : {
            "include" : [os.path.join("include", "curl")],
            "lib" : [
                os.path.join("lib", "Release", "libcurl.dll"),
                os.path.join("lib", "Release", "libcurl_imp.lib"),
            ],
        },
    }
    dependencies = ["openssl", "nghttp2>=1.0.0", "libssh2", "zlib"]
    required_tools = ["cmake", "visualstudio>=2017"]
    build_script = {
        'x86' : '''
            CALL cmake.exe -G "Visual Studio 15 2017" \
                -DCMAKE_CONFIGURATION_TYPES=Release \
                -DBUILD_SHARED_LIBS=ON \
                -DCMAKE_USE_OPENSSL=ON \
                -DOPENSSL_INCLUDE_DIR="{includes}" \
                -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                -DZLIB_INCLUDE_DIR="{includes}" \
                -DZLIB_LIBRARY_RELEASE="{libs}/zlib.lib" \
                -DLIBSSH2_INCLUDE_DIR="{includes}" \
                -DLIBSSH2_LIBRARY="{libs}/libssh2.lib" \
                -DUSE_NGHTTP2=ON \
                -DNGHTTP2_INCLUDE_DIR="{includes}" \
                -DNGHTTP2_LIBRARY="{libs}/nghttp2.lib"
            CALL cmake.exe --build . --config Release
        ''',
        'x64' : '''
            CALL cmake.exe -G "Visual Studio 15 2017 Win64" \
                -DCMAKE_CONFIGURATION_TYPES=Release \
                -DBUILD_SHARED_LIBS=ON \
                -DCMAKE_USE_OPENSSL=ON \
                -DOPENSSL_INCLUDE_DIR="{includes}" \
                -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                -DZLIB_INCLUDE_DIR="{includes}" \
                -DZLIB_LIBRARY_RELEASE="{libs}/zlib.lib" \
                -DLIBSSH2_INCLUDE_DIR="{includes}" \
                -DLIBSSH2_LIBRARY="{libs}/libssh2.lib" \
                -DUSE_NGHTTP2=ON \
                -DNGHTTP2_INCLUDE_DIR="{includes}" \
                -DNGHTTP2_LIBRARY="{libs}/nghttp2.lib"
            CALL cmake.exe --build . --config Release
        ''',
    }
