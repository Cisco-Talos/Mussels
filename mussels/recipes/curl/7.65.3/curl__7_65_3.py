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
    Recipe to build libcurl.
    """

    mussels_version = "0.1"

    name = "curl"
    version = "7.65.3"
    url = "https://curl.haxx.se/download/curl-7.65.3.zip"
    platforms = {
        "Windows": {
            "x86": {
                # "patches": "patches_windows", # (optional) Apply a patch set in this directory before the "configure" build step
                "install_paths": {
                    "license/curl": ["COPYING"],
                    "include": [os.path.join("include", "curl")],
                    "lib": [
                        os.path.join("lib", "Release", "libcurl.dll"),
                        os.path.join("lib", "Release", "libcurl_imp.lib"),
                    ],
                },
                "dependencies": ["openssl", "nghttp2>=1.0.0", "libssh2", "zlib"],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
                            CALL cmake.exe -G "Visual Studio 15 2017" -T v141 \
                                -DCMAKE_CONFIGURATION_TYPES=Release \
                                -DBUILD_SHARED_LIBS=ON \
                                -DCMAKE_USE_OPENSSL=ON \
                                -DOPENSSL_INCLUDE_DIR="{includes}" \
                                -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                                -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                                -DZLIB_INCLUDE_DIR="{includes}" \
                                -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
                                -DLIBSSH2_INCLUDE_DIR="{includes}" \
                                -DLIBSSH2_LIBRARY="{libs}/libssh2.lib" \
                                -DUSE_NGHTTP2=ON \
                                -DNGHTTP2_INCLUDE_DIR="{includes}" \
                                -DNGHTTP2_LIBRARY="{libs}/nghttp2.lib"
                        """,
                    "make": """
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
            "x64": {
                # "patches": "patches_windows",
                "install_paths": {
                    "license/curl": ["COPYING"],
                    "include": [os.path.join("include", "curl")],
                    "lib": [
                        os.path.join("lib", "Release", "libcurl.dll"),
                        os.path.join("lib", "Release", "libcurl_imp.lib"),
                    ],
                },
                "dependencies": ["openssl", "nghttp2>=1.0.0", "libssh2", "zlib"],
                "required_tools": ["cmake", "visualstudio>=2017"],
                "build_script": {
                    "configure": """
                            CALL cmake.exe -G "Visual Studio 15 2017 Win64" -T v141 \
                                -DCMAKE_CONFIGURATION_TYPES=Release \
                                -DBUILD_SHARED_LIBS=ON \
                                -DCMAKE_USE_OPENSSL=ON \
                                -DOPENSSL_INCLUDE_DIR="{includes}" \
                                -DLIB_EAY_RELEASE="{libs}/libcrypto.lib" \
                                -DSSL_EAY_RELEASE="{libs}/libssl.lib" \
                                -DZLIB_INCLUDE_DIR="{includes}" \
                                -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
                                -DLIBSSH2_INCLUDE_DIR="{includes}" \
                                -DLIBSSH2_LIBRARY="{libs}/libssh2.lib" \
                                -DUSE_NGHTTP2=ON \
                                -DNGHTTP2_INCLUDE_DIR="{includes}" \
                                -DNGHTTP2_LIBRARY="{libs}/nghttp2.lib"
                        """,
                    "make": """
                            CALL cmake.exe --build . --config Release
                        """,
                },
            },
        },
        "Darwin": {
            "host": {
                "install_paths": {"license/curl": ["COPYING"]},
                "dependencies": ["openssl", "nghttp2>=1.0.0", "libssh2", "zlib"],
                "required_tools": ["cmake", "clang"],
                "build_script": {
                    "configure": """
                            cmake . \
                                -DCMAKE_CONFIGURATION_TYPES=Release \
                                -DBUILD_SHARED_LIBS=ON \
                                -DCMAKE_USE_OPENSSL=ON \
                                -DOPENSSL_INCLUDE_DIR="{includes}" \
                                -DOPENSSL_LIBRARIES="{libs}" \
                                -DOPENSSL_CRYPTO_LIBRARY="{libs}/libcrypto.1.1.dylib" \
                                -DOPENSSL_SSL_LIBRARY="{libs}/libssl.1.1.dylib" \
                                -DZLIB_INCLUDE_DIR="{includes}" \
                                -DZLIB_LIBRARY_RELEASE="{libs}/libz.a" \
                                -DLIBSSH2_INCLUDE_DIR="{includes}" \
                                -DLIBSSH2_LIBRARY="{libs}/libssh2.dylib" \
                                -DUSE_NGHTTP2=ON \
                                -DNGHTTP2_INCLUDE_DIR="{includes}" \
                                -DNGHTTP2_LIBRARY="{libs}/libnghttp2.dylib" \
                                -DCMAKE_INSTALL_PREFIX="{install}/{target}"
                        """,
                    "make": """
                            cmake --build . --config Release
                        """,
                    "install": """
                            make install
                            install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/lib/libcurl.dylib"
                        """,
                },
            }
        },
    }
