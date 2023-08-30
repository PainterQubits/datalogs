"""Tests for datalogger._logger."""

from __future__ import annotations
from typing import Any
import os
from datetime import datetime
import xarray as xr
import xarray.testing
import pytest
from freezegun import freeze_time
from paramdb import ParamDB
from datalogger._get_filename import get_filename
from datalogger import Coord, DataVar, Logger


# pylint: disable-next=too-few-public-methods
class Obj:
    """Class for creating objects in the following tests."""

    def __repr__(self) -> str:
        return "<Obj>"


def test_root_logger_parent_fails() -> None:
    """A root Logger fails to be defined with a parent."""
    logger = Logger("dir")
    with pytest.raises(TypeError) as exc_info:
        Logger("dir", parent=logger)  # type: ignore
    assert str(exc_info.value) == "Logger with a root_directory cannot have a parent"


def test_root_logger_description_fails() -> None:
    """A root Logger fails to be defined with a description."""
    with pytest.raises(TypeError) as exc_info:
        Logger("dir", description="test")  # type: ignore
    assert (
        str(exc_info.value) == "Logger with a root_directory cannot have a description"
    )


def test_sub_logger_no_parent_fails() -> None:
    """A sub-Logger fails to be defined without a parent."""
    with pytest.raises(TypeError) as exc_info:
        Logger(description="test")  # type: ignore
    assert str(exc_info.value) == "Logger with no root_directory must have a parent"


def test_sub_logger_no_description_fails() -> None:
    """A sub-Logger fails to be defined without a description."""
    logger = Logger("dir")
    with pytest.raises(TypeError) as exc_info:
        Logger(parent=logger)  # type: ignore
    assert (
        str(exc_info.value) == "Logger with no root_directory must have a description"
    )


@pytest.mark.usefixtures("cd_tempdir")
def test_root_logger_creates_directory() -> None:
    """A root Logger creates its directory when it is defined."""
    assert not os.path.exists("dir")
    Logger("dir")
    assert os.path.exists("dir")


def test_sub_logger_creates_directory(logger: Logger, timestamp: datetime) -> None:
    """A sub-Logger creates its directory when a log is created."""
    parent_dir = logger.directory
    sub_logger = logger.sub_logger("sub_logger")
    sub_logger_dir = os.path.join(
        parent_dir,
        get_filename(parent_dir, "sub_logger", timestamp=timestamp.astimezone()),
    )
    assert not os.path.exists(sub_logger_dir)
    with freeze_time(timestamp):
        sub_logger.log_dict("dict", {})
    assert os.path.exists(sub_logger_dir)


def test_root_logger_directory(root_logger: Logger) -> None:
    """A root logger can return its directory."""
    assert root_logger.directory == "dir"


def test_sub_logger_directory(logger: Logger, timestamp: datetime) -> None:
    """
    A sub-Logger can return its directory and continues to use that same directory name
    to generate future logs.
    """
    parent_dir = logger.directory
    sub_logger = logger.sub_logger("sub_logger")
    sub_logger_dir = os.path.join(
        parent_dir,
        get_filename(parent_dir, "sub_logger", timestamp=timestamp.astimezone()),
    )
    with freeze_time(timestamp):
        assert sub_logger.directory == sub_logger_dir
    assert not os.path.exists(sub_logger_dir)
    sub_logger.log_dict("dict", {})
    assert os.path.exists(sub_logger_dir)


def test_file_path(logger: Logger) -> None:
    """A logger can return a file path within its directory."""
    assert logger.file_path("test.png") == os.path.join(logger.directory, "test.png")


def test_log_data(
    logger: Logger,
    coord: Coord,
    data_var: DataVar,
    xarray_data: xr.Dataset,
    timestamp: datetime,
) -> None:
    """A logger can create and save data logs."""
    with freeze_time(timestamp):
        data_log = logger.log_data("test_data", [coord], [data_var])
    assert os.path.exists(data_log.path)
    log_metadata = data_log.metadata
    assert log_metadata.directory == logger.directory
    assert log_metadata.timestamp == timestamp
    assert log_metadata.description == "test_data"
    assert log_metadata.commit_id is None
    assert log_metadata.param_db_path is None
    xarray.testing.assert_identical(data_log.data, xarray_data)


def test_log_dict_not_dict_fails(logger: Logger) -> None:
    """A logger fails to save a dict log when a non-dict object is passed."""
    with pytest.raises(TypeError) as exc_info:
        logger.log_dict("test_dict", 123)  # type: ignore
    assert str(exc_info.value) == "'int' data given for dict log 'test_dict'"


