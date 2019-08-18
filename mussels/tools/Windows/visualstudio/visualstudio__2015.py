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

from mussels.tool import BaseTool


class Tool(BaseTool):
    """
    Tool to detect Visual Studio 2015
    """

    name = "visualstudio"
    version = "2015"
    url = ""
    platform = ["Windows"]

    path_mods = {
        "system": {
            "x86": [
                os.path.join(
                    "C:\\", "Program Files (x86)", "Microsoft Visual Studio 14.0", "VC"
                )
            ],
            "x64": [
                os.path.join(
                    "C:\\", "Program Files (x86)", "Microsoft Visual Studio 14.0", "VC"
                )
            ],
        },
        "local": {
            "x86": [os.path.join("expected", "install", "path")],
            "x64": [os.path.join("expected", "install", "path")],
        },
    }

    file_checks = {
        "system": [
            os.path.join(
                "C:\\",
                "Program Files (x86)",
                "Microsoft Visual Studio 14.0",
                "VC",
                "vcvarsall.bat",
            )
        ],
        "local": [os.path.join("expected", "install", "path")],
    }

    # Install script to use in case the tool isn't already available and must be installed.
    install_script = """
    """

    def detect(self) -> bool:
        """
        rc.exe Hack to make openssl build with vs2015
        """
        super().detect()

        if self.installed == False:
            return False

        rc_path = "C:\\Program Files (x86)\\Windows Kits\\10\\bin\\"

        bin_ver = 0
        bin_file = ""
        for filename in os.listdir(rc_path):
            if filename.startswith("10.0."):
                ver = int(filename.split(".")[2])
                if ver > bin_ver:
                    bin_ver = ver
                    bin_file = filename
        if bin_ver == 0:
            self.logger.warning("Failed to find rc.exe path")
            return False

        rc_path = os.path.join(rc_path, bin_file)

        if not os.path.isfile(os.path.join(rc_path, "x86", "rc.exe")):
            self.logger.warning(
                f"Failed to find: {os.path.join(rc_path, 'x86', 'rc.exe')}"
            )
            return False

        if not os.path.isfile(os.path.join(rc_path, "x64", "rc.exe")):
            self.logger.warning(
                f"Failed to find: {os.path.join(rc_path, 'x64', 'rc.exe')}"
            )
            return False

        self.logger.debug(f"rc.exe detected at:")
        self.logger.debug(f"\t{os.path.join(rc_path, 'x86')}")
        self.logger.debug(f"\t{os.path.join(rc_path, 'x64')}")

        self.path_mods["system"]["x86"].append(os.path.join(rc_path, "x86"))
        self.path_mods["system"]["x64"].append(os.path.join(rc_path, "x64"))

        return
