"""Tests for datalogs._load_log."""

from __future__ import annotations
from typing import Any
import xarray.testing
import pytest
from datalogs import Logger, Coord, DataVar, DataLog, DictLog, load_log


@pytest.mark.usefixtures("cd_tempdir")
def test_load_unsupported_ext_fails() -> None:
    """Fails to load a log if the extension is unsupported."""
    with open("data.txt", "w", encoding="utf-8"):
        pass
    with pytest.raises(ValueError) as exc_info:
        load_log("data.txt")
    assert str(exc_info.value) == "'.txt' file extension is not supported"


def test_load_data_log(logger: Logger, coord: Coord, data_var: DataVar) -> None:
    """Can load a data log."""
    data_log = logger.log_data("test", [coord], [data_var])
    loaded_data_log = load_log(data_log.path)
    assert isinstance(loaded_data_log, DataLog)
    assert loaded_data_log.metadata == data_log.metadata
    xarray.testing.assert_identical(loaded_data_log.data, data_log.data)
    assert loaded_data_log.path == data_log.path


def test_load_dict_log(logger: Logger, dict_data: dict[str, Any]) -> None:
    """Can load a dict log using ``load_log()``."""
    dict_log = logger.log_dict("test", dict_data)
    loaded_dict_log = load_log(dict_log.path)
    assert isinstance(loaded_dict_log, DictLog)
    assert loaded_dict_log.metadata == dict_log.metadata
    assert loaded_dict_log.data == dict_log.data
    assert loaded_dict_log.path == dict_log.path
