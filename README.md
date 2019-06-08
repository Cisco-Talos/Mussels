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

* Ability to specify "Debug" or "Release" builds
  * Debug builds should also include copying .pdb files to the out/install directory (Windows)
* Ability to specify Platform Toolset (i.e. v141 / 14.1) in recipe build script & as a version requirement.
  * It may make sense to create the platform toolset as a tool which adds a build script variable.
    * Should tools have the ability to add new build script variables?
* Ability to package release materials (zip/tarball per "application")
  * An "application" would be a recipe that includes "bin" install materials.
  * A release package would include install files for the recipe and all dependencies.
  * A release package should include license & configuration files/directories for the recipe and each dependency.
* Recipes to build common libraries on non-Windows systems.
* Recipes should install their licenses.  
  * Maybe a new "license" directory next to "include", "lib", "bin".
* There should be an option to build just one architecture (eg. "x64").
