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
experiments. These logs are stored in files (NetCDF for array data and JSON for
dictionary data). The log files are organized within a nested directory structure and
tagged with metadata, such as timestamp or optionally a commit ID from a [ParamDB]
database.

The original purpose of DataLogger was to store logs from graph calibrations, where
directories correspond to nodes in a graph, so the examples are based on this
application. However, the core functionality is very general.

## Logging Data

### Root Logger

To log data, we first have to create a root {py:class}`Logger` object, passing the name
of the root directory.

```{jupyter-execute}
from datalogger import Logger

root_logger = Logger("data_logs")
```

Our current working directory now contains a directory called `data_logs`.

```{jupyter-execute}
:hide-code:

display_tree("data_logs")
```

```{note}
The root {py:class}`Logger` should typically be defined in one place, and passed or
imported to parts of the code that use it.
```

### Sub-Loggers

We can then create a sub-{py:class}`Logger` objects, which will correspond to a
particular calibration graph and node.

```{jupyter-execute}
graph_logger = root_logger.sub_logger("calibration_graph")
node_logger = graph_logger.sub_logger("q1_spec_node")
```

These will correspond to subdirectories within the root directory.

````{note}
Unlike the root {py:class}`Logger`, the directories for sub-{py:class}`Logger`s are only
created when the first log file is created within them. So the current directory
structure has not changed yet.

```{jupyter-execute}
:hide-code:

display_tree("data_logs")
```

The reason for this is that each log subdirectory contains a timestamp in its name, so
this way the timestamp will generally reflect the time that the first log within the
subdirectory was created.
````

### Data Logs

The first type of log that can be created is a data log, which contains multidimensional
array data. This type of log stores data in an [`xarray.Dataset`], which contains data
variables, coordinates, and attributes.

```{seealso}
To learn more about Xarray data, see [Data Structures] in the Xarray user guide.
```

To aid in creating [`xarray.Dataset`] objects and to enforce certain conventions,
DataLogger provides {py:class}`Coord` as a wrapper for an Xarray coordinate and
{py:class}`DataVar` as a wrapper for a Xarray data variable. We can create a data log
using these objects.

[ParamDB]: https://paramdb.readthedocs.io
[`xarray.Dataset`]: https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html
[Data Structures]: https://docs.xarray.dev/en/stable/user-guide/data-structures.html
