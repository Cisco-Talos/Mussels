# Notable Changes

Changes in this document should be grouped per release using the following types:

- Added
- Changed
- Deprecated
- Removed
- Fixed
- Security

## Version 0.2.0

### Added

- Added the `msl build` `--install`/`-i` option, allowing builds to install directly to a directory of the user's choosing.

### Changed

- The `{install}` build script variable now points to the full install prefix, including the target architecture directory when building with the default install directory (eg: `host`, `x86`, `x64`, etc).

  This was necessary in order for the `--install` option to make sense. This also simplifies recipes because they no longer have to specify "`{install}/{target}`" to reference the install directory. This, unfortunately, also makes it a breaking change. All recipes will have to remove the "`/{target}`" to remain compatible.

## Version 0.1.0

First release!
