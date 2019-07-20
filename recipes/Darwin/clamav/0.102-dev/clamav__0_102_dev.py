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
import shutil

from recipes.recipe import BaseRecipe


class Recipe(BaseRecipe):
    """
    Recipe to build clamav.
    """

    name = "clamav"
    version = "0.102"
    url = "https://github.com/Cisco-Talos/clamav-devel/archive/dev/0.102.zip"
    archive_name_change = ("0.102", "clamav-devel-dev-0.102")
    install_paths = {
        "host": {
            "include": [
                os.path.join("libclamav", "clamav.h"),
                os.path.join("clamav-types.h"),
            ],
            "lib": [
                os.path.join("libclamav", "libclamav.dylib"),
                os.path.join("libfreshclam", "libfreshclam.dylib"),
                os.path.join("libclamunrar", "libclamunrar.dylib"),
                os.path.join("libclamunrar_iface", "libclamunrar_iface.dylib"),
                os.path.join("mspack", "mspack.dylib"),
            ],
            "bin": [
                os.path.join("clambc", "clambc"),
                os.path.join("clamconf", "clamconf"),
                os.path.join("clamd", "clamd"),
                os.path.join("clamdscan", "clamdscan"),
                os.path.join("clamscan", "clamscan"),
                os.path.join("clamsubmit", "clamsubmit"),
                os.path.join("freshclam", "freshclam"),
                os.path.join("sigtool", "sigtool"),
            ],
            "etc": [
                os.path.join("etc", "clamd.conf.sample"),
                os.path.join("etc", "freshclam.conf.sample"),
            ],
        }
    }
    dependencies = ["curl", "json_c", "libxml2", "openssl", "pcre2", "bzip2"]
    required_tools = ["make", "clang"]
    build_script = {
        "host": """
            chmod +x ./configure
            ./configure --with-libcurl={install}/host --with-libjson={install}/host --with-xml={install}/host --with-openssl={install}/host --with-pcre={install}/host --with-libbz2-prefix={install}/host --enable-llvm --with-system-llvm=no
            make
        """
    }
