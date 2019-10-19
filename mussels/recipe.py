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
import glob
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
import time
import zipfile

import requests
import urllib.request
import patch

from mussels.utils.versions import pick_platform, nvc_str


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

    platforms: dict = {}  # Dictionary of recipe instructions for each platform.

    builds: dict = {}  # Dictionary of build paths.

    module_file: str = ""

    def __init__(self, toolchain: dict, platform: str, target: str, data_dir: str = ""):
        """
        Download the archive (if necessary) to the Downloads directory.
        Extract the archive to the temp directory so it is ready to build.
        """
        self.toolchain = toolchain
        self.platform = platform
        self.target = target

        if data_dir == "":
            # No temp dir provided, build in the current working directory.
            self.data_dir = os.getcwd()
        else:
            self.data_dir = os.path.abspath(data_dir)

        self.install_dir = os.path.join(self.data_dir, "install")
        self.downloads_dir = os.path.join(self.data_dir, "cache", "downloads")
        self.logs_dir = os.path.join(self.data_dir, "logs", "recipes")
        self.work_dir = os.path.join(self.data_dir, "cache", "work")

        self.module_dir = os.path.split(self.module_file)[0]

        if "patches" in self.platforms[self.platform][self.target]:
            self.patch_dir = os.path.join(
                self.module_dir, self.platforms[self.platform][self.target]["patches"]
            )
        else:
            self.patch_dir = ""

        self._init_logging()

    def _init_logging(self):
        """
        Initializes the logging parameters
        """
        os.makedirs(self.logs_dir, exist_ok=True)

        self.logger = logging.getLogger(f"{nvc_str(self.name, self.version)}")
        self.logger.setLevel(os.environ.get("LOG_LEVEL", logging.DEBUG))

        formatter = logging.Formatter(
            fmt="%(asctime)s - %(levelname)s:  %(message)s",
            datefmt="%m/%d/%Y %I:%M:%S %p",
        )

        self.log_file = os.path.join(
            self.logs_dir,
            f"{nvc_str(self.name, self.version)}.{datetime.datetime.now()}.log".replace(
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
        os.makedirs(self.downloads_dir, exist_ok=True)

        # Determine download path from URL &  possible archive name change.
        self.archive = self.url.split("/")[-1]
        if self.archive_name_change[0] != "":
            self.archive = self.archive.replace(
                self.archive_name_change[0], self.archive_name_change[1]
            )
        self.download_path = os.path.join(
            self.data_dir, "cache", "downloads", self.archive
        )

        # Exit early if we already have the archive.
        if os.path.exists(self.download_path):
            self.logger.debug(f"Archive already downloaded.")
            return True

        self.logger.info(f"Downloading {self.url}")
        self.logger.info(f"         to {self.download_path} ...")

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

    def _extract_archive(self, clean: bool) -> bool:
        """
        Extract the archive found in Downloads directory, if necessary.
        """
        if self.archive.endswith(".tar.gz"):
            self.builds[self.target] = os.path.join(
                self.work_dir, self.target, f"{self.archive[:-len('.tar.gz')]}"
            )
        elif self.archive.endswith(".zip"):
            self.builds[self.target] = os.path.join(
                self.work_dir, self.target, f"{self.archive[:-len('.zip')]}"
            )
        else:
            self.logger.error(
                f"Unexpected archive extension. Currently only supports .tar.gz and .zip!"
            )
            return False

        self.prior_build_exists = os.path.exists(self.builds[self.target])

        if self.prior_build_exists:
            if not clean:
                # Build directory already exists.  We're good.
                return True

            # Remove previous built, start over.
            self.logger.info(
                f"--clean: Removing previous {self.target} build directory:"
            )
            self.logger.info(f"   {self.builds[self.target]}")
            shutil.rmtree(self.builds[self.target])
            self.prior_build_exists = False

        os.makedirs(os.path.join(self.work_dir, self.target), exist_ok=True)

        # Make our own copy of the extracted source so we don't dirty the original.
        self.logger.debug(f"Preparing {self.target} build directory:")
        self.logger.debug(f"   {self.builds[self.target]}")

        if self.archive.endswith(".tar.gz"):
            # Un-tar
            self.logger.info(
                f"Extracting tarball archive {self.archive} to {self.builds[self.target]} ..."
            )

            tar = tarfile.open(self.download_path, "r:gz")
            tar.extractall(os.path.join(self.work_dir, self.target))
            tar.close()
        elif self.archive.endswith(".zip"):
            # Un-zip
            self.logger.info(
                f"Extracting zip archive {self.archive} to {self.builds[self.target]} ..."
            )

            zip_ref = zipfile.ZipFile(self.download_path, "r")
            zip_ref.extractall(os.path.join(self.work_dir, self.target))
            zip_ref.close()

        return True

    def _run_script(self, target, name, script) -> bool:
        """
        Run a script in the current working directory.
        """
        # Create a build script.
        if platform.system() == "Windows":
            script_name = f"_{name}.bat"
            newline = "\r\n"
        else:
            script_name = f"_{name}.sh"
            newline = "\n"

        with open(os.path.join(os.getcwd(), script_name), "w", newline=newline) as fd:
            # Evaluate "".format() syntax in the build script
            var_includes = os.path.join(self.install_dir, target, "include").replace(
                "\\", "/"
            )
            var_libs = os.path.join(self.install_dir, target, "lib").replace("\\", "/")
            var_install = os.path.join(self.install_dir).replace("\\", "/")
            var_build = os.path.join(self.builds[target]).replace("\\", "/")
            var_target = target

            script = script.format(
                includes=var_includes,
                libs=var_libs,
                install=var_install,
                build=var_build,
                target=var_target,
            )

            # Write the build commands to a file
            build_lines = script.splitlines()
            for line in build_lines:
                line = line.strip()
                if platform.system() == "Windows" and line.endswith("\\"):
                    fd.write(line.rstrip("\\") + " ")
                else:
                    fd.write(line + "\n")

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
            self.logger.warning(
                f"{nvc_str(self.name, self.version)} {target} build failed!"
            )
            self.logger.warning(f"Command:")
            for line in script.splitlines():
                self.logger.warning(line)
            self.logger.warning(f"Exit code: {process.returncode}")
            self.logger.error(f'"{name}" script failed for {target} build')
            return False

        return True

    def _build(self, clean: bool = False) -> bool:
        """
        Patch source materials if not already patched.
        Then, for each architecture, run the build commands if the output files don't already exist.
        """
        if self.is_collection:
            self.logger.debug(
                f"Build completed for recipe collection {nvc_str(self.name, self.version)}"
            )
            return True

        os.makedirs(self.work_dir, exist_ok=True)

        # Download and build if necessary.
        if not self._download_archive():
            self.logger.error(
                f"Failed to download source archive for {nvc_str(self.name, self.version)}"
            )
            return False

        # Extract to the work_dir.
        if not self._extract_archive(clean):
            self.logger.error(
                f"Failed to extract source archive for {nvc_str(self.name, self.version)}"
            )
            return False

        if not os.path.isdir(self.patch_dir):
            self.logger.debug(f"No patch directory found.")
        else:
            # Patches exists for this recipe.
            self.logger.debug(
                f"Patch directory found for {nvc_str(self.name, self.version)}."
            )
            if not os.path.exists(
                os.path.join(self.builds[self.target], "_mussles.patched")
            ):
                # Not yet patched. Apply patches.
                self.logger.info(
                    f"Applying patches to {nvc_str(self.name, self.version)} ({self.target}) build directory ..."
                )
                for patchfile in os.listdir(self.patch_dir):
                    if patchfile.endswith(".diff") or patchfile.endswith(".patch"):
                        self.logger.info(f"Attempting to apply patch: {patchfile}")
                        pset = patch.fromfile(os.path.join(self.patch_dir, patchfile))
                        patched = pset.apply(1, root=self.builds[self.target])
                        if not patched:
                            self.logger.error(f"Patch failed!")
                            return False
                    else:
                        self.logger.info(
                            f"Copying new file {patchfile} to {nvc_str(self.name, self.version)} ({self.target}) build directory ..."
                        )
                        shutil.copyfile(
                            os.path.join(self.patch_dir, patchfile),
                            os.path.join(self.builds[self.target], patchfile),
                        )

                with open(
                    os.path.join(self.builds[self.target], "_mussles.patched"), "w"
                ) as patchmark:
                    patchmark.write("patched")

        build_scripts = self.platforms[self.platform][self.target]["build_script"]

        self.logger.info(
            f"Attempting to build {nvc_str(self.name, self.version)} for {self.target}"
        )

        # Add each tool from the toolchain to the PATH environment variable.
        for tool in self.toolchain:
            platform_options = self.toolchain[tool].platforms.keys()
            matching_platform = pick_platform(platform.system(), platform_options)
            if self.toolchain[tool].tool_path != "":
                self.logger.debug(
                    f"Adding tool {tool} path {self.toolchain[tool].tool_path} to PATH"
                )
                os.environ["PATH"] = (
                    self.toolchain[tool].tool_path + os.pathsep + os.environ["PATH"]
                )

        cwd = os.getcwd()
        os.chdir(self.builds[self.target])

        if not self.prior_build_exists:
            # Run "configure" script, if exists.
            if "configure" in build_scripts.keys():
                if not self._run_script(
                    self.target, "configure", build_scripts["configure"]
                ):
                    self.logger.error(
                        f"{nvc_str(self.name, self.version)} {self.target} build failed."
                    )
                    os.chdir(cwd)
                    return False

        else:
            os.chdir(self.builds[self.target])

        # Run "make" script, if exists.
        if "make" in build_scripts.keys():
            if not self._run_script(self.target, "make", build_scripts["make"]):
                self.logger.error(
                    f"{nvc_str(self.name, self.version)} {self.target} build failed."
                )
                os.chdir(cwd)
                return False

        # Run "install" script, if exists.
        if "install" in build_scripts.keys():
            if not self._run_script(self.target, "install", build_scripts["install"]):
                self.logger.error(
                    f"{nvc_str(self.name, self.version)} {self.target} build failed."
                )
                os.chdir(cwd)
                return False

        self.logger.info(
            f"{nvc_str(self.name, self.version)} {self.target} build succeeded."
        )
        os.chdir(cwd)

        if not self._install():
            return False

        return True

    def _install(self):
        """
        Copy the headers and libs to an install directory.
        """
        os.makedirs(self.install_dir, exist_ok=True)

        self.logger.info(
            f"Copying {nvc_str(self.name, self.version)} install files to: {self.install_dir}."
        )

        install_paths = self.platforms[self.platform][self.target]["install_paths"]

        for install_path in install_paths:

            for install_item in install_paths[install_path]:
                src_path = os.path.join(self.builds[self.target], install_item)

                for src_filepath in glob.glob(src_path):
                    # Make sure it actually exists.
                    if not os.path.exists(src_filepath):
                        self.logger.error(
                            f"Required target files for installation do not exist:\n\t{src_filepath}"
                        )
                        return False

                    dst_path = os.path.join(
                        self.install_dir,
                        self.target,
                        install_path,
                        os.path.basename(src_filepath),
                    )

                    # Remove prior installation, if exists.
                    if os.path.isdir(dst_path):
                        shutil.rmtree(dst_path)
                    elif os.path.isfile(dst_path):
                        os.remove(dst_path)

                    # Create the target install paths, if it doesn't already exist.
                    os.makedirs(os.path.split(dst_path)[0], exist_ok=True)

                    self.logger.debug(f"Copying: {src_filepath}")
                    self.logger.debug(f"     to: {dst_path}")

                    # Now copy the file or directory.
                    if os.path.isdir(src_filepath):
                        dir_util.copy_tree(src_filepath, dst_path)
                    else:
                        shutil.copyfile(src_filepath, dst_path)

        self.logger.info(
            f"{nvc_str(self.name, self.version)} {self.target} install succeeded."
        )
        return True