def test_log_dict(
    logger: Logger, dict_data: dict[str, Any], timestamp: datetime
) -> None:
    """A logger can create and save dict logs."""
    with freeze_time(timestamp):
        dict_log = logger.log_dict("test_dict", dict_data)
    assert os.path.exists(dict_log.path)
    log_metadata = dict_log.metadata
    assert log_metadata.directory == logger.directory
    assert log_metadata.timestamp == timestamp
    assert log_metadata.description == "test_dict"
    assert log_metadata.commit_id is None
    assert log_metadata.param_db_path is None
    assert dict_log.data == dict_data


def test_log_props_unsupported_fails(logger: Logger) -> None:
    """
    A logger fails to save an object property log when an unsupported object is passed
    (one without a ``__dict__`` property).
    """
    with pytest.raises(TypeError) as exc_info:
        logger.log_props("test_props", 123)
    assert str(exc_info.value) == "'int' object is not supported by log_props"


def test_log_props_basic(logger: Logger, timestamp: datetime) -> None:
    """A logger can create and save an object property log for a basic object."""
    obj = Obj()
    setattr(obj, "p1", 1)
    setattr(obj, "p2", 2)
    with freeze_time(timestamp):
        props_log = logger.log_props("test_props", obj)
    assert os.path.exists(props_log.path)
    log_metadata = props_log.metadata
    assert log_metadata.directory == logger.directory
    assert log_metadata.timestamp == timestamp
    assert log_metadata.description == "test_props"
    assert log_metadata.commit_id is None
    assert log_metadata.param_db_path is None
    assert props_log.data == {"p1": 1, "p2": 2}


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
        ({"nested": {"p1": [(1, 2), 3]}}, {"nested": {"p1": [[1, 2], 3]}}),
        (
            {"nonstring_keys": {(1, 2): 1, 12: 2, 1.2: 3, None: 4, False: 5}},
            {"nonstring_keys": {"(1, 2)": 1, "12": 2, "1.2": 3, "None": 4, "False": 5}},
        ),
        ({"obj": Obj()}, {"obj": "<Obj>"}),
    ],
)
def test_log_props(
    root_logger: Logger, props: dict[Any, Any], props_log_data: dict[str, Any]
) -> None:
    """
    A logger can create and save object property logs for a range of object property
    values.
    """
    obj = Obj()
    for k, v in props.items():
        setattr(obj, k, v)
    props_log = root_logger.log_props("test", obj)
    assert os.path.exists(props_log.path)
    assert props_log.data == props_log_data


@pytest.mark.usefixtures("cd_tempdir")
def test_log_empty_paramdb_latest_commit_fails() -> None:
    """A logger fails to create a log if an empty ParamDB is given."""
    param_db = ParamDB[Any]("param.db")
    root_logger = Logger("dir", param_db)
    error_msg = (
        "cannot tag log 'test' with most recent commit because ParamDB 'param.db' is"
        " empty"
    )
    with pytest.raises(IndexError) as exc_info:
        root_logger.log_data("test", [], [])
    assert str(exc_info.value) == error_msg
    with pytest.raises(IndexError) as exc_info:
        root_logger.log_dict("test", {})
    assert str(exc_info.value) == error_msg
    with pytest.raises(IndexError) as exc_info:
        root_logger.log_props("test", Obj())
    assert str(exc_info.value) == error_msg


@pytest.mark.usefixtures("cd_tempdir")
def test_log_paramdb_latest_commit(param_db: ParamDB[Any]) -> None:
    """A logger can tag logs with the current ParamDB and path."""
    logger = Logger("dir", param_db)
    for commit_id in 3, 4:
        log_metadatas = [
            logger.log_data("test", [], []).metadata,
            logger.log_dict("test", {}).metadata,
            logger.log_props("test", Obj).metadata,
        ]
        for log_metadata in log_metadatas:
            assert log_metadata.commit_id == commit_id
            assert log_metadata.param_db_path == "param.db"
        param_db.commit("Message", "test")


def test_log_no_paramdb_explicit_commit() -> None:
    """A logger with no ParamDB can tag logs with an explicit commit ID."""
    logger = Logger("dir")
    log_metadatas = [
        logger.log_data("test", [], [], commit_id=100).metadata,
        logger.log_dict("test", {}, commit_id=100).metadata,
        logger.log_props("test", Obj, commit_id=100).metadata,
    ]
    for log_metadata in log_metadatas:
        assert log_metadata.commit_id == 100
        assert log_metadata.param_db_path is None


def test_log_param_db_explicit_commit(param_db: ParamDB[Any]) -> None:
    """A logger with a ParamDB can tag logs with an explicit commit ID."""
    logger = Logger("dir", param_db)
    log_metadatas = [
        logger.log_data("test", [], [], commit_id=100).metadata,
        logger.log_dict("test", {}, commit_id=100).metadata,
        logger.log_props("test", Obj, commit_id=100).metadata,
    ]
    for log_metadata in log_metadatas:
        assert log_metadata.commit_id == 100
        assert log_metadata.param_db_path == "param.db"
