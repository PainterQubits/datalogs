"""Functions to load logs from files."""

from typing import TypeVar
from datalogger._logs import LogMetadata, DataLog, DictLog

# Log type
_LT = TypeVar("_LT", DataLog, DictLog)


def _load_log(log_type: type[_LT], path_or_metadata: str | LogMetadata) -> _LT:
    return log_type.load(path_or_metadata)


def load_data_log(path_or_metadata: str | LogMetadata) -> DataLog:
    """
    Load a data log containing an Xarray ``Dataset`` from the NetCDF file (".nc")
    specified by the given file path, or the given description and commit ID.
    """
    return _load_log(DataLog, path_or_metadata)


def load_dict_log(path_or_metadata: str | LogMetadata) -> DictLog:
    """
    Load a dictionary log from the JSON file (".json") specified by the given file
    path, or the given description and commit ID.
    """
    return _load_log(DictLog, path_or_metadata)
