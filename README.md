# Mussels

```
  __    __     __  __     ______     ______     ______     __         ______
 /\ "-./  \   /\ \/\ \   /\  ___\   /\  ___\   /\  ___\   /\ \       /\  ___\
 \ \ \-./\ \  \ \ \_\ \  \ \___  \  \ \___  \  \ \  __\   \ \ \____  \ \___  \
  \ \_\ \ \_\  \ \_____\  \/\_____\  \/\_____\  \ \_____\  \ \_____\  \/\_____\
   \/_/  \/_/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/   \/_____/
```

A tool to download, build, and assemble application dependencies.
                                    Brought to you by the Clam AntiVirus Team.

Copyright (C) 2019 Cisco Systems, Inc. and/or its affiliates. All rights reserved.

## License

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

## Example Usage

Get help:

> `python mussels.py --help`
> `python mussels.py build --help`

View all available recipes:

> `python mussels.py list`

Perform a dry-run to view order in which dependency graph will be build all recipes:

> `python mussels.py build -d`

Perform a dry-run to view order in which dependency graph will be build a specific recipe:

> `python mussels.py build -r openssl -d`

Build a specific version of a recipe:

> `python mussels.py build -r openssl -v 1.1.0j`

## To-do

The following are issues or features on the to-do list to implement or repair.

* Add ability to specify "Debug" or "Release" builds
  * Debug builds should also include copying .pdb files to the out/install directory (Windows)
* Add ability to specify Platform Toolset (i.e. v141 / 14.1) in recipe build script & as a version requirement.
  * It may make sense to create the platform toolset as a tool which adds a build script variable.
    * Should tools have the ability to add new build script variables?
* Add ability to package release materials (zip/tarball per "application")
  * An "application" would be a recipe that includes "bin" install materials.
  * A release package would include install files for the recipe and all dependencies.
  * A release package should include license & configuration files/directories for the recipe and each dependency.
* Recipes should install their licenses.
  * Maybe each should install a "license" directory alongside "include", "lib", "bin".
* There should be an option to build just one architecture (eg. "x86", or "cross-..."). The default should be "host" or the current system architecture.
* Currently recipes install to a single path (out/install).  It should be possible to install to out/install/{recipe}/{version} instead.  This will require careful design, as each recipe must still be able to pass the path for their dependencies when they configure.
* Separate the "configure" and "build" steps into separate scripts.  Not all recipes will have a "configure" or a "build" step.  That's ok.
* Add build `--clean` option.  A clean build always deletes the work directory and starts over.  The default behavior should be that the work directory is not deleted just because the previous build did not succeed, and the "configure" step is skipped if the work directory already exists.
* Add build `--dev` option.  A dev build always runs the "build" step for the primary build target, even if the output binaries already exist in the out/install directory.
* Add build `--deploy` option that copies the primary build target install files as well as the "lib" and "license" files for each of its dependencies to a specified directory, collocating all libraries and binaries in one directory.
