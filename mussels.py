r'''
  __    __     __  __     ______     ______     ______     __         ______    
 /\ "-./  \   /\ \/\ \   /\  ___\   /\  ___\   /\  ___\   /\ \       /\  ___\   
 \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \___  \  \ \  __\   \ \ \____  \ \___  \  
  \ \_\ \ \_\  \ \_____\  \/\_____\  \/\_____\  \ \_____\  \ \_____\  \/\_____\ 
   \/_/  \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/ 

A tool to download and build source archives and assemble the %CLAM_DEPENDENCIES% directory.
'''

import argparse
import datetime
from distutils import dir_util
import logging
import os
import requests
import shutil
import subprocess
import tarfile
import zipfile

import pexpect

logging.basicConfig()
module_logger = logging.getLogger('mussels')
module_logger.setLevel(logging.DEBUG)

class Builder(object):

    name = "sample"
    url = "https://sample.com/sample.tar.gz"
    archive_name_change = ("","") # Tuple of strings to replace: Eg. ("v", "nghttp2-")
    install_paths = {
        "include" : {
            "x86" : "", # Include directory for x86: "<relative path to headers>",
            "x64" : "", # Include directory for x64: "<relative path to headers>",
        },
        "lib" : {
            "x86" : [], # List of built x86 libraries: ["<relative path to DLL>",],
            "x64" : [], # List of built x64 libraries: ["<relative path to DLL>",],
        }
    }
    dependencies = []   # Dependencies on other Mussels builds.
    toolchain = {}      # Dictionary of files and directories required by the build commands.
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
        if self.__detect_toolchain() == False:
            raise(Exception(f"Failed to detect toolchain required to build {self.name}"))

        # Download if necessary.
        if self.__download_archive() == False:
            raise(Exception(f"Failed to download source archive for {self.name}"))

        # Extract to the tempdir.
        if self.__extract_archive() == False:
            raise(Exception(f"Failed to extract source archive for {self.name}"))

    def __init_logging(self):
        '''
        Initializes the logging parameters
        '''
        self.logger = logging.getLogger(f'mussels.{self.name}')
        self.logger.setLevel(os.environ.get('LOG_LEVEL', logging.DEBUG))

        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s:  %(message)s',
            datefmt='%m/%d/%Y %I:%M:%S %p')

        self.log_file = os.path.join(self.tempdir, f"mussels.{self.name}.{datetime.datetime.now()}.log".replace(':', '_'))
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
            self.build_path = os.path.join(self.tempdir, self.archive[:-7])
            if (os.path.exists(self.build_path)):
                self.logger.debug(f"Archive already extracted.")
                return True

            self.logger.info(f"Extracting Tarball {self.archive} to {self.build_path}...")

            tar = tarfile.open(self.download_path, "r:gz")
            tar.extractall(self.tempdir)
            tar.close()
        elif self.download_path.endswith(".zip"):
            # Un-zip
            self.build_path = os.path.join(self.tempdir, self.archive[:-4])
            if (os.path.exists(self.build_path)):
                self.logger.debug(f"Archive already extracted.")
                return True

            self.logger.info(f"Extracting Zip {self.archive} to {self.build_path}...")

            zip_ref = zipfile.ZipFile(self.download_path, 'r')
            zip_ref.extractall(self.tempdir)
            zip_ref.close()
        else:
            self.logger.error(f"Unexpected archive extension!")
            return False

        return True

    def __detect_toolchain(self) -> bool:
        '''
        Detect filepaths needed for the build.

        This base object implementation detects:
         - "rcpath" : The location of rc.exe
         - "vcvars" : The full path of vcvarsall.bat
        '''
        rcpath = "C:\\Program Files (x86)\\Windows Kits\\10\\bin\\"
        vcvars = "C:\\Program Files (x86)\\Microsoft Visual Studio 10.0\\VC"

        bin_ver = 0
        bin_file = ''
        for filename in os.listdir(rcpath):
            if filename.startswith("10.0."):
                ver = int(filename.split('.')[2])
                if (ver > bin_ver):
                    bin_ver = ver
                    bin_file = filename
        if bin_ver == 0:
            self.logger.warning("Failed to find rc.exe path")
            return False

        rcpath = os.path.join(rcpath, bin_file)

        if not os.path.isfile(os.path.join(rcpath, "x86", "rc.exe")):
            self.logger.warning(f"Failed to find: {os.path.join(rcpath, 'x86', 'rc.exe')}")
            return False

        if not os.path.isfile(os.path.join(rcpath, "x64", "rc.exe")):
            self.logger.warning(f"Failed to find: {os.path.join(rcpath, 'x64', 'rc.exe')}")
            return False

        if not os.path.isfile(os.path.join(vcvars, "vcvarsall.bat")):
            self.logger.warning("Failed to find vcvarsall.bat")
            return False

        os.environ["PATH"] += os.pathsep + vcvars
        print(f"Setting path to: {os.environ['PATH']}")
        self.toolchain['rcpath'] = rcpath
        self.toolchain['vcvars'] = vcvars

    def cmake_build(self) -> bool:
        '''
        Compile a project using standard CMake calls.
        '''
        self.logger.info(f"Attempting CMake build in: \"{self.build_path}\"...")
        
        return False

    def build(self) -> bool:
        '''
        Run the build commands if the output files don't already exist.
        '''
        for build in self.build_cmds:
            already_built = True

            # Check for prior completed build output.
            self.logger.info(f"Attempting to build {self.name} for {build}")
            self.builds[build] = self.build_path + "." + build

            if os.path.exists(self.builds[build]):
                self.logger.debug("Checking for prior build output...")
                for dll in self.install_paths["lib"][build]:
                    self.logger.debug(f"Checking for {dll}")

                    if not os.path.exists(os.path.join(self.builds[build], dll)):
                        self.logger.debug(f"{dll} not found.")
                        already_built = False
                        break

                if already_built == True:
                    self.logger.info(f"{self.name} {build} build output already exists.")
                    continue
            else:
                shutil.copytree(self.build_path, self.builds[build])

            # Run the build.
            cwd = os.getcwd()
            os.chdir(self.builds[build])

            # Hack to make rc.exe work for openssl 1.1.0
            os.environ["PATH"] += os.pathsep + self.toolchain['rcpath'] + os.path.sep + build

            # Create a build script.
            with open(os.path.join(os.getcwd(), "build.bat"), 'w') as fd:
                fd.write(' && ping 127.0.0.1 -n 10 > nul && '.join(self.build_cmds[build]))

            # Run the build script.
            completed_process = subprocess.Popen(os.path.join(os.getcwd(), "build.bat"), shell=True)
            completed_process.wait()
            if completed_process.returncode != 0:
                self.logger.warning(f"Build failed!")
                self.logger.warning(f"Command: {' && '.join(self.build_cmds[build])}\n")
                self.logger.warning(f"Exit code: {completed_process.returncode}")
                return False

            os.chdir(cwd)

        return True

    def install(self, install="install"):
        '''
        Copy the headers and libs to an install directory in the format expected by ClamAV.
        '''
        install_path = os.path.join(self.tempdir, install)

        self.logger.error(f"Copying required files into install directory.")

        for target_type in self.install_paths:
            
            for build in self.build_cmds:
                install_arch = build
                if build == "x86":
                    install_arch = "Win32"

                for target in self.install_paths[target_type][build]:
                    src_path = os.path.join(self.builds[build], target)
                    dst_path = os.path.join(install_path, install_arch, target_type, os.path.basename(target))

                    # Create the target install paths, if it doesn't already exist.
                    os.makedirs(os.path.split(dst_path)[0], exist_ok=True)

                    # Make sure it actually exists.
                    if not os.path.exists(src_path):
                        self.logger.error(f"Required target files for installation do not exist:\n\t{src_path}")
                        return False

                    # Remove prior installation, if exists.
                    if os.path.exists(dst_path):
                        shutil.rmtree(dst_path)

                    # Now copy the file or directory.
                    if os.path.isdir(src_path):
                        dir_util.copy_tree(src_path, dst_path)
                    else:
                        shutil.copyfile(src_path, dst_path)

