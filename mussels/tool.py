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
from distutils import dir_util, spawn
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

from mussels.utils.versions import platform_is, nvc_str


class BaseTool(object):
    """
    Base class for Mussels tool detection.
    """

    name = "sample"
    version = ""
    platforms: dict = {}
    logs_dir = ""
    tool_path = ""

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

        self.name_version = nvc_str(self.name, self.version)

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

    def _run_command(self, command: str, expected_output: str) -> bool:
        """
        Run a command.
        """
        found_expected_output = False

        cmd = command.split()

        # Run the build script.
        try:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            )
            with process.stdout:
                for line in iter(process.stdout.readline, b""):
                    if expected_output in line.decode("utf-8"):
                        found_expected_output = True

            process.wait()
            if process.returncode != 0:
                self.logger.warning(f"Command failed!")
                return False
        except FileNotFoundError:
            self.logger.warning(f"Command failed; File not found!")
            return False
            
        return found_expected_output

    def detect(self) -> bool:
        """
        Determine if tool is available in expected locations.
        """
        found = False

        self.logger.info(f"Detecting tool: {self.name_version}...")

        for each_platform in self.platforms:
            if platform_is(each_platform):
                if "path_checks" in self.platforms[each_platform]:
                    for path_check in self.platforms[each_platform]["path_checks"]:
                        self.logger.info(f"  Checking for {path_check} in PATH")
                        install_location = spawn.find_executable(path_check)
                        if install_location == None:
                            self.logger.info(f"    {path_check} not found")
                        else:
                            self.logger.info(
                                f"    {path_check} found, at: {install_location}"
                            )
                            found = True
                            break

                if found:
                    break

                if "command_checks" in self.platforms[each_platform]:
                    for script_check in self.platforms[each_platform]["command_checks"]:
                        found = self._run_command(
                            command=script_check["command"],
                            expected_output=script_check["output_has"],
                        )
                        if not found:
                            self.logger.info(f"    {script_check['command']} failed.")
                        else:
                            self.logger.info(f"    {script_check['command']} passed!")
                            break

                if found:
                    break

                if "file_checks" in self.platforms[each_platform]:
                    for filepath in self.platforms[each_platform]["file_checks"]:
                        if not os.path.exists(filepath):
                            self.logger.info(
                                f'{self.name_version} file "{filepath}" not found'
                            )
                        else:
                            self.logger.info(
                                f'{self.name_version} file "{filepath}" found'
                            )
                            self.tool_path = os.path.dirname(filepath)
                            found = True
                            break
                break

        if not found:
            self.logger.warning(f"Failed to detect {self.name_version}.")
            return False

        return True
