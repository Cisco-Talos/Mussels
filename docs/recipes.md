# Recipes

Recipes are simple YAML files that must adhere to the following format:

```yaml
name: template
version: "0.1"
url: "hxxps://www.example.com/releases/v0.1.tar.gz"
archive_name_change: # Optional; delete if not needed.
  - v0.1         # search pattern
  - template-0.1 # replace pattern
mussels_version: "0.1"
type: recipe
platforms:
  <platform>:
    <target>:
      build_script:
        configure: |
          < a shell script to configure prior to build >
        make: |
          < a shell script to build the software >
        install: |
          < a shell script to install the software >
      dependencies: []
      install_paths:
        <install location>:
          - <files or directories to be copied to the install location>
          - <files or directories to be copied to the install location>
          - <files or directories to be copied to the install location>
      patches: <patch directory>   # Optional; delete if not needed.
      required_tools:
        - <names of tools required for the build>
        - <names of tools required for the build>
        - <names of tools required for the build>
```

## Recipe Fields, in Detail

### `name`

The name of the library or application this recipe builds.

_Tip_: Mussels recipe names may not include the following characters: `-`, `=`, `@`, `>`, `<`, `:`. Instead, consider the humble underscore `_`.

### `version`

The recipe version _string_ is generally expected to follow traditional semantic versioning practices (i.e `"<major>.<minor>.<patch>"`), though any alpha-numeric version string should be fine. So long as the format is consistent across multiple versions, Mussels should be able to compare version strings for a given recipe.

### `url`

The URL to be used to download a TAR or ZIP archive containing the source code to be built.

In the future, we would like to add support for local paths and Git repositories, but for the moment this must be a URL ending in `.tar.gz` or `.zip`.

### `archive_name_change` (optional)

This _optional_ field exists because some software packages are provided in zips or tarballs that have been renamed after creation, meaning that after extraction the resulting director does not have the same prefix as the original archive.

The `archive_name_change` list field should have 2 items:

- The "search pattern"
- The "replace pattern"

When downloaded, an archive will be renamed to replace the "search pattern" with the "replace pattern", thereby reverting the archive to it's true/original name so that when extracted - the resulting directory name will match the archive.

### `mussels_version`

This version string defines which version of Musssels the recipe is written to work with.  It is also the key used by Mussels to differentiate Mussels YAML files from any other YAML file.

The value must be `"0.1"`

### `type`

Recipe type can either be one of:

- `recipe`
- `collection`

What is the difference between a `recipe` and a `collection`?  Recipes have the `url` field, and include the fields `build_script`, `install_paths`, `patches`, and `required_tools`.  Collections don't include any of the above. Collections just provide the `dependencies` lists.

### `platforms`

The platforms dictionary allows you to define build instructions for different host platforms all in one file.

The `<platform>` keys under `platforms` may be one of the following^:

- Darwin / macOS / OSX
- Windows
- Linux
- Unix ( Darwin, FreeBSD, OpenBSD, SunOS, AIX, HP-UX )
- Posix ( Unix and Linux )
- FreeBSD
- OpenBSD
- SunOS
- AIX
- HP-UX

### `target`

Each `platform` under `platforms` is itself also a dictionary and may contain one or more `<target>` keys.

Each `target` represents the built target architecture.  On Posix systems, Mussels' default target is `host` and on Windows, it is the current architecture (either `x64` or `x86`).

However, you may define the `<target>` name to be anything you like, representing the architecture of the machine intended to run the built software.

The `target` name must be provided by every dependency of your recipes for the given `platform`.

### `build_script`

The `build_script` dictionary provides up to three (3) scripts used to build the software.  On Posix systems these are each written to a shell script and executed, and on Windows these are written to a batch (.bat) scripts and executed.

These three scripts are each optional, but must be named as follows::

- `configure` - Configure the build, only run the first time a build is run. This script is only run the first time you build a package and is skipped in subsequent builds so as to save compile time.  If you need to re-run this step, build the recipe with the `msl build --clean` option.

  In many recipes, this step sets the "prefix" to the `{install}/{target}` directory, so the resulting binaries are automatically copied there when the `install` step runs `make install`.

- `make` - Build the software.

- `install` - Install the software to the `.mussels/install/{target}` directory

Within the scripts, curly braces are used to identify a few special variables that you may use to reference dependencies or the install path.

Variables available in Mussels 0.1 include:

- `{target}` - The name of the build `target` (i.e. `host` / `x64` / `x86` or whatever you named it.)

- `{build}`

  The build directory, found under `.mussels/cache/work/{target}/<archive prefix>`

- `{install}`

  The `.mussels/install` directory.

- `{includes}`

  Shorthand for the `{install}/{target}/include` directory.

