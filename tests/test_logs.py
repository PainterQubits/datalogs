"""Tests for datalogger._logs."""

from typing import Any
import os
from copy import deepcopy
from datetime import datetime
import xarray as xr
import pytest
from datalogger import Coord, DataVar
from datalogger._logs import LogMetadata, DataLog, DictLog


def test_log_metadata_properties(
    log_metadata: LogMetadata, timestamp: datetime
) -> None:
    """Can access the properties of a LogMetadata object."""
    assert log_metadata.directory == "dir"
    assert log_metadata.timestamp == timestamp
    assert log_metadata.description == "test"
    assert log_metadata.commit_id == 123
    assert log_metadata.param_db_path == "param.db"


def test_log_metadata_repr(log_metadata: LogMetadata, timestamp_str: str) -> None:
    """Converts a LogMetadata to a ``repr`` string."""
    assert (
        repr(log_metadata)
        == f"""\
directory      dir
timestamp      {timestamp_str}
description    test
commit_id      123
param_db_path  param.db"""
    )


def test_log_metadata_equality(log_metadata: LogMetadata) -> None:
    """LogMetadata objects can be compared using equality."""
    log_metadata_2 = deepcopy(log_metadata)
    assert log_metadata == log_metadata_2
    log_metadata_2.directory = "dir2"
    assert log_metadata != log_metadata_2


def test_data_log_from_variables(
    log_metadata: LogMetadata, xarray_data: xr.Dataset
) -> None:
    """A DataLog can be constructed from variable objects."""
    data_log = DataLog.from_variables(
        log_metadata,
        [
            Coord(
                str(name),
                data=list(coord.data),
                long_name=coord.attrs["long_name"],
                units=coord.attrs["units"],
            )
            for name, coord in xarray_data.coords.items()
        ],
        [
            DataVar(
                str(name),
                dims=[str(dim) for dim in data_var.dims],
                data=list(data_var.data),
                long_name=data_var.attrs["long_name"],
                units=data_var.attrs["units"],
            )
            for name, data_var in xarray_data.data_vars.items()
        ],
    )
    assert data_log.metadata == log_metadata
    assert data_log.data == xarray_data


def test_log_metadata(log: DataLog | DictLog, log_metadata: LogMetadata) -> None:
    """Metadata can be retrieved from a log."""
    assert log.metadata == log_metadata


def test_log_data(log: DataLog | DictLog, data: xr.Dataset | dict[str, Any]) -> None:
    """Data can be retrieved from a log."""
    assert log.data == data


@pytest.mark.usefixtures("cd_tempdir")
def test_log_path(
    log: DataLog | DictLog,
    log_path_prefix: str,
    log_ext: str,
) -> None:
    """Logs generate the correct path."""
    assert log.path == f"{log_path_prefix}{log_ext}"


@pytest.mark.usefixtures("cd_tempdir")
def test_log_path_unique(
    log: DataLog | DictLog, log_path_prefix: str, log_ext: str
) -> None:
    """
    Logs generate unique file paths if the default path already exists, and remember
    their path once it is generated.
    """
    os.mkdir(log.metadata.directory)
    deepcopy(log).save()
    for i in range(5):
        new_log = deepcopy(log)
        new_log_path = f"{log_path_prefix}_{i + 1}{log_ext}"
        assert new_log.path == new_log_path
        new_log.save()
        assert new_log.path == new_log_path  # Log remembers path once file exists


@pytest.mark.usefixtures("cd_tempdir")
def test_log_save(log: DataLog | DictLog) -> None:
    """Logs can be saved to their path."""
    os.mkdir(log.metadata.directory)
    assert not os.path.exists(log.path)
    log.save()
    assert os.path.exists(log.path)


@pytest.mark.usefixtures("cd_tempdir")
def test_log_load(log_type: type[DataLog | DictLog], log: DataLog | DictLog) -> None:
    """
    Logs can be loaded from a file and retain the correct metadata, data, and path.
    """
    os.mkdir(log.metadata.directory)
    log.save()
    loaded_log = log_type.load(log.path)
    assert loaded_log.metadata == log.metadata
    assert loaded_log.data == log.data
    assert loaded_log.path == log.path