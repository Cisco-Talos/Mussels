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

    mussels_version = "0.1"

    name = "libssh2"
    version = "1.9.0"
    url = "https://www.libssh2.org/download/libssh2-1.9.0.tar.gz"
    platforms = {
        "Windows": {
            "x86": {
                # "patches": "patches_windows", # (optional) Apply a patch set in this directory before the "configure" build step
                "install_paths": {
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
                "dependencies": ["openssl>=1.1.0", "zlib"],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
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
                                -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
                                -DBUILD_TESTING=OFF
                        """,
                    "make": """
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
            "x64": {
                # "patches": "patches_windows",
                "install_paths": {
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
                "dependencies": ["openssl>=1.1.0", "zlib"],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
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
                                -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
                                -DBUILD_TESTING=OFF
                        """,
                    "make": """
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
        },
        "Darwin": {
            "host": {
                "install_paths": {"license/libssh2": ["COPYING"]},
                "dependencies": ["openssl>=1.1.0", "zlib"],
                "required_tools": ["cmake", "make", "clang"],
                "build_script": {
                    "configure": """
                            cmake . \
                                -DCRYPTO_BACKEND=OpenSSL \
                                -DBUILD_SHARED_LIBS=ON \
                                -DOPENSSL_INCLUDE_DIR="{includes}" \
                                -DOPENSSL_LIBRARIES="{libs}" \
                                -DOPENSSL_CRYPTO_LIBRARY="{libs}/libcrypto.1.1.dylib" \
                                -DOPENSSL_SSL_LIBRARY="{libs}/libssl.1.1.dylib" \
                                -DENABLE_ZLIB_COMPRESSION=ON \
                                -DZLIB_INCLUDE_DIR="{includes}" \
                                -DZLIB_LIBRARY_RELEASE="{libs}/libz.a" \
                                -DCMAKE_INSTALL_PREFIX="{install}/{target}" \
                                -DBUILD_TESTING=OFF
                        """,
                    "make": """
                            cmake --build . --config Release
                        """,
                    "install": """
                            make install
                            install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/lib/libssh2.dylib"
                        """,
                },
            }
        },
    }
