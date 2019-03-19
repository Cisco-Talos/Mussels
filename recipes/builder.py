'''
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
'''

import datetime
from distutils import dir_util
import logging
import os
import requests
import shutil
import subprocess
import tarfile
import zipfile

class Builder(object):
    '''
    Base class for Mussels recipe.
    '''
    name = "sample"

    version = "1.2.3"

    url = "https://sample.com/sample.tar.gz"

    archive_name_change = ("","") # Tuple of strings to replace: Eg. ("v", "nghttp2-")
                                  # This hack is necessary because archives with changed
                                  # will extract to their original directory name.

    install_paths = {
        "x86" : {
           # "include" : [],      # "Destination directory": ["list", "of", "source", "items"],
           # "lib" : [],          # Will copy source item to destination directory,
        },
        "x64" : {
           # "include" : [        # Examples:
           #     "blarghus.h",    #  1. Copy file to x64\\include\\blarghus.h
           #     "iface/blarghus" #  2. Copy directory to x64\\include\\blarghus
           # ],
           # "lib" : [
           #     "Win32/blah.dll" #  3. Copy DLL to x64\\lib\\blah.dll
           # ],
        }
    }

    dependencies = []   # Dependencies on other Mussels builds.
                        # str format:  name@version.
                        #    "@version" is optional.
                        #    If version is omitted, the default (highest) will be selected.

    toolchain = []      # List of tools required by the build commands.

    build_cmds = {}     # Dictionary containing build command lists.

    builds = {}         # Dictionary of build paths.

    def __init__(self, tempdir=None):
        '''
        Download the archive (if necessary) to the Downloads directory.
        Extract the archive to the temp directory so it is ready to build.
        '''
        if tempdir == None:
            # No temp dir provided, build in the current working directory.
            self.tempdir = os.getcwd()
        else:
            self.tempdir = tempdir

        self.__init_logging()

        # Detect required toolchain.
        if self.detect_toolchain() == False:
            raise(Exception(f"Failed to detect toolchain required to build {self.name}-{self.version}"))

        # Download if necessary.
        if self.__download_archive() == False:
            raise(Exception(f"Failed to download source archive for {self.name}-{self.version}"))

        # Extract to the tempdir.
        if self.__extract_archive() == False:
            raise(Exception(f"Failed to extract source archive for {self.name}-{self.version}"))

    def __init_logging(self):
        '''
        Initializes the logging parameters
        '''
        self.logger = logging.getLogger(f'{self.name}-{self.version}')
        self.logger.setLevel(os.environ.get('LOG_LEVEL', logging.DEBUG))

        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s:  %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')

        self.log_file = os.path.join(self.tempdir, f"{self.name}-{self.version}.{datetime.datetime.now()}.log".replace(':', '_'))
        filehandler = logging.FileHandler(filename=self.log_file)
        filehandler.setLevel(logging.DEBUG)
        filehandler.setFormatter(formatter)

        self.logger.addHandler(filehandler)

    def __download_archive(self) -> bool:
        '''
        Use the URL to download the archive if it doesn't already exist in the Downloads directory.
        '''
        # Determine download path from URL &  possible archive name change.
        self.archive = self.url.split('/')[-1]
        if self.archive_name_change[0] != "":
            self.archive = self.archive.replace(self.archive_name_change[0], self.archive_name_change[1])
        self.download_path = os.path.join(os.path.expanduser('~'), 'Downloads', self.archive)

        # Exit early if we already have the archive.
        if (os.path.exists(self.download_path)):
            self.logger.debug(f"Archive already downloaded.")
            return True

        self.logger.info(f"Downloading {self.url} to {self.download_path}...")

        try:
            r = requests.get(self.url)
            with open(self.download_path, 'wb') as f:
                f.write(r.content)
        except Exception:
            self.logger.info(f"Failed to download archive from {self.url}!")
            return False

        return True

    def __extract_archive(self) -> bool:
        '''
        Extract the archive found in Downloads directory, if necessary.
        '''
        if self.download_path.endswith(".tar.gz"):
            # Un-tar
            self.extracted_source_path = os.path.join(self.tempdir, self.archive[:-7])
            if (os.path.exists(self.extracted_source_path)):
                self.logger.debug(f"Archive already extracted.")
                return True

            self.logger.info(f"Extracting Tarball {self.archive} to {self.extracted_source_path}...")

            tar = tarfile.open(self.download_path, "r:gz")
            tar.extractall(self.tempdir)
            tar.close()
        elif self.download_path.endswith(".zip"):
            # Un-zip
            self.extracted_source_path = os.path.join(self.tempdir, self.archive[:-4])
            if (os.path.exists(self.extracted_source_path)):
                self.logger.debug(f"Archive already extracted.")
                return True

            self.logger.info(f"Extracting Zip {self.archive} to {self.extracted_source_path}...")

            zip_ref = zipfile.ZipFile(self.download_path, 'r')
            zip_ref.extractall(self.tempdir)
            zip_ref.close()
        else:
            self.logger.error(f"Unexpected archive extension!")
            return False

        return True

    def __detect_vs2015(self) -> bool:
        '''
        Identify:
         - The full path of vcvarsall.bat for vs2015.
         - The location of rc.exe (check x86 and x64 locations).
           This is a hack, needed only because vcvarsall.bat doesn't
           set the rc.exe path location for you. vs2017 does.
        '''
        vcvars_path = "C:\\Program Files (x86)\\Microsoft Visual Studio 14.0\\VC"

        if not os.path.isfile(os.path.join(vcvars_path, "vcvarsall.bat")):
            self.logger.warning("Failed to find vcvarsall.bat")
            return False

        self.logger.debug(f"vcvarsall.bat detected at: {vcvars_path}")
        os.environ["PATH"] += os.pathsep + vcvars_path

        # rc.exe Hack to make openssl build with vs2015
        rc_path = "C:\\Program Files (x86)\\Windows Kits\\10\\bin\\"

        bin_ver = 0
        bin_file = ''
        for filename in os.listdir(rc_path):
            if filename.startswith("10.0."):
                ver = int(filename.split('.')[2])
                if (ver > bin_ver):
                    bin_ver = ver
                    bin_file = filename
        if bin_ver == 0:
            self.logger.warning("Failed to find rc.exe path")
            return False

        rc_path = os.path.join(rc_path, bin_file)

        if not os.path.isfile(os.path.join(rc_path, "x86", "rc.exe")):
            self.logger.warning(f"Failed to find: {os.path.join(rc_path, 'x86', 'rc.exe')}")
            return False

        if not os.path.isfile(os.path.join(rc_path, "x64", "rc.exe")):
            self.logger.warning(f"Failed to find: {os.path.join(rc_path, 'x64', 'rc.exe')}")
            return False

        self.logger.debug(f"rc.exe detected at:")
        self.logger.debug(f"\t{os.path.join(rc_path, 'x86')}")
        self.logger.debug(f"\t{os.path.join(rc_path, 'x64')}")

        self.rc_path = rc_path

        return True

    def __detect_vs2017(self) -> bool:
        '''
        Identify:
         - The full path of vcvarsall.bat for vs2017.
        '''
        vcvars_path = "C:\\Program Files (x86)\\Microsoft Visual Studio\\2017\\Community\\VC\\Auxiliary\\Build"

        if not os.path.isfile(os.path.join(vcvars_path, "vcvarsall.bat")):
            self.logger.warning("Failed to find vcvarsall.bat")
            return False

        self.logger.debug(f"vcvarsall.bat detected at: {vcvars_path}")
        os.environ["PATH"] += os.pathsep + vcvars_path

        return True

    def __detect_nasm(self) -> bool:
        '''
        Identify:
         - The location of nasm.exe.
        '''
        nasm_path = "C:\\Program Files\\NASM"

        if not os.path.isfile(os.path.join(nasm_path, "nasm.exe")):
            self.logger.warning("Failed to find nasm.exe")
            return False

        self.logger.debug(f"nasm.exe detected at: {nasm_path}")
        os.environ["PATH"] += os.pathsep + nasm_path

        return True

    def __detect_perl(self) -> bool:
        '''
        Identify:
         - The location of perl.exe.
        '''
        perl_path = "C:\\Perl64\\bin"

        if not os.path.isfile(os.path.join(perl_path, "perl.exe")):
            self.logger.warning("Failed to find perl.exe")
            return False

        self.logger.debug(f"perl.exe detected at: {perl_path}")
        os.environ["PATH"] += os.pathsep + perl_path

        return True

    def __detect_cmake(self) -> bool:
        '''
        Identify:
         - The location of perl.exe.
        '''
        cmake_path = "C:\\Program Files\\CMake\\bin"

        if not os.path.isfile(os.path.join(cmake_path, "cmake.exe")):
            self.logger.warning("Failed to find cmake.exe")
            return False

        self.logger.debug(f"cmake.exe detected at: {cmake_path}")
        os.environ["PATH"] += os.pathsep + cmake_path

        return True

    def detect_toolchain(self) -> bool:
        '''
        Detect existence of toolchain filepaths needed for the build.

        This base object implementation detects:
         - "vs2015" : Adds paths to path needed to use Visual Studio for builds.
         - "nmake" : Add NMake to the path.

        You can extend this functionality by overriding it to detect
        new tools to add to the path.
        '''
        for tool in self.toolchain:
            if "vs2015" == tool:
                if False == self.__detect_vs2015():
                    self.logger.error("Failed to detect vs2015")
                    return False
                else:
                    self.logger.info("Detected vs2015")

            if "vs2017" == tool:
                if False == self.__detect_vs2017():
                    self.logger.error("Failed to detect vs2017")
                    return False
                else:
                    self.logger.info("Detected vs2017")

            elif "nasm" == tool:
                if False == self.__detect_nasm():
                    self.logger.error("Failed to detect nasm")
                    return False
                else:
                    self.logger.info("Detected nasm")

            elif "perl" == tool:
                if False == self.__detect_perl():
                    self.logger.error("Failed to detect perl")
                    return False
                else:
                    self.logger.info("Detected perl")

            elif "cmake" == tool:
                if False == self.__detect_cmake():
                    self.logger.error("Failed to detect cmake")
                    return False
                else:
                    self.logger.info("Detected cmake")

        return True

    def build(self) -> bool:
        '''
        Run the build commands if the output files don't already exist.
        '''
        for build in self.build_cmds:
            already_built = True

            # Check for prior completed build output.
            self.logger.info(f"Attempting to build {self.name}-{self.version} for {build}")
            self.builds[build] = self.extracted_source_path + "." + build

            if os.path.exists(self.builds[build]):
                self.logger.debug("Checking for prior build output...")
                for install_path in self.install_paths[build]:
                    for install_item in self.install_paths[build][install_path]:
                        self.logger.debug(f"Checking for {install_item}")

                        if not os.path.exists(os.path.join(self.builds[build], install_item)):
                            self.logger.debug(f"{install_item} not found.")
                            already_built = False
                            break

                if already_built == True:
                    # It looks like there was a successful prior build. Skip.
                    self.logger.info(f"{self.name}-{self.version} {build} build output already exists.")
                    continue
                else:
                    # It appears that the previous build is missing the desired build output.
                    # Maybe the previous build failed?
                    # Probably should delete the incomplete build directory and try again.
                    shutil.rmtree(self.builds[build])
            else:
                # Make our own copy of the extracted source so we don't dirty the original.
                shutil.copytree(self.extracted_source_path, self.builds[build])

            # Run the build.
            cwd = os.getcwd()
            os.chdir(self.builds[build])

            # Hack to make openssl build work with vs2015
            try:
                os.environ["PATH"] += os.pathsep + self.rc_path + os.path.sep + build
            except:
                pass

            # Create a build script.
            with open(os.path.join(os.getcwd(), "build.bat"), 'w') as fd:
                fd.write(' && '.join(self.build_cmds[build]))

            # Run the build script.
            completed_process = subprocess.Popen(os.path.join(os.getcwd(), "build.bat"), shell=True)
            completed_process.wait()
            if completed_process.returncode != 0:
                self.logger.warning(f"{self.name}-{self.version} {build} build failed!")
                self.logger.warning(f"Command: {' && '.join(self.build_cmds[build])}\n")
                self.logger.warning(f"Exit code: {completed_process.returncode}")
                os.chdir(cwd)
                return False

            self.logger.info(f"{self.name}-{self.version} {build} build succeeded.")
            os.chdir(cwd)

        return True

    def install(self, install="install"):
        '''
        Copy the headers and libs to an install directory in the format expected by ClamAV.
        '''
        install_path = os.path.join(self.tempdir, install)

        self.logger.info(f"Copying {self.name}-{self.version} install files into install directory.")

        for build in self.install_paths:
            if build == "x86":
                install_arch = "Win32"
            install_arch = build

            for install_path in self.install_paths:

                for install_item in self.install_paths[build][install_path]:
                    src_path = os.path.join(self.builds[build], install_item)
                    dst_path = os.path.join(install_path, install_arch, install_path, os.path.basename(install_item))

                    # Create the target install paths, if it doesn't already exist.
                    os.makedirs(os.path.split(dst_path)[0], exist_ok=True)

                    # Make sure it actually exists.
                    if not os.path.exists(src_path):
                        self.logger.error(f"Required target files for installation do not exist:\n\t{src_path}")
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
