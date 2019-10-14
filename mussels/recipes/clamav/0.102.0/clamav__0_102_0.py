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

    mussels_version = "0.1"

    name = "clamav"
    version = "0.102.0"
    is_collection = False
    url = "https://www.clamav.net/downloads/production/clamav-0.102.0.tar.gz"
    platforms = {
        "Windows": {
            "x86": {
                # "patches": "patches_windows", # (optional) Apply a patch set in this directory before the "configure" build step
                "install_paths": {
                    "license/clamav": ["COPYING*"],
                    "include": [
                        os.path.join("libclamav", "clamav.h"),
                        os.path.join("win32", "clamav-types.h"),
                    ],
                    "lib": [
                        os.path.join("win32", "Win32", "Release", "libclamav.dll"),
                        os.path.join("win32", "Win32", "Release", "libclamav.lib"),
                        os.path.join("win32", "Win32", "Release", "libfreshclam.dll"),
                        os.path.join("win32", "Win32", "Release", "libfreshclam.lib"),
                        os.path.join("win32", "Win32", "Release", "libclamunrar.dll"),
                        os.path.join("win32", "Win32", "Release", "libclamunrar.lib"),
                        os.path.join(
                            "win32", "Win32", "Release", "libclamunrar_iface.dll"
                        ),
                        os.path.join(
                            "win32", "Win32", "Release", "libclamunrar_iface.lib"
                        ),
                        os.path.join("win32", "Win32", "Release", "mspack.dll"),
                        os.path.join("win32", "Win32", "Release", "mspack.lib"),
                    ],
                    "bin": [
                        os.path.join("win32", "Win32", "Release", "clambc.exe"),
                        os.path.join("win32", "Win32", "Release", "clamconf.exe"),
                        os.path.join("win32", "Win32", "Release", "clamd.exe"),
                        os.path.join("win32", "Win32", "Release", "clamdscan.exe"),
                        os.path.join("win32", "Win32", "Release", "clamscan.exe"),
                        os.path.join("win32", "Win32", "Release", "clamsubmit.exe"),
                        os.path.join("win32", "Win32", "Release", "freshclam.exe"),
                        os.path.join("win32", "Win32", "Release", "sigtool.exe"),
                    ],
                    "etc": [
                        os.path.join("win32", "conf_examples", "clamd.conf.sample"),
                        os.path.join("win32", "conf_examples", "freshclam.conf.sample"),
                    ],
                },
                "dependencies": [
                    "curl",
                    "json_c",
                    "pthreads",
                    "libxml2",
                    "openssl",
                    "pcre2",
                    "bzip2-1.0.8",
                ],
                "required_tools": ["visualstudio==2017"],
                "build_script": {
                    "configure": """
                            robocopy "{install}" "%CD%\\clamdeps" /MIR
                            rename "%CD%\\clamdeps\\x86" "Win32"
                            call vcvarsall.bat x86 -vcvars_ver=14.1
                            setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                            cd win32
                            call configure.bat
                        """,
                    "make": """
                            call vcvarsall.bat x86 -vcvars_ver=14.1
                            setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                            cd win32
                            call devenv ClamAV.sln /Clean "Release|Win32" /useenv /ProjectConfig "Release|Win32"
                            set CL=/DWINDOWS_IGNORE_PACKING_MISMATCH && call devenv ClamAV.sln /Rebuild "Release|Win32" /useenv /ProjectConfig "Release|Win32"
                        """,
                },
            },
            "x64": {
                # "patches": "patches_windows",
                "install_paths": {
                    "license/clamav": ["COPYING*"],
                    "include": [
                        os.path.join("libclamav", "clamav.h"),
                        os.path.join("win32", "clamav-types.h"),
                    ],
                    "lib": [
                        os.path.join("win32", "x64", "Release", "libclamav.dll"),
                        os.path.join("win32", "x64", "Release", "libclamav.lib"),
                        os.path.join("win32", "x64", "Release", "libfreshclam.dll"),
                        os.path.join("win32", "x64", "Release", "libfreshclam.lib"),
                        os.path.join("win32", "x64", "Release", "libclamunrar.dll"),
                        os.path.join("win32", "x64", "Release", "libclamunrar.lib"),
                        os.path.join(
                            "win32", "x64", "Release", "libclamunrar_iface.dll"
                        ),
                        os.path.join(
                            "win32", "x64", "Release", "libclamunrar_iface.lib"
                        ),
                        os.path.join("win32", "x64", "Release", "mspack.dll"),
                        os.path.join("win32", "x64", "Release", "mspack.lib"),
                    ],
                    "bin": [
                        os.path.join("win32", "x64", "Release", "clambc.exe"),
                        os.path.join("win32", "x64", "Release", "clamconf.exe"),
                        os.path.join("win32", "x64", "Release", "clamd.exe"),
                        os.path.join("win32", "x64", "Release", "clamdscan.exe"),
                        os.path.join("win32", "x64", "Release", "clamscan.exe"),
                        os.path.join("win32", "x64", "Release", "clamsubmit.exe"),
                        os.path.join("win32", "x64", "Release", "freshclam.exe"),
                        os.path.join("win32", "x64", "Release", "sigtool.exe"),
                    ],
                    "etc": [
                        os.path.join("win32", "conf_examples", "clamd.conf.sample"),
                        os.path.join("win32", "conf_examples", "freshclam.conf.sample"),
                    ],
                },
                "dependencies": [
                    "curl",
                    "json_c",
                    "pthreads",
                    "libxml2",
                    "openssl",
                    "pcre2",
                    "bzip2-1.0.8",
                ],
                "required_tools": ["visualstudio==2017"],
                "build_script": {
                    "configure": """
                            robocopy "{install}" "%CD%\\clamdeps" /MIR
                            call vcvarsall.bat x64 -vcvars_ver=14.1
                            setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                            cd win32
                            call configure.bat
                        """,
                    "make": """
                            call vcvarsall.bat x64 -vcvars_ver=14.1
                            setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                            cd win32
                            call devenv ClamAV.sln /Clean "Release|x64" /useenv /ProjectConfig "Release|x64"
                            set CL=/DWINDOWS_IGNORE_PACKING_MISMATCH && call devenv ClamAV.sln /Rebuild "Release|x64" /useenv /ProjectConfig "Release|x64"
                        """,
                },
            },
        },
        "Darwin": {
            "host": {
                "install_paths": {
                    "license/clamav": ["COPYING*"],
                    "etc": ["etc/clamd.conf.sample", "etc/freshclam.conf.sample"],
                    "share/clamav": ["database/main.cvd", "database/daily.cvd"],
                },
                "dependencies": [
                    "curl",
                    "json_c",
                    "libxml2",
                    "openssl",
                    "pcre2",
                    "bzip2-1.0.7",
                ],
                "required_tools": ["make", "clang"],
                "build_script": {
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
                                --enable-llvm --with-system-llvm=no \
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
                },
            }
        },
    }
