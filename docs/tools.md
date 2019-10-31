# Tools

Tools are simple YAML files that must adhere to the following format:

```yaml
name: template_tool
version: "0.1"
mussels_version: "0.1"
type: tool
platforms:
  <platform>:
    path_checks:
      - template_tool
    command_checks:
      - command: "<any shell command>"
        output_has: "<optional output check>"
    file_checks:
      - </path/to/check/1>
      - </path/to/check/2>
```

## Tool Fields, in Detail

### `name`

The name of the program this tool detects.

_Tip_: Mussels tool names may not include the following characters: `-`, `=`, `@`, `>`, `<`, `:`. Instead, consider the humble underscore `_`.

### `version`

The tool version _string_ is generally expected to follow traditional semantic versioning practices (i.e `"<major>.<minor>.<patch>"`), though any alpha-numeric version string should be fine. So long as the format is consistent across multiple versions, Mussels should be able to compare version strings for a given tool.

Tools, unlike recipes, may omit the version number if no specific version is needed.

### `mussels_version`

This version string defines which version of Musssels the tool is written to work with.  It is also the key used by Mussels to differentiate Mussels YAML files from any other YAML file.

The value must be `"0.1"`

### `type`

Tool type must be set to `tool`:

### `platforms`

The platforms dictionary allows you to define instructions to identify tools for different host platforms all in one file.

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

### Checks

There are 3 ways to check if a tool exists.  If any one of these pass, then the tool is "detected":

- `path_checks`:

  The `path_checks` are a way to check if an executable exists in the PATH. This check will look in the pATH directories for the executable name. If found, the check passes.

- `command_checks`

  The `command_checks` are a way to run a `command` and verify the result.  If the `command` exit code is `0` and the `output_has` string is found within the `command` output, then the check passes.

  `output_has` may be an empty string, in which case only the exit code needs to be `0` for the check to pass.

- `file_checks`

  The `file_checks` are a list of absolute paths to executables.  If any one of these exist, then the tool will be "detected".  At build time, the path where the executable was found will be added to the PATH environment variable.

## Example Tool Definition

This tool, copypasted from the `scrapbook` defines how to find CMake.

Several notable things about this tool...

The tool provides instructions for 2 platforms: Posix, and Windows. Posix was chosen rather than something more specific because the means to identify CMake on POSIX systems are generally the same.

For Windows, it this tool definition merely checks for the existance of the `cmake.exe` program.  If found, the directory will be added to the `%PATH%` environment variable at build time.

For Posix systems, this tool will check first if `cmake` is in the `$PATH` already.  If that fails, it will check if the executable `cmake` exists in either `/usr/local/bin` or `/usr/bin`.  As with the Windows platform, it would add the directories to the `$PATH` at build time, if found - though in this case those directories will probably already be in the `$PATH`.

```yaml
name: cmake
version: ""
mussels_version: "0.1"
type: tool
platforms:
  Posix:
    path_checks:
      - cmake
    file_checks:
      - /usr/local/bin/cmake
      - /usr/bin/cmake
  Windows:
    file_checks:
      - C:\/Program Files/CMake/bin/cmake.exe
```

If a specific version of CMake was needed, a tool definition could be written to identify it using the `command_checks` field.

For example:

```yaml
name: cmake
version: "3.14"
mussels_version: "0.1"
type: tool
platforms:
  Posix:
    command_checks:
      - command: "cmake --version"
        output_has: "cmake version 3.14"
  Windows:
    command_checks:
      - command: "cmake.exe --version"
        output_has: "cmake version 3.14"
      - command: "C:\/Program Files/CMake/bin/cmake.exe --version"
        output_has: "cmake version 3.14"
```
