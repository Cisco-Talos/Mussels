"""
Copyright (C) 2026 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

Tests for deterministic recipe patch application.

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

from pathlib import Path

from mussels import recipe as recipe_module
from mussels.recipe import BaseRecipe


class PatchOrderRecipe(BaseRecipe):
    name = "patch-order"
    version = "1.0"
    source = {"none": True}
    platforms = {
        "test": {
            "host": {
                "build_script": {},
                "dependencies": [],
                "patches": "patches",
                "required_tools": [],
            }
        }
    }


def test_recipe_patches_are_applied_in_filename_order(tmp_path, monkeypatch):
    patch_dir = tmp_path / "patches"
    patch_dir.mkdir()
    PatchOrderRecipe.module_file = str(tmp_path / "recipe.yaml")

    applied_patches = []

    class SuccessfulPatch:
        def apply(self, strip, root):
            return True

    def load_patch(path):
        applied_patches.append(Path(path).name)
        return SuccessfulPatch()

    monkeypatch.setattr(
        recipe_module.os,
        "listdir",
        lambda path: ["0002-second.patch", "0001-first.patch"],
    )
    monkeypatch.setattr(recipe_module.patch, "fromfile", load_patch)

    recipe = PatchOrderRecipe(
        toolchain={},
        platform="test",
        target="host",
        install_dir=str(tmp_path / "install"),
        data_dir=str(tmp_path),
        work_dir=str(tmp_path / "work"),
        log_dir=str(tmp_path / "logs"),
        download_dir=str(tmp_path / "downloads"),
    )
    recipe.builds = {}
    recipe.variables = {}
    monkeypatch.setattr(recipe, "_install", lambda: True)

    try:
        assert recipe.build()
        assert applied_patches == ["0001-first.patch", "0002-second.patch"]
    finally:
        for handler in recipe.logger.handlers[:]:
            handler.close()
            recipe.logger.removeHandler(handler)