class OpenSSL(Builder):
    name = "openssl"
    url = "https://www.openssl.org/source/openssl-1.1.0j.tar.gz"
    install_paths = {
        "include" : {
            "x86" : [
                os.path.join("include", "openssl"),
            ],
            "x64" : [
                os.path.join("include", "openssl"),
            ],
        },
        "lib" : {
            "x86" : [
                os.path.join("libssl-1_1.dll"), 
                os.path.join("libcrypto-1_1.dll"),
            ],
            "x64" : [
                os.path.join("libssl-1_1-x64.dll"), 
                os.path.join("libcrypto-1_1-x64.dll"),
            ],
        },
    }
    dependencies = []
    build_cmds = {
        'x86' : [
            f'vcvarsall.bat x86',
            f'perl Configure VC-WIN32',
            f'nmake',
        ],
        'x64' : [
            f'vcvarsall.bat amd64',
            f'perl Configure VC-WIN64A',
            f'nmake',
        ]
    }

class PThreads(Builder):
    name = "pthreads"
    url = "ftp://sourceware.org/pub/pthreads-win32/pthreads-w32-1-11-0-release.tar.gz"
    install_paths = {
        "include" : {
            "x86" : "include",
            "x64" : "include",
        },
        "lib" : {
            "x86" : [os.path.join("win32", "pthreads.dll"),],
            "x64" : [os.path.join("x64", "pthreads.dll"),],
        },
    }
    dependencies = []

    def build(self) -> bool:
        '''
        Build pthreads-win32
        '''
        if super().build() == True:
            return True

        self.logger.info("Not yet implemented!")
        return False

