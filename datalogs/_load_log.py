"""Function to load logs from files."""

from __future__ import annotations
import os
from datalogs._logs import DataLog, DictLog


def load_log(path: str) -> DataLog | DictLog:
    """
    Load the log specified by the given file path.

    If the extension is ".nc" (NetCDF), a :py:class:`DataLog` containing an Xarray
    ``Dataset`` will be loaded.

    If the extension is ".json" (JSON), a :py:class:`DictLog` containing a dictionary
    will be loaded.
    """
    ext = os.path.splitext(path)[1].lower()
    log_type: type[DataLog | DictLog]
    if ext == ".nc":
        log_type = DataLog
    elif ext == ".json":
        log_type = DictLog
    else:
        raise ValueError(f"'{ext}' file extension is not supported")
    return log_type.load(path)
