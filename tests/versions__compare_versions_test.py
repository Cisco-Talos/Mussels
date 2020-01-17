"""
Copyright (C) 2019-2020 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

Tests for versions.py utility functions

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

import json
import os
import unittest

import pytest

from mussels.utils.versions import *


class TestClass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_compare_versions_lt_0(self):
        assert compare_versions("0.0.1", "0.0.2") == -1

    def test_compare_versions_eq_0(self):
        assert compare_versions("0.0.1", "0.0.1") == 0

    def test_compare_versions_gt_0(self):
        assert compare_versions("0.0.2", "0.0.1") == 1

    def test_compare_versions_lt_1(self):
        assert compare_versions("0.0.2", "0.2.1") == -1

    def test_compare_versions_eq_1(self):
        assert compare_versions("0.2.1", "0.2.1") == 0

    def test_compare_versions_gt_1(self):
        assert compare_versions("0.2.2", "0.0.3") == 1

    def test_compare_versions_lt_2(self):
        assert compare_versions("1.0.2g", "1.1.1c") == -1

    def test_compare_versions_eq_2(self):
        assert compare_versions("1.0.2g", "1.0.2g") == 0

    def test_compare_versions_gt_2(self):
        assert compare_versions("1.1.1a", "1.0.2s") == 1

    def test_compare_versions_lt_3(self):
        assert compare_versions("0.101.0_1", "0.102.0_0") == -1

    def test_compare_versions_eq_3(self):
        assert compare_versions("0.101.0_1", "0.101.0_1") == 0

    def test_compare_versions_gt_3(self):
        assert compare_versions("0.102.0_1", "0.101.0") == 1

    def test_compare_versions_gt_beta_0(self):
        assert compare_versions("0.102.0", "0.101.0-beta") == 1

    def test_compare_versions_gt_beta_1(self):
        assert compare_versions("0.102.0-beta", "0.101.0") == 1


if __name__ == "__main__":
    pytest.main(args=["-v", os.path.abspath(__file__)])
