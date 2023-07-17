# Usage

<!-- Jupyter Sphinx setup -->

```{jupyter-execute}
:hide-code:

import os
from tempfile import TemporaryDirectory
tmp_dir = TemporaryDirectory()
os.chdir(tmp_dir.name)
```

## Background

DataLogger is designed to log data from graph-based experiments, where routines and
measurements belong to nodes in a graph. Each log is stored within a node directory, which
is stored within a graph directory, which is stored within a root directory.

Each log, node, and graph are also tagged with a commit ID from a
[ParamDB](https://paramdb.readthedocs.io) database to keep a record of what parameters
were used to generate them.

## Setup

To begin logging data, we first need to create a ParamDB database with some commits so
our logs can be tagged with commit IDs.

```{jupyter-execute}
from paramdb import ParamDB

param_db = ParamDB[str]("param.db")

for i in range(5):
    param_db.commit(f"Commit {i + 1}", "contents")
```

Next, we create a {py:class}`DataLogger` object, passing the ParamDB database and the name
of the root directory to save logs within.

```{jupyter-execute}
from datalogger import DataLogger

data_logger = DataLogger(param_db, "data_logs")
```

If we list the contents of the working directory, we can see that the directory data_logs
has been created.

```{jupyter-execute}
import os

os.listdir()
```

## Logging Data

A {py:class}`DataLogger` object is used to generate {py:class}`GraphLogger` objects, which
are used to generate {py:class}`NodeLogger` objects, which are used to generate log files.

This nested object structure mirrors the nested directory structure log files are saved
within. We can create a graph and node logger as follows.

```{jupyter-execute}
example_graph_logger = data_logger.graph_logger("example")
```