- `{libs}`

  Shorthand for the `{install}/{target}/lib` directory.

### `dependencies`

The `dependencies` list may either be empty (`[]`), meaning no dependencies, or may be a list of other recipes names with version numbers and even cookbooks specified if so desired.

Some fictional examples:

```yaml
      dependencies:
        - meepioux
        - blarghus>=1.2.3
        - wheeple@0.2.0
        - pyplo==5.1.0g
        - "scrapbook:sasquatch<2.0.0"
        - "scrapbook:minnow<0.1.12"
```

### `install_paths`

The `install_paths` provides lists of files and directories to be copied to a specific path under `{install}`.

### `patches` (optional)

This optional field provides the name of a directory provided alongside the recipe YAML file that contains a patch set to be applied to the source before any of the build scripts are run.

### `required_tools`

This list of required tools defines which tools much be present on the host platform in order to do the build.  Like the `dependencies`, these lists may include version numbers and cookbook names in the format:

`[cookbook:]name[>=,<=,>,<,(==|=|@)version]`

Some fictional examples:

```yaml
      required_tools:
        - "scrapbook:pkgfiend<1.1.1"
        - appmaker
```

## Example Recipe Definition

This recipe, copypasted from the `clamav` cookbook defines how to build libpcre2.

Several notable things about this recipe...

The recipe provides instructions for 3 platforms: Darwin, Linux, and Windows.

For Windows, it provides build instructions targeting both `x64` and `x86`, but for the others, it simply provides `host`.

In the `configure` script, the install "prefix" is set for the package in the Linux and Mac recipes.  This is often necessary to configure the software to be used from the install directory.

The Windows instructions omit the `install` script.  All scripts are optional, but the `install` step is often not requires for Windows.  The Darwin and Linux recipes also make use of `install_name_tool` (provided by Clang), and `patchelf` (an additional required tool) to set the RPATH for each executable so that dynamic libraries may be found at runtime.

```yaml
name: pcre2
version: "10.33"
url: https://ftp.pcre.org/pub/pcre/pcre2-10.33.tar.gz
mussels_version: "0.1"
type: recipe
platforms:
  Darwin:
    host:
      build_script:
        configure: |
          ./configure --prefix="{install}/{target}" --disable-dependency-tracking
        make: |
          make
        install: |
          make install
          install_name_tool -add_rpath @executable_path/../lib "{install}/{target}/lib/libpcre2-8.dylib"
      dependencies:
        - bzip2
        - zlib
      install_paths:
        license/pcre2:
          - COPYING
      required_tools:
        - make
        - clang
  Linux:
    host:
      build_script:
        configure: |
          chmod +x ./configure ./install-sh
          ./configure --prefix="{install}/{target}" --disable-dependency-tracking
        make: |
          make
        install: |
          make install
          patchelf --set-rpath '$ORIGIN/../lib' "{install}/{target}/lib/libpcre2-8.so"
      dependencies:
        - bzip2
        - zlib
      install_paths:
        license/pcre2:
          - COPYING
      required_tools:
        - make
        - gcc
        - patchelf
  Windows:
    x64:
      build_script:
        configure: |
          CALL cmake.exe -G "Visual Studio 15 2017 Win64" \
              -DBUILD_SHARED_LIBS=ON \
              -DZLIB_INCLUDE_DIR="{includes}" \
              -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
              -DBZIP2_INCLUDE_DIR="{includes}" \
              -DBZIP2_LIBRARY_RELEASE="{libs}/libbz2.lib"
        make: |
          CALL cmake.exe --build . --config Release
      dependencies:
        - bzip2<1.1.0
        - zlib
      install_paths:
        include:
          - pcre2.h
        lib:
          - Release/pcre2-8.dll
          - Release/pcre2-8.lib
        license/openssl:
          - COPYING
      patches: pcre2-10.33-patches
      required_tools:
        - cmake
        - visualstudio>=2017
    x86:
      build_script:
        configure: |
          CALL cmake.exe -G "Visual Studio 15 2017" \
              -DBUILD_SHARED_LIBS=ON \
              -DZLIB_INCLUDE_DIR="{includes}" \
              -DZLIB_LIBRARY_RELEASE="{libs}/zlibstatic.lib" \
              -DBZIP2_INCLUDE_DIR="{includes}" \
              -DBZIP2_LIBRARY_RELEASE="{libs}/libbz2.lib"
        make: |
          CALL cmake.exe --build . --config Release
      dependencies:
        - bzip2<1.1.0
        - zlib
      install_paths:
        include:
          - pcre2.h
        lib:
          - Release/pcre2-8.dll
          - Release/pcre2-8.lib
        license/openssl:
          - COPYING
      patches: pcre2-10.33-patches
      required_tools:
        - cmake
        - visualstudio>=2017
```
