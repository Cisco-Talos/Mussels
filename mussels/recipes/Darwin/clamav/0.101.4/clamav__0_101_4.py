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

from mussels.recipe import BaseRecipe


class Recipe(BaseRecipe):
    """
    Recipe to build clamav.
    """

    name = "clamav"
    version = "0.101.4"
    url = "https://www.clamav.net/downloads/production/clamav-0.101.4.tar.gz"
    install_paths = {
        "host": {
            "license/clamav": ["COPYING*"],
            "etc": ["etc/clamd.conf.sample", "etc/freshclam.conf.sample"],
            "share/clamav": ["database/main.cvd", "database/daily.cvd"],
        }
    }
    platform = ["Darwin"]
    dependencies = ["curl", "json_c", "libxml2", "openssl", "pcre2", "bzip2-1.0.7"]
    required_tools = ["make", "clang"]
    build_script = {
        "host": {
            "configure": """
                chmod +x ./configure ./config/install-sh
                ./configure \
                    --with-libcurl={install}/{target} \
                    --with-libjson={install}/{target} \
                    --with-xml={install}/{target} \
                    --with-openssl={install}/{target} \
                    --with-pcre={install}/{target} \
                    --with-zlib={install}/{target} \
                    --with-libbz2-prefix={install}/{target} \
                    --prefix="{install}/{target}" \
                    --with-systemdsystemunitdir=no
            """,
            "make": """
                make
            """,
            "install": """
                make install
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/bin/clambc"
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/bin/clamconf"
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/bin/clamdscan"
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/bin/clamscan"
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/bin/clamsubmit"
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/bin/freshclam"
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/bin/sigtool"
                install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/sbin/clamd"
            """,
        }
    }
