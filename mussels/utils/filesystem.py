"""
Copyright (C) 2026 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

This module provides cross-platform filesystem helpers.

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

import os
import platform
import shutil
import stat


def _remove_readonly(function, path, exception_info):
    """
    Make a read-only Windows path writable and retry its removal.
    """
    exception = exception_info[1]
    if platform.system() != "Windows" or not isinstance(exception, PermissionError):
        raise exception

    os.chmod(path, os.stat(path).st_mode | stat.S_IWRITE)
    function(path)


def remove_tree(path):
    """
    Remove a directory tree, including read-only files on Windows.
    """
    shutil.rmtree(path, onerror=_remove_readonly)
