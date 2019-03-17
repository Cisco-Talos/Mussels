'''
Copyright (C)2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

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

import os

from recipes.builder import Builder

class Recipe(Builder):
    '''
    Recipe to build libcurl.
    '''
    name = "curl"
    version = "7.64.0"
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
    dependencies = ["openssl", "nghttp2", "zlib"]