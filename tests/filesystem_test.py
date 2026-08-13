"""
Copyright (C) 2026 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

Tests for cross-platform filesystem helpers.

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

import stat
from unittest.mock import Mock, patch

import pytest

from mussels.utils.filesystem import _remove_readonly, remove_tree


@patch("mussels.utils.filesystem.shutil.rmtree")
def test_remove_tree_uses_readonly_handler(rmtree):
    remove_tree("example")

    rmtree.assert_called_once_with("example", onerror=_remove_readonly)


@patch("mussels.utils.filesystem.platform.system", return_value="Windows")
@patch("mussels.utils.filesystem.os.chmod")
@patch("mussels.utils.filesystem.os.stat")
def test_remove_readonly_retries_on_windows(path_stat, chmod, system):
    path_stat.return_value.st_mode = stat.S_IREAD
    remove = Mock()
    error = PermissionError("read-only")

    _remove_readonly(remove, "example", (PermissionError, error, None))

    chmod.assert_called_once_with("example", stat.S_IREAD | stat.S_IWRITE)
    remove.assert_called_once_with("example")


@patch("mussels.utils.filesystem.platform.system", return_value="Linux")
def test_remove_readonly_preserves_posix_error(system):
    error = PermissionError("permission denied")

    with pytest.raises(PermissionError) as raised:
        _remove_readonly(Mock(), "example", (PermissionError, error, None))

    assert raised.value is error


@patch("mussels.utils.filesystem.platform.system", return_value="Windows")
def test_remove_readonly_preserves_other_windows_errors(system):
    error = OSError("file is busy")

    with pytest.raises(OSError) as raised:
        _remove_readonly(Mock(), "example", (OSError, error, None))

    assert raised.value is error
