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

from recipes.recipe import BaseRecipe


class Recipe(BaseRecipe):
    """
    Recipe to build libcurl.
    """

    name = "curl"
    version = "7.64.0"
    url = "https://curl.haxx.se/download/curl-7.64.0.zip"
    install_paths = {
        "host": {
            "include": [os.path.join("include", "curl")],
            "lib": [
                os.path.join("lib", "libcurl.dylib"),
            ],
        },
    }
    dependencies = ["openssl", "nghttp2>=1.0.0", "libssh2", "zlib"]
    required_tools = ["cmake", "clang"]
    build_script = {
        "host": """
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
                -DNGHTTP2_LIBRARY="{libs}/libnghttp2.dylib"
            cmake --build . --config Release
        """,
    }
