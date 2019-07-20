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


class BaseTool(object):
    """
    Base class for Mussels tool detection.
    """

    name = "sample"
    version = "1.2.3"
    url = "https://sample.com/sample.exe"

    path_mods = {
        "system": {
            "x86": [os.path.join("expected", "install", "path")],
            "x64": [os.path.join("expected", "install", "path")],
        },
        "local": {
            "x86": [os.path.join("expected", "install", "path")],
            "x64": [os.path.join("expected", "install", "path")],
        },
    }

    file_checks = {
        "system": [os.path.join("expected", "install", "path")],
        "local": [os.path.join("expected", "install", "path")],
    }

    # Install script to use in case the tool isn't already available and must be installed.
    install_script = """
    """

    # The installdir may be used for a local install in the event that the tool must be installed.
    tempdir = ""
    installdir = ""

    installed = ""

    def __init__(self, tempdir: str = ""):
        """
        Download the archive (if necessary) to the Downloads directory.
        Extract the archive to the temp directory so it is ready to build.
        """
        if tempdir == "":
            # No temp dir provided, build in the current working directory.
            self.tempdir = os.getcwd()
        else:
            self.tempdir = os.path.abspath(tempdir)
        os.makedirs(self.tempdir, exist_ok=True)

        self.installdir = os.path.join(self.tempdir, "toolchain")
        os.makedirs(self.installdir, exist_ok=True)

        self.logsdir = os.path.join(self.tempdir, "logs", "tools")
        os.makedirs(self.logsdir, exist_ok=True)

        self.__init_logging()

    def __init_logging(self):
        """
        Initializes the logging parameters
        """
        self.logger = logging.getLogger(f"{self.name}-{self.version}")
        self.logger.setLevel(os.environ.get("LOG_LEVEL", logging.DEBUG))

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s:  %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

        self.log_file = os.path.join(
            self.logsdir,
            f"{self.name}-{self.version}.{datetime.datetime.now()}.log".replace(
                ":", "_"
            ),
        )
        filehandler = logging.FileHandler(filename=self.log_file)
        filehandler.setLevel(logging.DEBUG)
        filehandler.setFormatter(formatter)

        self.logger.addHandler(filehandler)

    def __download_installer(self) -> bool:
        """
        Use the URL to download the archive if it doesn't already exist in the Downloads directory.
        """
        if self.url == "":
            self.logger.warning(
                f"No download URL available for {self.name}-{self.version}."
            )
            return False

        # Determine download path from URL
        self.archive = self.url.split("/")[-1]
        self.download_path = os.path.join(
            os.path.expanduser("~"), "Downloads", self.archive
        )

        # Exit early if we already have the archive.
        if os.path.exists(self.download_path):
            self.logger.debug(f"Installer already downloaded.")
            return True

        self.logger.info(f"Downloading {self.url} to {self.download_path}...")

        try:
            r = requests.get(self.url)
            with open(self.download_path, "wb") as f:
                f.write(r.content)
        except Exception:
            self.logger.info(f"Failed to download archive from {self.url}!")
            return False

        return True

    def detect(self) -> bool:
        """
        Determine if tool is available in expected locations.
        """
        self.installed = ""

        self.logger.info(f"Detecting tool: {self.name}-{self.version}...")

        for install_location in self.file_checks:
            missing_file = False

            for filepath in self.file_checks[install_location]:
                if os.path.exists(filepath):
                    self.logger.debug(
                        f'{install_location}-install {self.name}-{self.version} file "{filepath}" found'
                    )
                else:
                    self.logger.warning(
                        f'{install_location}-install {self.name}-{self.version} file "{filepath}" not found'
                    )
                    missing_file = True

            if missing_file == False:
                self.logger.info(
                    f"{install_location}-install {self.name}-{self.version} detected!"
                )
                self.installed = install_location
                break

        if self.installed == "":
            self.logger.warning(f"Failed to detect {self.name}-{self.version}.")
            return False

        return True

    def install(self) -> bool:
        """
        Install the tool.
        """
        if self.install_script.strip() == "":
            self.logger.warning(
                f"No install script defined for {self.name}-{self.version}"
            )
            return False

        # Download if necessary.
        if self.__download_installer() == False:
            self.logger.warning(
                f"Failed to download installer for {self.name}-{self.version}"
            )
            return False

        # Create a install script.
        if platform.system() == "Windows":
            script_name = "build.bat"
            newline = "\r\n"
        else:
            script_name = "build.sh"
            newline = "\n"

        with open(os.path.join(os.getcwd(), script_name), "w", newline=newline) as fd:
            # Write the build commands to a file
            build_lines = self.install_script.splitlines()
            for line in build_lines:
                fd.write(line.strip() + "\n")

        if platform.system() != "Windows":
            st = os.stat(script_name)
            os.chmod(script_name, st.st_mode | stat.S_IEXEC)

        # Run the build script.
        process = subprocess.Popen(
            os.path.join(os.getcwd(), script_name),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        with process.stdout:
            for line in iter(process.stdout.readline, b""):
                self.logger.debug(line.decode("utf-8").strip())
        process.wait()
        if process.returncode != 0:
            self.logger.warning(f"{self.name}-{self.version} install failed!")
            self.logger.warning(f"Command:")
            for line in self.install_script.splitlines():
                self.logger.warning(line)
            self.logger.warning(f"Exit code: {process.returncode}")
            return False

        self.logger.info(f"{self.name}-{self.version} install completed.")

        # Detect if tool installed correctly.
        return self.detect()
