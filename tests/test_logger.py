"""Tests for datalogger._logger."""

from typing import Any
import os
import xarray as xr
import xarray.testing
import pytest
from datalogger import Coord, DataVar, Logger


# pylint: disable-next=too-few-public-methods
class Obj:
    """Class for creating objects in the following tests."""


@pytest.mark.usefixtures("cd_tempdir")
def test_root_logger_creates_directory() -> None:
    """A root logger creates its directory when it is defined."""
    assert not os.path.exists("dir")
    Logger(root_directory="dir")
    assert os.path.exists("dir")


def test_log_data(
    logger: Logger, coord: Coord, data_var: DataVar, xarray_data: xr.Dataset
) -> None:
    """A logger can create and save data logs."""
    data_log = logger.log_data("test", [coord], [data_var])
    assert os.path.exists(data_log.path)
    xarray.testing.assert_identical(data_log.data, xarray_data)


def test_log_dict(logger: Logger, dict_data: dict[str, Any]) -> None:
    """A logger can create and save dict logs."""
    dict_log = logger.log_dict("test", dict_data)
    assert os.path.exists(dict_log.path)
    assert dict_log.data == dict_data


@pytest.mark.parametrize(
    "props,props_log_data",
    [
        ({"p1": 123, "p2": 456}, {"p1": 123, "p2": 456}),
        ({"str": "test"}, {"str": "test"}),
        ({"int": 123}, {"int": 123}),
        ({"float": 1.23}, {"float": 1.23}),
        ({"bool": True}, {"bool": True}),
        ({"list": [1, 2, 3]}, {"list": [1, 2, 3]}),
        ({"tuple": (1, 2, 3)}, {"tuple": [1, 2, 3]}),
        ({"dict": {"p1": 1, "p2": 2}}, {"dict": {"p1": 1, "p2": 2}}),
    ],
)
def test_log_props(
    root_logger: Logger, props: dict[Any, Any], props_log_data: dict[str, Any]
) -> None:
    """A logger can create and save object property logs."""

    obj = Obj()
    for k, v in props.items():
        setattr(obj, k, v)
    props_log = root_logger.log_props("test", obj)
    assert os.path.exists(props_log.path)
    assert props_log.data == props_log_data
