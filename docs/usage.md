# Usage

```{py:currentmodule} datalogger

```

<!-- Jupyter Sphinx setup -->

```{jupyter-execute}
:hide-code:

import os
from tempfile import TemporaryDirectory
from directory_tree import display_tree

tmp_dir = TemporaryDirectory()
os.chdir(tmp_dir.name)
```

## Background

DataLogger is Python package to log array and dictionary data from scientific
experiments. These logs are stored in files (netCDF for array data and JSON for
dictionary data). The log files are organized within a nested directory structure and
tagged with metadata, such as timestamp or optionally a commit ID from a [ParamDB]
database.

The original purpose of DataLogger was to store logs from graph calibration experiments,
where directories correspond to nodes in a graph, so the examples below are based on this
application. However, the core functionality is very general.

## Logger Setup

### Root Logger

To log data, we first have to create a root {py:class}`Logger` object, passing the path
(either relative or absolute) to the root directory. This directory will be created if it
does not exist.

```{jupyter-execute}
from datalogger import Logger

root_logger = Logger("data_logs")
```

Our current working directory now contains a directory called `data_logs`.

```{jupyter-execute}
:hide-code:

display_tree("data_logs")
```

```{tip}
The root {py:class}`Logger` should typically be defined in one place, and passed or
imported to parts of the code that use it.
```

### Sub-Loggers

We can also create sub-{py:class}`Logger` objects, which will correspond to subdirectories
within the root directory. By default, a sub-{py:class}`Logger` creates a new directory
with a timestamp. However, using the `timestamp` argument, it is possible to create
sub-{py:class}`Logger`s that, just like root loggers, contain no timestamp and immediately
create their directory if it does not exist.

For example, here we create a sub-{py:class}`Logger` with no timestamp to contain all
calibration experiments, and then timestamped sub-{py:class}`Logger`s to run a particular
experiment graph containing one node.

```{jupyter-execute}
calibration_logger = root_logger.sub_logger("calibrations", timestamp=False)
graph_logger = calibration_logger.sub_logger("calibration_graph")
node_logger = graph_logger.sub_logger("q1_spec_node")
```

We can see that the directory `calibrations` is created immediately, while the timestamped
directories are not created yet.

```{jupyter-execute}
:hide-code:

display_tree("data_logs")
```

```{important}
Sub-{py:class}`Logger`s with timestamps wait to create their directories until their
directory path is accessed, either explicitly via {py:attr}`Logger.directory` or
internally, e.g. to create a log file.

This is done so that timestamps in directory names can reflect when the first file within
them was created (often when that part of the experiment is being run), not when the
{py:class}`Logger` object was created (often when the entire experiment is being set up).
```

## Logging

### Data Logs

The first type of log that can be created is a data log, which contains multidimensional
array data. This type of log stores data in an [`xarray.Dataset`], which contains data
variables, coordinates, and attributes. The log is saved to a [netCDF] file via
[`xarray.Dataset.to_netcdf()`].

```{seealso}
To learn more about Xarray data, see [Data Structures] in the Xarray user guide.
```

To aid in creating [`xarray.Dataset`] objects and to enforce certain conventions,
DataLogger provides {py:class}`Coord` as a wrapper for an Xarray coordinate and
{py:class}`DataVar` as a wrapper for a Xarray data variable. We can create a data log
using these objects and {py:meth}`Logger.log_data`.

```{jupyter-execute}
from datalogger import Coord, DataVar

times = [1, 2, 3]
signal = [10, 20, 30]

node_logger.log_data(
    "q1_spec_signal",
    [Coord("time", data=times, long_name="Time", units="s")],
    [DataVar("signal", dims="time", data=signal, long_name="Signal", units="V")],
)
```

The directories for the graph and node have now been created, along with the netCDF log
file.

```{jupyter-execute}
:hide-code:

display_tree("data_logs")
```

### Dictionary Logs

Dictionary logs store `dict` data in JSON files. The data stored in the dictionary log
will be converted to JSON-serializable types according to
{py:meth}`Logger.convert_to_json`. We can create a dictionary log using
{py:meth}`Logger.log_dict`.

```{jupyter-execute}
node_logger.log_dict(
    "q1_spec_frequency",
    {"f_rf": 3795008227, "f_if": 95008227, "f_lo": 3700000000},
)
```

The log file has now been created within the node directory.

```{jupyter-execute}
:hide-code:

display_tree("data_logs")
```

### Property Logs

Property logs automatically store the properties of an object within a dictionary log.
Only properties marked with the type hint {py:class}`~datalogger._logger.LoggedProp` will
be saved. We can create a property log using {py:meth}`Logger.log_props`.

