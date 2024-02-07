# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.3.1] (Feb 7 2024)

### Added

- Latest source distribution (latest.tar.gz) added to Pages site.
- Support for ParamDB v0.11.0.

## [0.3.0] (Nov 6 2023)

### Added

- `LoggedProp` type hint to indicate class properties that should be logged by
  `Logger.log_props()`.

### Changed

- `Logger.log_props()` only logs properties marked by the `LoggedProp` type hint in the
  object's class.
- `Logger.convert_to_json()` handles Numpy values and Pandas DataFrames, and takes in an
  optional `convert()` function.
- `Logger.log_dict()` and `Logger.log_props()` take in an optional `convert()` function to
  pass to `Logger.convert_to_json()`.

## [0.2.0] (Oct 4 2023)

### Added

- Ability to create sub-`Logger`s with no timestamp using the `timestamp` option.

### Changed

- Sub-`Logger`s without timestamps create their directory as soon as `Logger.directory` is
  first called, rather than when a log is created.

## [0.1.1] (Aug 30 2023)

### Added

- Support for Python 3.9.

## [0.1.0] (Aug 8 2023)

### Added

- Logger class `Logger` to create nested directory structure and log array data,
  dictionaries, and object properties.
- Log classes `DataLog` and `DictLog`, and log metadata class `LogMetadata`.
- Classes `Coord` and `DataVar` to aid in creating a data log.
- Function `load_log()` to load log files.
- Initial documentation website.

[unreleased]: https://github.com/PainterQubits/datalogger/compare/v0.3.1...main
[0.3.1]: https://github.com/PainterQubits/datalogger/releases/tag/v0.3.1
[0.3.0]: https://github.com/PainterQubits/datalogger/releases/tag/v0.3.0
[0.2.0]: https://github.com/PainterQubits/datalogger/releases/tag/v0.2.0
[0.1.1]: https://github.com/PainterQubits/datalogger/releases/tag/v0.1.1
[0.1.0]: https://github.com/PainterQubits/datalogger/releases/tag/v0.1.0
