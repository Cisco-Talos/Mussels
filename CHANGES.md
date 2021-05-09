# Notable Changes

> _Note_: Changes should be grouped by release and use these icons:
> - Added: ➕
> - Changed: 🌌
> - Deprecated: 👇
> - Removed: ❌
> - Fixed: 🐛
> - Security: 🛡

## Version 0.3.0

### Added

➕ Added the ability to define variables in tools that can be accessed in recipes.

  To define variables, add a `variables` list for each platform.

  This feature was inspired by a need to make recipes that have strings in them specific to a given tool version. Specifically we'll be using this to define CMake generator names in Visual Studio tool YAML files. The correct generator name for a given Visual Studio version will then be available for use in recipes that use Visual Studio.

  Example tool, `visualstudio-2017.yaml`:

  ```yaml
  name: visualstudio
  version: "2017"
  mussels_version: "0.3"
  type: tool
  platforms:
    Windows:
      file_checks:
        - C:\/Program Files (x86)/Microsoft Visual Studio/2017/Professional/VC/Auxiliary/Build/vcvarsall.bat
        - C:\/Program Files (x86)/Microsoft Visual Studio/2017/Enterprise/VC/Auxiliary/Build/vcvarsall.bat
        - C:\/Program Files (x86)/Microsoft Visual Studio/2017/Community/VC/Auxiliary/Build/vcvarsall.bat
      variables:
        cmake_generator: Visual Studio 15 2017
  ```

  Example recipe, `libz.yaml`:

  ```yaml
  name: libz
  version: "1.2.11"
  url: https://www.zlib.net/zlib-1.2.11.tar.gz
  mussels_version: "0.3"
  type: recipe
  platforms:
    Windows:
      x64:
        build_script:
          configure: |
            CALL cmake.exe -G "{visualstudio.cmake_generator} Win64"
          make: |
            CALL cmake.exe --build . --config Release
        dependencies: []
        install_paths:
          include:
            - zlib.h
            - zconf.h
          lib:
            - Release/zlibstatic.lib
          license/zlib:
            - README
        required_tools:
          - cmake
          - visualstudio>=2017
  ```

🐛 Fixed a crash caused by a failure to properly decode command output text from some locales to utf8.

## Version 0.2.1

➕ Added the Mussels version string to the `msl --help` output.

➕ Added `msl build` options allowing users to customize the work, logs, and downloads directories:
- `-w`, `--work-dir TEXT`      Work directory. The default is: ~/.mussels/cache/work
- `-l`, `--log-dir TEXT`       Log directory. The default is: ~/.mussels/logs
- `-D`, `--download-dir TEXT`  Downloads directory. The default is: ~/.mussels/cache/downloads

🐛 The `msl build -c` shorthand for `--cookbook` was overloaded by the `--clean` (`-c`) shorthand. Because `--cookbook` (`-c` ) is also used elsewhere, the `--clean` option was renamed to `--rebuild` (`-r`).

🐛 Fixed an issue where the list of available tools was being limited based on _all_ recipe tool version requirements rather than just those found in the dependency chain.

## Version 0.2.0

➕ Added the `msl build` `--install`/`-i` option, allowing builds to install directly to a directory of the user's choosing.

🌌 The `{install}` build script variable now points to the full install prefix, including the target architecture directory when building with the default install directory (eg: `host`, `x86`, `x64`, etc).

This was necessary in order for the `--install` option to make sense. This also simplifies recipes because they no longer have to specify "`{install}/{target}`" to reference the install directory. This, unfortunately, also makes it a breaking change. All recipes will have to remove the "`/{target}`" to remain compatible.

## Version 0.1.0

➕ First release!
