"""
Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

This module provides the base class for every Recipe.

This includes the logic for how to perform a build and how to relocate (or "install")
select files to a directory structure where other recipes can find & depend on them.

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
from io import StringIO
import logging
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import zipfile

import requests
import urllib.request
import patch


class BaseRecipe(object):
    """
    Base class for Mussels recipe.
    """

    name = "sample"
    version = "1.2.3"

    # Set collection to True if this is just a collection of recipes to build, and not an actual recipe.
    # If True, only `dependencies` and `required_tools` matter. Everything else should be omited.
    is_collection = False

    url = "https://sample.com/sample.tar.gz"  # URL of project release materials.

    # archive_name_change is a tuple of strings to replace.
    # For example:
    #     ("v", "nghttp2-")
    # will change:
    #     v2.3.4  to  nghttp2-2.3.4.
    # This hack is necessary because archives with changed names will extract to their original directory name.
    archive_name_change: tuple = ("", "")

    install_paths: dict = {
        # "x86": {
        #     "include" : [],      # "Destination directory": ["list", "of", "source", "items"],
        #     "lib" : [],          # Will copy source item to destination directory,
        # },
        # "x64": {
        #     "include" : [        # Examples:
        #         "blarghus.h",    #   Copy file to x64\\include\\blarghus.h
        #         "iface/blarghus" #   Copy directory to x64\\include\\blarghus
        #     ],
        #     "lib" : [
        #         "x64/blah.dll"   #   Copy DLL to x64\\lib\\blah.dll
        #         "x64/blah.lib"   #   Copy LIB to x64\\lib\\blah.lib
        #     ],
        # },
    }

    platform: list = []

    # Dependencies on other Mussels builds.
    # str format:  name@version.
    #    "@version" is optional.
    #    If version is omitted, the default (highest) will be selected.
    dependencies: list = []

    required_tools: list = []  # List of tools required by the build commands.

    # build_script is a dictionary containing build scripts for each build target.
    # Variables in "".format() syntax will be evaluated at build time.
    # Paths must have unix style forward slash (`/`) path separators.
    #
    # Variable options include:
    # - install:        The base install directory for build output.
    # - includes:       The install/{build}/include directory.
    # - libs:           The install/{build}/lib directory.
    # - build:          The build directory for a given build.
    build_script: dict = {
        # "x86": """
        # """,
        # "x64": """
        # """,
        # "host": """
        # """,
    }

    builds: dict = {}  # Dictionary of build paths.

    # The following will be defined during the build and exist here for convenience
    # when writing build_script's using the f-string `f` prefix to help remember the
    # names of variables.
    data_dir = ""
    installdir = ""

    def __init__(self, toolchain: dict, data_dir: str = ""):
        """
        Download the archive (if necessary) to the Downloads directory.
        Extract the archive to the temp directory so it is ready to build.
        """
        if data_dir == "":
            # No temp dir provided, build in the current working directory.
            self.data_dir = os.getcwd()
        else:
            self.data_dir = os.path.abspath(data_dir)
        os.makedirs(self.data_dir, exist_ok=True)

        self.installdir = os.path.join(self.data_dir, "install")
        os.makedirs(self.installdir, exist_ok=True)

        self.logsdir = os.path.join(self.data_dir, "logs", "recipes")
        os.makedirs(self.logsdir, exist_ok=True)
        self.workdir = os.path.join(self.data_dir, "work")
        os.makedirs(self.workdir, exist_ok=True)
        self.srcdir = os.path.join(self.data_dir, "src")
        os.makedirs(self.srcdir, exist_ok=True)

        self._init_logging()

        self.toolchain = toolchain

        # Skip download & build steps for collections.
        if self.is_collection == False:
            # Download and build if necessary.
            if self._download_archive() == False:
                raise (
                    Exception(
                        f"Failed to download source archive for {self.name}-{self.version}"
                    )
                )

            # Extract to the data_dir.
            if self._extract_archive() == False:
                raise (
                    Exception(
                        f"Failed to extract source archive for {self.name}-{self.version}"
                    )
                )

        module_file = sys.modules[self.__class__.__module__].__file__
        self.patches = os.path.join(
            os.path.split(os.path.abspath(module_file))[0], "patches"
        )

    def _init_logging(self):
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

    def _download_archive(self) -> bool:
        """
        Use the URL to download the archive if it doesn't already exist in the Downloads directory.
        """
        # Determine download path from URL &  possible archive name change.
        self.archive = self.url.split("/")[-1]
        if self.archive_name_change[0] != "":
            self.archive = self.archive.replace(
                self.archive_name_change[0], self.archive_name_change[1]
            )
        self.download_path = os.path.join(
            os.path.expanduser("~"), "Downloads", self.archive
        )

        # Exit early if we already have the archive.
        if os.path.exists(self.download_path):
            self.logger.debug(f"Archive already downloaded.")
            return True

        self.logger.info(f"Downloading {self.url} to {self.download_path}...")

        if self.url.startswith("ftp"):
            try:
                urllib.request.urlretrieve(self.url, self.download_path)
            except Exception as exc:
                self.logger.info(f"Failed to download archive from {self.url}, {exc}!")
                return False
        else:
            try:
                r = requests.get(self.url)
                with open(self.download_path, "wb") as f:
                    f.write(r.content)
            except Exception:
                self.logger.info(f"Failed to download archive from {self.url}!")
                return False

        return True

    def _extract_archive(self) -> bool:
        """
        Extract the archive found in Downloads directory, if necessary.
        """
        if self.download_path.endswith(".tar.gz"):
            # Un-tar
            self.extracted_source_path = os.path.join(self.srcdir, self.archive[:-7])
            if os.path.exists(self.extracted_source_path):
                self.logger.debug(f"Archive already extracted.")
                return True

            self.logger.info(
                f"Extracting Tarball {self.archive} to {self.extracted_source_path}..."
            )

            tar = tarfile.open(self.download_path, "r:gz")
            tar.extractall(self.srcdir)
            tar.close()
        elif self.download_path.endswith(".zip"):
            # Un-zip
            self.extracted_source_path = os.path.join(self.srcdir, self.archive[:-4])
            if os.path.exists(self.extracted_source_path):
                self.logger.debug(f"Archive already extracted.")
                return True

            self.logger.info(
                f"Extracting Zip {self.archive} to {self.extracted_source_path}..."
            )

            zip_ref = zipfile.ZipFile(self.download_path, "r")
            zip_ref.extractall(self.srcdir)
            zip_ref.close()
        else:
            self.logger.error(f"Unexpected archive extension!")
            return False

        return True

    def _install(self, build):
        """
        Copy the headers and libs to an install directory.
        """
        self.logger.info(
            f"Copying {self.name}-{self.version} install files to: {self.installdir}."
        )

        for install_path in self.install_paths[build]:

            for install_item in self.install_paths[build][install_path]:
                src_path = os.path.join(self.builds[build], install_item)
                dst_path = os.path.join(
                    self.installdir, build, install_path, os.path.basename(install_item)
                )

                # Create the target install paths, if it doesn't already exist.
                os.makedirs(os.path.split(dst_path)[0], exist_ok=True)

                # Make sure it actually exists.
                if not os.path.exists(src_path):
                    self.logger.error(
                        f"Required target files for installation do not exist:\n\t{src_path}"
                    )
                    return False

                # Remove prior installation, if exists.
                if os.path.isdir(dst_path):
                    shutil.rmtree(dst_path)
                elif os.path.isfile(dst_path):
                    os.remove(dst_path)

                self.logger.debug(f"Copying: {src_path}")
                self.logger.debug(f"     to: {dst_path}")

                # Now copy the file or directory.
                if os.path.isdir(src_path):
                    dir_util.copy_tree(src_path, dst_path)
                else:
                    shutil.copyfile(src_path, dst_path)

        self.logger.info(f"{self.name}-{self.version} {build} install succeeded.")
        return True

    def _build(self) -> bool:
        """
        First, patch source materials if not already patched.
        Then, for each architecture, run the build commands if the output files don't already exist.
        """
        if self.is_collection == True:
            self.logger.debug(
                f"Build completed for recipe collection {self.name}-{self.version}"
            )
            return True

        if not os.path.isdir(self.patches):
            self.logger.debug(f"No patch directory found.")
        else:
            # Patches exists for this recipe.
            self.logger.debug(f"Patch directory found for {self.name}-{self.version}.")
            if not os.path.exists(
                os.path.join(self.extracted_source_path, "_mussles.patched")
            ):
                # Not yet patched. Apply patches.
                self.logger.info(
                    f"Applying patches to {self.name}-{self.version} source directory..."
                )
                for patchfile in os.listdir(self.patches):
                    if patchfile.endswith(".diff") or patchfile.endswith(".patch"):
                        self.logger.info(f"Attempting to apply patch: {patchfile}")
                        pset = patch.fromfile(os.path.join(self.patches, patchfile))
                        patched = pset.apply(1, root=self.extracted_source_path)
                        if not patched:
                            self.logger.error(f"Patch failed!")
                            return False
                    else:
                        self.logger.info(
                            f"Copying new file {patchfile} to {self.name}-{self.version} source directory..."
                        )
                        shutil.copyfile(
                            os.path.join(self.patches, patchfile),
                            os.path.join(self.extracted_source_path, patchfile),
                        )

                with open(
                    os.path.join(self.extracted_source_path, "_mussles.patched"), "w"
                ) as patchmark:
                    patchmark.write("patched")

        for build in self.build_script:
            already_built = True

            # Check for prior completed build output.
            self.logger.info(
                f"Attempting to build {self.name}-{self.version} for {build}"
            )
            self.builds[build] = os.path.join(
                self.workdir, f"{os.path.split(self.extracted_source_path)[-1]}-{build}"
            )

            if os.path.exists(self.builds[build]):
                self.logger.debug("Checking for prior build output...")
                for install_path in self.install_paths[build]:
                    for install_item in self.install_paths[build][install_path]:
                        self.logger.debug(f"Checking for {install_item}")

                        if not os.path.exists(
                            os.path.join(
                                self.installdir,
                                build,
                                install_path,
                                os.path.basename(install_item),
                            )
                        ):
                            self.logger.debug(f"{install_item} not found.")
                            already_built = False
                            break

                if already_built == True:
                    # It looks like there was a successful prior build. Skip.
                    self.logger.info(
                        f"{self.name}-{self.version} {build} build output already exists."
                    )
                    continue
                else:
                    # It appears that the previous build is missing the desired build output.
                    # Maybe the previous build failed?
                    # Probably should delete the incomplete build directory and try again.
                    self.logger.debug(f"Removing dirty old {build} build directory:")
                    self.logger.debug(f"   {self.builds[build]}")
                    shutil.rmtree(self.builds[build])

                    # Make our own copy of the extracted source so we don't dirty the original.
                    self.logger.debug(
                        f"Creating new {build} build directory from extracted sources:"
                    )
                    self.logger.debug(f"   {self.builds[build]}")
                    shutil.copytree(self.extracted_source_path, self.builds[build])
            else:
                # Make our own copy of the extracted source so we don't dirty the original.
                self.logger.debug(
                    f"Creating {build} build directory from extracted sources:"
                )
                self.logger.debug(f"\t{self.builds[build]}")
                shutil.copytree(self.extracted_source_path, self.builds[build])

            #
            # Run the build.
            #
            cwd = os.getcwd()
            os.chdir(self.builds[build])

            # Add each tool from the toolchain to the PATH environment variable.
            for tool in self.toolchain:
                for path_mod in self.toolchain[tool].path_mods[
                    self.toolchain[tool].installed
                ][build]:
                    os.environ["PATH"] = path_mod + os.pathsep + os.environ["PATH"]

            # Create a build script.
            if platform.system() == "Windows":
                script_name = "build.bat"
                newline = "\r\n"
            else:
                script_name = "build.sh"
                newline = "\n"

            with open(
                os.path.join(os.getcwd(), script_name), "w", newline=newline
            ) as fd:
                # Evaluate "".format() syntax in the build script
                var_includes = os.path.join(self.installdir, build, "include").replace(
                    "\\", "/"
                )
                var_libs = os.path.join(self.installdir, build, "lib").replace(
                    "\\", "/"
                )
                var_install = os.path.join(self.installdir).replace("\\", "/")
                var_build = os.path.join(self.builds[build]).replace("\\", "/")

                self.build_script[build] = self.build_script[build].format(
                    includes=var_includes,
                    libs=var_libs,
                    install=var_install,
                    build=var_build,
                )

                # Write the build commands to a file
                build_lines = self.build_script[build].splitlines()
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
                self.logger.warning(f"{self.name}-{self.version} {build} build failed!")
                self.logger.warning(f"Command:")
                for line in self.build_script[build].splitlines():
                    self.logger.warning(line)
                self.logger.warning(f"Exit code: {process.returncode}")
                os.chdir(cwd)
                return False

            self.logger.info(f"{self.name}-{self.version} {build} build succeeded.")
            os.chdir(cwd)

            if self._install(build) == False:
                return False

        return True
