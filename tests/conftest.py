from typing import Any
import os
from pathlib import Path
from datetime import datetime, timezone
import xarray as xr
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


@pytest.fixture(name="log_type", params=["DataLog", "DictLog"])
def fixture_log_type(request: pytest.FixtureRequest) -> type[DataLog | DictLog]:
    """Type of the log."""
    return DataLog if request.param == "DataLog" else DictLog


@pytest.fixture(name="xarray_data")
def fixture_xarray_data() -> xr.Dataset:
    """Xarray data object."""
    return xr.Dataset(
        data_vars={
            "signal": ("time", [10, 20, 30], {"long_name": "Signal", "units": "V"})
        },
        coords={"time": ("time", [1, 2, 3], {"long_name": "Time", "units": "s"})},
    )


@pytest.fixture(name="dict_data")
def fixture_dict_data() -> dict[str, Any]:
    """Dictionary data object."""
    return {"param1": 123, "param2": 456}


@pytest.fixture(name="data")
def fixture_data(
    log_type: type[DataLog | DictLog],
    xarray_data: xr.Dataset,
    dict_data: dict[str, Any],
) -> xr.Dataset | dict[str, Any]:
    """Data object for the log."""
    return xarray_data if log_type is DataLog else dict_data


@pytest.fixture(name="log")
def fixture_log(
    log_type: type[DataLog | DictLog],
    log_metadata: LogMetadata,
    data: xr.Dataset | dict[str, Any],
) -> DataLog:
    """DataLog object."""
    return log_type(log_metadata, data)  # type: ignore


@pytest.fixture(name="log_path_prefix")
def fixture_log_path_prefix(log_metadata: LogMetadata) -> str:
    """Prefix of the log path."""
    return os.path.join(log_metadata.directory, log_metadata.description)


@pytest.fixture(name="log_ext")
def fixture_log_ext(log_type: type[DataLog | DictLog]) -> str:
    """Extension of the log object."""
    return log_type._ext  # pylint: disable=protected-access
