"""Tests for datalogger._logger."""

from typing import Any
import os
from dataclasses import dataclass
import xarray as xr
import xarray.testing
import pytest
from datalogger import Coord, DataVar, Logger


@dataclass
class Obj:
    """Test object for testing ``Logger.log_props()``."""

    str_prop: str | None = None
    int_prop: int | None = None
    float_prop: float | None = None
    bool_prop: bool | None = None
    list_prop: list[Any] | None = None
    tuple_prop: tuple[Any, ...] | None = None
    dict_prop: dict[str, Any] | None = None


@pytest.mark.usefixtures("cd_tempdir")
def test_root_logger_creates_directory() -> None:
    """A root logger creates its directory when it is defined."""
    assert not os.path.exists("dir")
    Logger(root_directory="dir")
    assert os.path.exists("dir")


@pytest.mark.usefixtures("cd_tempdir")
def test_root_logger_data_log(
    coord: Coord, data_var: DataVar, xarray_data: xr.Dataset
) -> None:
    """A root logger can create and save data logs."""
    root_logger = Logger(root_directory="dir")
    data_log = root_logger.log_data("test", [coord], [data_var])
    assert os.path.exists(data_log.path)
    xarray.testing.assert_identical(data_log.data, xarray_data)


@pytest.mark.usefixtures("cd_tempdir")
def test_root_logger_dict_log(dict_data: dict[str, Any]) -> None:
    """A root logger can create and save dict logs."""
    root_logger = Logger(root_directory="dir")
    dict_log = root_logger.log_dict("test", dict_data)
    assert os.path.exists(dict_log.path)
    assert dict_log.data == dict_data


# TODO: Make different logger types (root, sub, sub-sub), and remake these tests so all
# of them are tested for being able to create each log type
