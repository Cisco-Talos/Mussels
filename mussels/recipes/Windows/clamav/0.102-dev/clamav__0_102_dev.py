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
    version = "0.102.0"
    url = "https://github.com/Cisco-Talos/clamav-devel/archive/dev/0.102.zip"
    archive_name_change = ("0.102", "clamav-devel-dev-0.102")
    install_paths = {
        "x86": {
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
                os.path.join("win32", "Win32", "Release", "libclamunrar_iface.dll"),
                os.path.join("win32", "Win32", "Release", "libclamunrar_iface.lib"),
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
        "x64": {
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
                os.path.join("win32", "x64", "Release", "libclamunrar_iface.dll"),
                os.path.join("win32", "x64", "Release", "libclamunrar_iface.lib"),
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
    }
    platform = ["Windows"]
    dependencies = [
        "curl",
        "json_c",
        "pthreads",
        "libxml2",
        "openssl",
        "pcre2",
        "bzip2-1.0.8",
    ]
    required_tools = ["visualstudio>=2017"]
    build_script = {
        "x86": {
            "configure" : """
                robocopy "{install}" "%CD%\\clamdeps" /MIR
                rename "%CD%\\clamdeps\\x86" "Win32"
                call vcvarsall.bat x86 -vcvars_ver=14.1
                setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                cd win32
                call configure.bat
            """,
            "make" : """
                call vcvarsall.bat x86 -vcvars_ver=14.1
                setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                cd win32
                call devenv ClamAV.sln /Clean "Release|Win32" /useenv /ProjectConfig "Release|Win32"
                set CL=/DWINDOWS_IGNORE_PACKING_MISMATCH && call devenv ClamAV.sln /Rebuild "Release|Win32" /useenv /ProjectConfig "Release|Win32"
            """
        },
        "x64": {
            "configure" : """
                robocopy "{install}" "%CD%\\clamdeps" /MIR
                call vcvarsall.bat x64 -vcvars_ver=14.1
                setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                cd win32
                call configure.bat
            """,
            "make" : """
                call vcvarsall.bat x64 -vcvars_ver=14.1
                setx CLAM_DEPENDENCIES "%CD%\\clamdeps"
                cd win32
                call devenv ClamAV.sln /Clean "Release|x64" /useenv /ProjectConfig "Release|x64"
                set CL=/DWINDOWS_IGNORE_PACKING_MISMATCH && call devenv ClamAV.sln /Rebuild "Release|x64" /useenv /ProjectConfig "Release|x64"
            """
        },
    }
