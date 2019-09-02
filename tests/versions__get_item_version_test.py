"""
Tests for versions.py utility functions
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
        self.sorted_items = {
            "wheeple": [
                {"version": "2.0.0", "cookbooks": ["tectonic"]},
                {"version": "1.0.1", "cookbooks": ["tectonic"]},
                {"version": "1.0.0", "cookbooks": ["tectonic"]},
            ]
        }

    def tearDown(self):
        pass

    def test_get_item_version(self):

        nvc = get_item_version(item_name="wheeple", sorted_items=self.sorted_items)

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "2.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_gt(self):

        nvc = get_item_version(
            item_name="wheeple>1.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "2.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_gt_nexists(self):

        no_item = False
        try:
            nvc = get_item_version(
                item_name="wheeple>2.0.0", sorted_items=self.sorted_items
            )
        except:
            no_item = True

        assert no_item

    def test_get_item_version_gte(self):

        nvc = get_item_version(
            item_name="wheeple>=1.0.1", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "2.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_gte_nexists(self):

        no_item = False
        try:
            nvc = get_item_version(
                item_name="wheeple>=2.0.1", sorted_items=self.sorted_items
            )
        except:
            no_item = True

        assert no_item

    def test_get_item_version_lt(self):

        nvc = get_item_version(
            item_name="wheeple<1.0.1", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "1.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_lt_nexists(self):

        no_item = False
        try:
            nvc = get_item_version(
                item_name="wheeple<1.0.0", sorted_items=self.sorted_items
            )
        except:
            no_item = True

        assert no_item

    def test_get_item_version_eq_0(self):

        nvc = get_item_version(
            item_name="wheeple=1.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "1.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_eq_1(self):

        nvc = get_item_version(
            item_name="wheeple@1.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "1.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_eq_2(self):

        nvc = get_item_version(
            item_name="wheeple==1.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "1.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_eq_3(self):

        nvc = get_item_version(
            item_name="wheeple-1.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "1.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_eq_nexists(self):

        no_item = False
        try:
            nvc = get_item_version(
                item_name="wheeple<1.0.0", sorted_items=self.sorted_items
            )
        except:
            no_item = True

        assert no_item

    def test_get_item_version_book_eq(self):

        nvc = get_item_version(
            item_name="tectonic:wheeple", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))

        assert nvc["name"] == "wheeple"
        assert nvc["version"] == "2.0.0"
        assert nvc["cookbook"] == "tectonic"

    def test_get_item_version_book_eq_nexists(self):

        no_item = False
        try:
            nvc = get_item_version(
                item_name="timtim:wheeple", sorted_items=self.sorted_items
            )
        except:
            no_item = True

        assert no_item

    def test_get_item_version_prune_version_0(self):

        nvc = get_item_version(
            item_name="tectonic:wheeple=1.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))
        print("sorted_items:")
        print(json.dumps(self.sorted_items["wheeple"], indent=4))

        assert len(self.sorted_items["wheeple"]) == 1

    def test_get_item_version_prune_version_1(self):

        nvc = get_item_version(
            item_name="tectonic:wheeple>1.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))
        print("sorted_items:")
        print(json.dumps(self.sorted_items["wheeple"], indent=4))

        assert len(self.sorted_items["wheeple"]) == 2

    def test_get_item_version_prune_version_2(self):

        nvc = get_item_version(
            item_name="tectonic:wheeple>=1.0.1", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))
        print("sorted_items:")
        print(json.dumps(self.sorted_items["wheeple"], indent=4))

        assert len(self.sorted_items["wheeple"]) == 2

    def test_get_item_version_prune_version_3(self):

        nvc = get_item_version(
            item_name="tectonic:wheeple<2.0.0", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))
        print("sorted_items:")
        print(json.dumps(self.sorted_items["wheeple"], indent=4))

        assert len(self.sorted_items["wheeple"]) == 2

    def test_get_item_version_prune_version_4(self):

        nvc = get_item_version(
            item_name="tectonic:wheeple<=1.0.1", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))
        print("sorted_items:")
        print(json.dumps(self.sorted_items["wheeple"], indent=4))

        assert len(self.sorted_items["wheeple"]) == 2

    def test_get_item_version_no_prune_version(self):

        nvc = get_item_version(
            item_name="tectonic:wheeple", sorted_items=self.sorted_items
        )

        print("nvc:")
        print(json.dumps(nvc, indent=4))
        print("sorted_items:")
        print(json.dumps(self.sorted_items["wheeple"], indent=4))

        assert len(self.sorted_items["wheeple"]) == 3


if __name__ == "__main__":
    pytest.main(args=["-v", os.path.abspath(__file__)])
