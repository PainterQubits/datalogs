import os
from pathlib import Path
from datetime import datetime, timezone
import pytest
from datalogger import Coord, DataVar, LogMetadata, DataLog, DictLog


@pytest.fixture(name="cd_tempdir")
def cd_tempdir(tmp_path: Path) -> None:
    """Change to a temporary directory."""
    os.chdir(tmp_path)


@pytest.fixture(name="timestamp")
def fixture_timestamp() -> datetime:
    """``datetime`` object to use as a timestamp."""
    return datetime(2023, 7, 28, 13, 12, 34, 567890, timezone.utc)


@pytest.fixture(name="timestamp_str")
def fixture_timestamp_str() -> str:
    """String representation of the timestamp."""
    return "2023-07-28 13:12:34.567890+00:00"


@pytest.fixture(name="timestamp_str_short")
def fixture_timestamp_str_short() -> str:
    """Shortened string representation of the timestamp."""
    return "23-07-28-1312"


@pytest.fixture(name="coord")
def fixture_coord() -> Coord:
    """Coord object."""
    return Coord("time", data=[1, 2, 3], long_name="Time", units="s")


@pytest.fixture(name="data_var")
def fixture_data_var() -> DataVar:
    """DataVar object."""
    return DataVar(
        "signal", dims="time", data=[10, 20, 30], long_name="Signal", units="V"
    )


@pytest.fixture(name="log_metadata")
def fixture_log_metadata(timestamp: datetime) -> LogMetadata:
    """LogMetadata object."""
    return LogMetadata(
        directory="dir",
        timestamp=timestamp,
        description="test",
        commit_id=123,
        param_db_path="param.db",
    )


@pytest.fixture(name="data_log")
def fixture_data_log(log_metadata: LogMetadata) -> DataLog:
    """DataLog object."""
    return DataLog.from_variables(
        log_metadata,
        [Coord("time", data=[1, 2, 3], long_name="Time", units="s")],
        [
            DataVar(
                "signal", dims="time", data=[10, 20, 30], long_name="Signal", units="V"
            )
        ],
    )


@pytest.fixture(name="dict_log")
def fixture_dict_log(log_metadata: LogMetadata) -> DictLog:
    """DictLog object."""
    return DictLog(log_metadata, {"param1": 123, "param2": 456})


@pytest.fixture(name="log", params=["data_log", "dict_log"])
def fixture_log(request: pytest.FixtureRequest) -> DataLog | DictLog:
    """DataLog or DictLog object."""
    log: DataLog | DictLog = request.getfixturevalue(request.param)
    return log
