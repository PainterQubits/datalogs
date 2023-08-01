"""Tests for datalogger._logs."""

from datetime import datetime, timezone
import pytest
from datalogger._logs import LogMetadata, DataLog, DictLog

TIMESTAMP_OBJ = datetime(2023, 7, 28, 13, 12, 34, 567890, timezone.utc)
TIMESTAMP_STR = "2023-07-28 13:12:34.567890+00:00"


@pytest.fixture(name="log_metadata")
def fixture_log_metadata() -> LogMetadata:
    """LogMetadata object."""
    return LogMetadata(
        directory="dir",
        timestamp=TIMESTAMP_OBJ,
        description="test",
        commit_id=123,
        param_db_path="param.db",
    )


def test_log_metadata_properties(log_metadata: LogMetadata) -> None:
    """Can access the properties of a LogMetadata object."""
    assert log_metadata.directory == "dir"
    assert log_metadata.timestamp == TIMESTAMP_OBJ
    assert log_metadata.description == "test"
    assert log_metadata.commit_id == 123
    assert log_metadata.param_db_path == "param.db"


def test_log_metadata_repr(log_metadata: LogMetadata) -> None:
    """Converts a LogMetadata to a ``repr`` string."""
    assert (
        repr(log_metadata)
        == f"""\
directory      dir
timestamp      {TIMESTAMP_STR}
description    test
commit_id      123
param_db_path  param.db"""
    )
