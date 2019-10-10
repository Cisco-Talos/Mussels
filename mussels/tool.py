"""
Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

This module provides the base class for every Tool.  A tool is anything that a Recipe
might depend on from the system environment.

The base class provides the logic for detecting tools.

There is work-in-progress logic to [optionally] download and install missing tools
on behalf of the user.

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

import datetime
from distutils import dir_util
import inspect
import logging
import os
import platform
import requests
import shutil
import stat
import subprocess
import tarfile
import zipfile

from io import StringIO

from mussels.utils.versions import platform_is


class BaseTool(object):
    """
    Base class for Mussels tool detection.
    """

    name = "sample"
    version = ""
    platforms: dict = {}
    logs_dir = ""
    installed = ""

    def __init__(self, data_dir: str = ""):
        """
        Download the archive (if necessary) to the Downloads directory.
        Extract the archive to the temp directory so it is ready to build.
        """
        if data_dir == "":
            # No temp dir provided, build in the current working directory.
            self.logs_dir = os.path.join(os.getcwd(), "logs", "tools")
        else:
            self.logs_dir = os.path.join(os.path.abspath(data_dir), "logs", "tools")
        os.makedirs(self.logs_dir, exist_ok=True)

        if self.version != "":
            self.name_version = f"{self.name}-{self.version}"
        else:
            self.name_version = self.name

        self._init_logging()

    def _init_logging(self):
        """
        Initializes the logging parameters
        """
        self.logger = logging.getLogger(f"{self.name_version}")
        self.logger.setLevel(os.environ.get("LOG_LEVEL", logging.DEBUG))

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s:  %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

        self.log_file = os.path.join(
            self.logs_dir,
            f"{self.name_version}.{datetime.datetime.now()}.log".replace(":", "_"),
        )
        filehandler = logging.FileHandler(filename=self.log_file)
        filehandler.setLevel(logging.DEBUG)
        filehandler.setFormatter(formatter)

        self.logger.addHandler(filehandler)

    def detect(self) -> bool:
        """
        Determine if tool is available in expected locations.
        """
        self.installed = ""

        self.logger.info(f"Detecting tool: {self.name_version}...")

        for each_platform in self.platforms:
            if platform_is(each_platform):
                for install_location in self.platforms[each_platform]["file_checks"]:
                    missing_file = False

                    for filepath in self.platforms[each_platform]["file_checks"][
                        install_location
                    ]:
                        if os.path.exists(filepath):
                            self.logger.info(
                                f'{install_location}-install {self.name_version} file "{filepath}" found'
                            )
                        else:
                            self.logger.info(
                                f'{install_location}-install {self.name_version} file "{filepath}" not found'
                            )
                            missing_file = True

                    if missing_file == False:
                        self.logger.info(
                            f"{install_location}-install {self.name_version} detected!"
                        )
                        self.installed = install_location
                        break
                break

        if self.installed == "":
            self.logger.warning(f"Failed to detect {self.name_version}.")
            return False

        return True
