"""Tests for datalogger._logs."""

import os
from copy import deepcopy
from datetime import datetime
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


def test_log_metadata(log_metadata: LogMetadata, log: DataLog | DictLog) -> None:
    """Metadata can be retrieved from a log."""
    assert log.metadata == log_metadata


def test_path_new_log(log_metadata: LogMetadata, log: DataLog | DictLog) -> None:
    """
    A unique path for a newly created log object is generated when the ``path`` property
    is accessed.
    """
    log.path
