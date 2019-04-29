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

import os

from tools.tool import BaseTool

class Tool(BaseTool):
    '''
    Tool to detect Visual Studio 2017
    '''
    name = "visualstudio"
    version = "2017"
    url = "https://download.visualstudio.microsoft.com/download/pr/cb4bb895-e020-49e0-8cb0-1cdeeb1bfc2f/0224f1b33e9624fd445c582b375c4076/vs_community.exe"

    path_mods = {
        "system" : {
            "x86" : [
                os.path.join('C:\\','Program Files (x86)','Microsoft Visual Studio','2017','Community','VC','Auxiliary','Build'),
            ],
            "x64" : [
                os.path.join('C:\\','Program Files (x86)','Microsoft Visual Studio','2017','Community','VC','Auxiliary','Build'),
            ]
        },
        "local" : {
            "x86" : [
                os.path.join('expected','install','path'),
            ],
            "x64" : [
                os.path.join('expected','install','path'),
            ]
        }
    }

    file_checks = {
        "system" : [
            os.path.join('C:\\','Program Files (x86)','Microsoft Visual Studio','2017','Community','VC','Auxiliary','Build','vcvarsall.bat'),
        ],
        "local" : [
            os.path.join('expected','install','path'),
        ]
    }

    # Install script to use in case the tool isn't already available and must be installed.
    install_script = '''
    '''