class NGHTTP2(Builder):
    name = "nghttp2"
    url = "https://github.com/nghttp2/nghttp2/archive/v1.36.0.zip"
    archive_name_change = ("v", "nghttp2-")
    install_paths = {
        "include" : {
            "x86" : "include",
            "x64" : "include",
        },
        "lib" : {
            "x86" : [os.path.join("win32", "libnghttp2.dll"),],
            "x64" : [os.path.join("x64", "libnghttp2.dll"),],
        },
    }
    dependencies = []

    def build(self) -> bool:
        '''
        Build nghttp2
        '''
        if super().build() == True:
            return True

        self.logger.info("Not yet implemented!")
        return False

class ZLib(Builder):
    name = "zlib"
    url = "https://www.zlib.net/zlib-1.2.11.tar.gz"
    install_paths = {
        "include" : {
            "x86" : "include",
            "x64" : "include",
        },
        "lib" : {
            "x86" : [os.path.join("win32", "libz.dll"),],
            "x64" : [os.path.join("x64" ,"libz.dll"),],
        },
    }

    def build(self) -> bool:
        '''
        Build zlib
        '''
        if super().build() == True:
            return True

        self.logger.info("Not yet implemented!")
        return False

class Curl(Builder):
    name = "curl"
    url = "https://curl.haxx.se/download/curl-7.64.0.zip"
    install_paths = {
        "include" : {
            "x86" : "include",
            "x64" : "include",
        },
        "lib" : {
            "x86" : [os.path.join("win32", "libcurl.dll"),],
            "x64" : [os.path.join("x64", "libcurl.dll"),],
        },
    }
    dependencies = [OpenSSL, NGHTTP2, ZLib]

    def build(self) -> bool:
        '''
        Build libcurl
        '''
        if super().build() == True:
            return True

        self.logger.info("Not yet implemented!")
        return False


'''
List of all available build targets.
'''
btargs = {
    Curl.name : Curl,
    ZLib.name : ZLib,
    NGHTTP2.name : NGHTTP2,
    PThreads.name : PThreads,
    OpenSSL.name : OpenSSL
}

def build(btarg, tempdir=None):
    '''
    Use the Builder class to download, extract, build, and install the dependency.
    '''
    module_logger.info(f"Attempting to build {btarg}...")
    builder = btargs[btarg](tempdir)
    
    if builder.build() == False:
        module_logger.error(f" !! {btarg} build Failed !!\n")
    else:
        module_logger.info(f" :) {btarg} build Succeeded (:\n")
        builder.install()

    return builder

def print_results(results):
    pass

def main():
    '''
    Entry-point for CLI usage.
    '''
    parser = argparse.ArgumentParser(description=__doc__)

    # create the top-level parser
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', required=False,
                        default="all",
                        choices=["all"] + list(btargs.keys()),
                        help='Choose a specific target you wish to build.')
    parser.add_argument('--notemp', required=False,
                        default=False, action='store_true',
                        help='Uses the current working directory instead of a temp directory.')

    args = parser.parse_args()

    module_logger.info(__doc__)

    if args.notemp == None:
        # Create a temporary directory to work in.
        tempdir = os.path.join(os.getcwd(), "clamdeps_" + str(datetime.datetime.now()).replace(' ', '_').replace(':', '-'))
        os.mkdir(tempdir)
    else:
        # Use the current working directory.
        tempdir = os.getcwd()

    # Build the depenencies
    if args.build == "all":
        results = [build(key, tempdir) for key in btargs.keys()]
    else:
        results = [build(args.build, tempdir),]

    print_results(results)

if __name__ == "__main__":
    main()
