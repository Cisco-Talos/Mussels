"""
Copyright (C) 2021 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

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
import logging
import multiprocessing
import os
import unittest
import tempfile
import shutil
import sys
import platform
from pathlib import Path
import http.server
import socketserver
from multiprocessing import Process, Pipe
import tarfile
import time

import pytest

from mussels.mussels import Mussels

def execute_build(stdout, stderr):
    sys.stdout = stdout.fileno()
    sys.stderr = stderr.fileno()

    my_mussels = Mussels(
        install_dir=os.getcwd(),
        work_dir=os.getcwd(),
        log_dir=os.getcwd(),
        download_dir=os.getcwd(),
    )

    results = []

    success = my_mussels.build_recipe(
        recipe="foobar",
        version="",
        cookbook="",
        target="host",
        results=results,
        dry_run=False,
        rebuild=False
    )

    stdout.send("The End")
    stdout.close()
    stderr.close()

    if success == False:
        sys.exit(1)

    sys.exit(0)

def host_server():
    '''
    Host files in the current directory on port 8000.
    '''
    PORT = 8000
    Handler = http.server.SimpleHTTPRequestHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()


class TC(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        TC.path_tmp = Path(tempfile.mkdtemp(prefix="msl-test-"))
        TC.savedir = os.getcwd()
        os.chdir(str(TC.path_tmp))

        (TC.path_tmp / "foo.yaml").write_text(f'''
name: python
version: "3"
mussels_version: "0.3"
type: tool
platforms:
  Posix:
    file_checks:
      - {sys.executable}
    variables:
      foo: Hello World!
  Windows:
    file_checks:
      - {sys.executable}
    variables:
      foo: Hello World!
''')

        # Make a foo.tar.gz package that the recipe build can download & extract.
        (TC.path_tmp / 'foo').mkdir()
        (TC.path_tmp / 'foo' / "foo.txt").write_text("Hello, World!\n")
        with tarfile.open(str(TC.path_tmp / "foo.tar.gz"), "w:gz") as tar:
            tar.add("foo")

        TC.p = Process(target=host_server)
        TC.p.start()

    @classmethod
    def tearDownClass(cls):
        TC.p.terminate()
        TC.p.kill()
        os.chdir(TC.savedir)
        shutil.rmtree(str(TC.path_tmp))

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_0_basic_variable(self):
        (TC.path_tmp / "foobar.yaml").write_text('''
name: foobar
version: "1.2.3"
url: https://www.example.com/foo.tar.gz
mussels_version: "0.3"
type: recipe
platforms:
  Posix:
    host:
      build_script:
        make: |
          echo "{python.foo}"
      dependencies: []
      required_tools:
        - python
  Windows:
    host:
      build_script:
        make: |
          echo "{python.foo}"
      dependencies: []
      required_tools:
        - python
''')

        my_mussels = Mussels(
            install_dir=os.getcwd(),
            work_dir=os.getcwd(),
            log_dir=os.getcwd(),
            download_dir=os.getcwd(),
            log_level="DEBUG"
        )

        results = []

        success = my_mussels.build_recipe(
            recipe="foobar",
            version="",
            cookbook="",
            target="host",
            results=results,
            dry_run=False,
            rebuild=False
        )

        logging.shutdown()

        # Find the foobar log
        for i in os.listdir(str(TC.path_tmp)):
            if (TC.path_tmp / i).is_file() and i.startswith('foobar-1.2.3'):
                text = (TC.path_tmp / i).read_text()
                break

        print(f"Checking for 'Hello World!' in:\n\n{text}")

        assert "Hello World!" in text

if __name__ == "__main__":
    pytest.main(args=["-v", os.path.abspath(__file__)])
