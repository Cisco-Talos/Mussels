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
    Recipe to build libssh2.
    """

    name = "libssh2"
    version = "1.8.1"
    url = "https://www.libssh2.org/download/libssh2-1.8.1.tar.gz"
    install_paths = {
        "x86": {
            "license/libssh2": ["COPYING"],
            "include": [
                os.path.join("include", "libssh2.h"),
                os.path.join("include", "libssh2_publickey.h"),
                os.path.join("include", "libssh2_sftp.h"),
            ],
            "lib": [
                os.path.join("src", "Release", "libssh2.dll"),
                os.path.join("src", "Release", "libssh2.lib"),
            ],
        },
        "x64": {
            "license/libssh2": ["COPYING"],
            "include": [
                os.path.join("include", "libssh2.h"),
                os.path.join("include", "libssh2_publickey.h"),
                os.path.join("include", "libssh2_sftp.h"),
            ],
            "lib": [
                os.path.join("src", "Release", "libssh2.dll"),
                os.path.join("src", "Release", "libssh2.lib"),
            ],
        },
    }
    platform = ["Windows"]
    dependencies = ["openssl>=1.1.0", "zlib"]
    required_tools = ["cmake", "visualstudio>=2017"]
    build_script = {
        "x86": """
        """,
        "x64": """
        """,
    }
    build_script = {
        "x86": {
            "configure" : """
                CALL cmake.exe -G "Visual Studio 15 2017" -T v141 \
                    -DCRYPTO_BACKEND=OpenSSL \
                    -DBUILD_SHARED_LIBS=ON \
                    -DOPENSSL_INCLUDE_DIR="{includes}" \
                    -DDLL_LIBEAY32="{libs}/libcrypto-1_1.dll" \
                    -DDLL_SSLEAY32="{libs}/libssl-1_1.dll" \
                    -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                    -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                    -DENABLE_ZLIB_COMPRESSION=ON \
                    -DZLIB_INCLUDE_DIR="{includes}" \
                    -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib"
            """,
            "make" : """
                CALL cmake.exe --build . --config Release
            """
        },
        "x64": {
            "configure" : """
                CALL cmake.exe -G "Visual Studio 15 2017 Win64" -T v141 \
                    -DCRYPTO_BACKEND=OpenSSL \
                    -DBUILD_SHARED_LIBS=ON \
                    -DOPENSSL_INCLUDE_DIR="{includes}" \
                    -DDLL_LIBEAY32="{libs}/libcrypto-1_1-x64.dll" \
                    -DDLL_SSLEAY32="{libs}/libssl-1_1-x64.dll" \
                    -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                    -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                    -DENABLE_ZLIB_COMPRESSION=ON \
                    -DZLIB_INCLUDE_DIR="{includes}" \
                    -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib"
            """,
            "make" : """
                CALL cmake.exe --build . --config Release
            """
        },
    }
