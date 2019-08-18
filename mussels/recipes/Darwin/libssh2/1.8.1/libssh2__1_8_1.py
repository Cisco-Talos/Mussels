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
        "host": {
            "include": [
                os.path.join("include", "libssh2.h"),
                os.path.join("include", "libssh2_publickey.h"),
                os.path.join("include", "libssh2_sftp.h"),
            ],
            "lib": [
                os.path.join("src", "libssh2.1.0.1.dylib"),
                os.path.join("src", "libssh2.1.dylib"),
                os.path.join("src", "libssh2.dylib"),
            ],
        }
    }
    platform = ["Darwin"]
    dependencies = ["openssl>=1.1.0", "zlib"]
    required_tools = ["cmake", "clang"]
    build_script = {
        "host": """
            cmake . \
                -DCRYPTO_BACKEND=OpenSSL \
                -DBUILD_SHARED_LIBS=ON \
                -DOPENSSL_INCLUDE_DIR="{includes}" \
                -DOPENSSL_LIBRARIES="{libs}" \
                -DOPENSSL_CRYPTO_LIBRARY="{libs}/libcrypto.1.1.dylib" \
                -DOPENSSL_SSL_LIBRARY="{libs}/libssl.1.1.dylib" \
                -DENABLE_ZLIB_COMPRESSION=ON \
                -DZLIB_INCLUDE_DIR="{includes}" \
                -DZLIB_LIBRARY_RELEASE="{libs}/libz.a"
            cmake --build . --config Release
        """
    }