```{note}
{py:class}`LoggedProp` can optionally take in a type parameter representing the type of
the variable, which is only used by code analysis tools.
```

```{jupyter-execute}
from typing import Optional
from datalogger import LoggedProp

class SpecNode:
    _element: LoggedProp
    xy_f_rf: LoggedProp[int]
    xy_f_if: LoggedProp[Optional[int]]

    def __init__(self, element: str) -> None:
        self._element = element
        self.xy_f_rf = 379500822
        self.xy_f_if = None
        self.xy_f_lo = 3700000000

q1_spec_node = SpecNode("q1")

node_logger.log_props("q1_spec_node_props", q1_spec_node)
```

The log file has now been created within the node directory.

```{jupyter-execute}
:hide-code:

display_tree("data_logs")
```

## Loading

Logs can be loaded by passing a file path to {py:func}`load_log`. We can also use
{py:meth}`Logger.file_path` to aid in creating the file paths to logs. (The full path can
also be passed in directly if known.)

```{jupyter-execute}
from datalogger import load_log

q1_spec_signal_log = load_log(node_logger.file_path("q1_spec_signal.nc"))
q1_spec_frequency_log = load_log(node_logger.file_path("q1_spec_frequency.json"))
q1_spec_node_props_log = load_log(node_logger.file_path("q1_spec_node_props.json"))
```

Alternatively, logs can be loaded using {py:class}`DataLog` for data logs or
{py:class}`DictLog` for dictionary logs. This is not necessary since {py:func}`load_log`
already infers the log type from the file extension, but is useful for static type
checking when the log type is known.

```{jupyter-execute}
from datalogger import DataLog, DictLog

q1_spec_signal_log = DataLog.load(node_logger.file_path("q1_spec_signal.nc"))
q1_spec_frequency_log = DictLog.load(node_logger.file_path("q1_spec_frequency.json"))
q1_spec_node_props_log = DictLog.load(node_logger.file_path("q1_spec_node_props.json"))
```

### Accessing Data

Logs are represented as objects ({py:class}`DataLog` or {py:class}`DictLog` depending on
the log type). Data can be accessed using {py:attr}`DataLog.data` or
{py:attr}`DictLog.data`.

For a {py:class}`DataLog`, data is returned as an [`xarray.Dataset`] object.

```{jupyter-execute}
q1_spec_signal_log.data
```

For a {py:class}`DictLog`, data is returned as a dictionary.

```{jupyter-execute}
q1_spec_frequency_log.data
```

### Accessing Metadata

Metadata is also loaded in and can be accessed using {py:attr}`DataLog.metadata` or
{py:attr}`DictLog.metadata`. Metadata is stored using a {py:class}`LogMetadata` object.

```{jupyter-execute}
q1_spec_signal_log.metadata
```

Metadata properties can be accessed as properties of this object. For example, we can get
the timestamp using {py:attr}`LogMetadata.timestamp`.

```{jupyter-execute}
q1_spec_signal_log.metadata.timestamp
```

## ParamDB Integration

Optionally, a [`ParamDB`] can be passed to a root {py:class}`Logger`, in which case it
will be used to automatically tag logs with the latest commit ID.

```{jupyter-execute}
from paramdb import ParamDB

param_db = ParamDB[int]("param.db")
param_db.commit("Initial commit", 123)

root_logger = Logger("data_logs", param_db)
graph_logger = root_logger.sub_logger("calibration_graph")
node_logger = graph_logger.sub_logger("q1_spec_node")

node_logger.log_dict(
    "q1_spec_frequency",
    {"f_rf": 3795008227, "f_if": 95008227, "f_lo": 3700000000},
)
```

<!-- Jupyter Sphinx cleanup -->

```{jupyter-execute}
:hide-code:

param_db.dispose()  # Fixes PermissionError on Windows
```

[ParamDB]: https://paramdb.readthedocs.io/en/stable/
[`xarray.Dataset`]: https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html
[netCDF]: https://www.unidata.ucar.edu/software/netcdf/
[`xarray.Dataset.to_netcdf()`]: https://docs.xarray.dev/en/latest/generated/xarray.Dataset.to_netcdf.html
[Data Structures]: https://docs.xarray.dev/en/stable/user-guide/data-structures.html
[`JSONEncoder`]: https://docs.python.org/3/library/json.html#json.JSONEncoder
[`vars()`]: https://docs.python.org/3/library/functions.html#vars
[`ParamDB`]: https://paramdb.readthedocs.io/en/stable/api-reference.html#paramdb.ParamDB
