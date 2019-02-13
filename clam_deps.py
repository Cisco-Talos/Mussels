'''
Download and extract each Windows Clam dependency.

Build each dependency.

Construct the %CLAM_DEPENDENCIES% directory.
'''

import argparse
import os
import shutil

DEPS = {
    "curl" : "https://curl.haxx.se/download/curl-7.64.0.zip",
    "nghttp2" : "https://github.com/nghttp2/nghttp2/archive/v1.36.0.zip",
    "openssl" : "https://www.openssl.org/source/openssl-1.1.1a.tar.gz",
    "pthreads-win32" : ""
}

def main():
    pass

if __name__ == "__main__":
    main()