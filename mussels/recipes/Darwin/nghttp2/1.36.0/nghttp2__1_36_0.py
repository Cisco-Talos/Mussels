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
    Recipe to build nghttp2.
    """

    name = "nghttp2"
    version = "1.36.0"
    url = "https://github.com/nghttp2/nghttp2/archive/v1.36.0.zip"
    archive_name_change = ("v", "nghttp2-")
    install_paths = {
        "host": {
            "include": [os.path.join("lib", "includes", "nghttp2")],
            "lib": [
                os.path.join("lib", "libnghttp2.14.17.1.dylib"),
                os.path.join("lib", "libnghttp2.14.dylib"),
                os.path.join("lib", "libnghttp2.dylib"),
                os.path.join("lib", "libnghttp2.a"),
            ],
        }
    }
    dependencies = ["openssl>=1.0.1", "zlib>=1.2.3", "libxml2>=2.9.9"]
    required_tools = ["cmake", "clang"]
    build_script = {
        "host": """
            cmake . \
                -DCMAKE_CONFIGURATION_TYPES=Release \
                -DBUILD_SHARED_LIBS=ON \
                -DOPENSSL_ROOT_DIR="{install}" \
                -DOPENSSL_INCLUDE_DIR="{includes}" \
                -DOPENSSL_LIBRARIES="{libs}" \
                -DOPENSSL_CRYPTO_LIBRARY="{libs}/libcrypto.1.1.dylib" \
                -DOPENSSL_SSL_LIBRARY="{libs}/libssl.1.1.dylib" \
                -DLIBXML2_INCLUDE_DIR="{includes}" \
                -DLIBXML2_LIBRARY="{libs}/libxml2.dylib" \
                -DZLIB_ROOT="{includes}" \
                -DZLIB_LIBRARY="{libs}/libz.a"
            cmake --build . --config Release
        """
    }
