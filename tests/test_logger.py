"""Tests for datalogger._logger."""

# pylint: disable=too-few-public-methods
# pylint: disable=missing-class-docstring
# pylint: disable=attribute-defined-outside-init

from __future__ import annotations
from typing import Any, Union, Optional
from collections.abc import Callable
import os
import sys
from datetime import datetime
import numpy as np
import pandas as pd  # type: ignore
import xarray as xr
import xarray.testing
import pytest
from freezegun import freeze_time
from paramdb import ParamDB
from datalogger._get_filename import get_filename
from datalogger import Coord, DataVar, LoggedProp, Logger

PYTHON_VERSION = f"{sys.version_info.major}.{sys.version_info.minor}"


class Obj:
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
    """
    A root Logger creates its directory when it is defined, and another root logger will
    reuse the same directory.
    """
    assert not os.path.exists("dir")
    root_logger_1 = Logger("dir")
    assert os.path.exists("dir")
    root_logger_2 = Logger("dir")
    assert root_logger_1.directory == root_logger_2.directory


def test_sub_logger_no_timestamp_creates_directory(logger: Logger) -> None:
    """
    A sub-Logger with no timestamp creates its directory when it is defined, and another
    sub-Logger with no timestamp will reuse the same directory.
    """
    sub_logger_dir = os.path.join(logger.directory, "sub_logger")
    sub_logger_1 = logger.sub_logger("sub_logger", timestamp=False)
    assert os.path.exists(sub_logger_dir)
    sub_logger_2 = logger.sub_logger("sub_logger", timestamp=False)
    assert sub_logger_1.directory == sub_logger_2.directory


def test_sub_logger_timestamp_creates_directory(
    logger: Logger, timestamp: datetime
) -> None:
    """
    A sub-Logger with a timestamp creates its directory when the directory is accessed,
    and another sub-Logger with a timestamp will always create a new directory.
    """
    parent_dir = logger.directory
    sub_logger_dir = os.path.join(
        parent_dir,
        get_filename(parent_dir, "sub_logger", timestamp=timestamp.astimezone()),
    )
    sub_logger_1 = logger.sub_logger("sub_logger")
    assert not os.path.exists(sub_logger_dir)
    with freeze_time(timestamp):
        sub_logger_1.directory  # pylint: disable=pointless-statement
    assert os.path.exists(sub_logger_dir)
    sub_logger_2 = logger.sub_logger("sub_logger")
    with freeze_time(timestamp):
        sub_logger_2.directory  # pylint: disable=pointless-statement
    assert sub_logger_1.directory != sub_logger_2.directory


def test_root_logger_directory(root_logger: Logger) -> None:
    """A root logger can return its directory."""
    assert root_logger.directory == "dir"


def test_sub_logger_no_timestamp_directory(logger: Logger) -> None:
    """A sub-Logger with no timestamp can return its directory."""
    sub_logger = logger.sub_logger("sub_logger", timestamp=False)
    assert sub_logger.directory == os.path.join(logger.directory, "sub_logger")


def test_sub_logger_timestamp_directory(logger: Logger, timestamp: datetime) -> None:
    """
    A sub-Logger with a timestamp can return its directory and continues to use that
    same directory name.
    """
    parent_dir = logger.directory
    sub_logger_dir = os.path.join(
        parent_dir,
        get_filename(parent_dir, "sub_logger", timestamp=timestamp.astimezone()),
    )
    sub_logger = logger.sub_logger("sub_logger")
    with freeze_time(timestamp):
        assert sub_logger.directory == sub_logger_dir
    assert sub_logger.directory == sub_logger_dir  # Continues to use the same directory


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


@pytest.mark.parametrize(
    "obj,expected_converted",
    [
        ("test", "test"),
        (123, 123),
        (1.23, 1.23),
        (True, True),
        ([1, 2, 3], [1, 2, 3]),
        ((1, 2, 3), [1, 2, 3]),
        ({1, 2, 3}, [1, 2, 3]),
        ({"p1": 123, "p2": 456}, {"p1": 123, "p2": 456}),
        ({"p1": [(1, Obj()), 2]}, {"p1": [[1, "<Obj>"], 2]}),
        (
            {(1, 2): 1, 12: 2, 1.2: 3, None: 4, False: 5},
            {"(1, 2)": 1, "12": 2, "1.2": 3, "None": 4, "False": 5},
        ),
        (Obj(), "<Obj>"),
        (np.int32(123), 123),
        (np.float64(1.23), 1.23),
        (np.array(123), 123),
        (np.array(1.23), 1.23),
        (
            pd.DataFrame({"col1": [1, 2], "col2": [3, 4]}),
            {"col1": {"0": 1, "1": 2}, "col2": {"0": 3, "1": 4}},
        ),
    ],
)
def test_convert_to_json(obj: Any, expected_converted: Any) -> None:
    """A logger can convert a given object to a JSON-serializable object."""
    converted = Logger.convert_to_json(obj)
    assert converted == expected_converted
    assert type(converted) is type(expected_converted)


@pytest.mark.parametrize(
    "obj,convert,expected_converted",
    [
        ("test", lambda obj: 123, 123),
        (123, lambda obj: obj * 2, 246),
        ((1, 2, 3), lambda obj: obj + 1 if isinstance(obj, int) else obj, [2, 3, 4]),
        (
            {"p1": 1, "p2": Obj()},
            lambda obj: "Obj()" if isinstance(obj, Obj) else obj,
            {"p1": 1, "p2": "Obj()"},
        ),
    ],
)
def test_convert_to_json_convert(
    obj: Any, convert: Callable[[Any], Any] | None, expected_converted: Any
) -> None:
    """
    A logger can use a convert function to convert a given object to a JSON-serializable
    object.
    """
    converted = Logger.convert_to_json(obj, convert)
    assert converted == expected_converted
    assert type(converted) is type(expected_converted)


def test_log_dict_not_dict_fails(root_logger: Logger) -> None:
    """A logger fails to save a dict log when a non-dict object is passed."""
    with pytest.raises(TypeError) as exc_info:
        root_logger.log_dict("test_dict", 123)  # type: ignore
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


@pytest.mark.parametrize(
    "dict_data,expected_converted",
    [
        ({"p1": 123, "p2": 456}, {"p1": 123, "p2": 456}),
        ({"p1": [(1, Obj()), 2]}, {"p1": [[1, "<Obj>"], 2]}),
        (
            {(1, 2): 1, 12: 2, 1.2: 3, None: 4, False: 5},
            {"(1, 2)": 1, "12": 2, "1.2": 3, "None": 4, "False": 5},
        ),
    ],
)
def test_log_dict_convert_to_json(
    root_logger: Logger, dict_data: dict[Any, Any], expected_converted: Any
) -> None:
    """A logger converts data to JSON before storing in a dict_log."""
    dict_log = root_logger.log_dict("test_dict", dict_data)
    assert dict_log.data == expected_converted


@pytest.mark.parametrize(
    "dict_data,convert,expected_converted",
    [
        (
            {"p1": 123, "p2": 456},
            lambda obj: obj + 1 if isinstance(obj, int) else obj,
            {"p1": 124, "p2": 457},
        ),
        (
            {"p1": [(1, Obj()), 2]},
            lambda obj: "Obj()" if isinstance(obj, Obj) else obj,
            {"p1": [[1, "Obj()"], 2]},
        ),
    ],
)
def test_log_dict_convert_to_json_convert(
    root_logger: Logger,
    dict_data: dict[Any, Any],
    convert: Callable[[Any], Any] | None,
    expected_converted: Any,
) -> None:
    """
    A logger can use a convert function to convert data to JSON before storing in a
    dict_log.
    """
    dict_log = root_logger.log_dict("test_dict", dict_data, convert=convert)
    assert dict_log.data == expected_converted


if PYTHON_VERSION == "3.9":

    def test_python39_log_props_invalid_type_hints_fails(root_logger: Logger) -> None:
        """
        A logger fails to log the properties of an object whose class type hints are
        invalid for Python 3.9.
        """

        class LogPropsObj:
            p1: LoggedProp[int | float]

        with pytest.raises(RuntimeError) as exc_info:
            root_logger.log_props("test_props", LogPropsObj())
        assert (
            str(exc_info.value)
            == "cannot log properties of 'LogPropsObj' object because its class type"
            f" hints are invalid in Python {PYTHON_VERSION}"
        )


def test_log_props(logger: Logger, timestamp: datetime) -> None:
    """A logger can create and save an object property log for a basic object."""

    class LogPropsObj:
        p1: LoggedProp[int]
        p2: bool
        p3: LoggedProp[str]

    obj = LogPropsObj()
    obj.p1 = 123
    obj.p2 = False
    obj.p3 = "test"
    with freeze_time(timestamp):
        props_log = logger.log_props("test_props", obj)
    assert os.path.exists(props_log.path)
    log_metadata = props_log.metadata
    assert log_metadata.directory == logger.directory
    assert log_metadata.timestamp == timestamp
    assert log_metadata.description == "test_props"
    assert log_metadata.commit_id is None
    assert log_metadata.param_db_path is None
    assert props_log.data == {"p1": 123, "p3": "test"}


@pytest.mark.parametrize(
    "annotations,props,expected_logged",
    [
        (
            {"p1": LoggedProp[int], "p2": bool, "p3": LoggedProp[str]},
            {"p1": 123, "p2": False, "p3": "test"},
            {"p1": 123, "p3": "test"},
        ),
        (
            {"p1": "LoggedProp[int]", "p2": "bool", "p3": "LoggedProp[str]"},
            {"p1": 123, "p2": False, "p3": "test"},
            {"p1": 123, "p3": "test"},
        ),
        (
            {
                "p1": LoggedProp[Union[int, str]],
                "p2": Optional[LoggedProp],
                "p3": LoggedProp[Optional[str]],
            },
            {"p1": 123, "p2": False, "p3": None},
            {"p1": 123, "p3": None},
        ),
    ],
)
def test_log_props_type_hints(
    root_logger: Logger,
    annotations: dict[str, Any],
    props: dict[str, Any],
    expected_logged: dict[str, Any],
) -> None:
    """
    A logger only logs the properties of objects that are marked with a LoggedProp
    type hint annotation.
    """

    class LogPropsObj:
        __annotations__ = annotations

    obj = LogPropsObj()
    for k, v in props.items():
        setattr(obj, k, v)

    props_log = root_logger.log_props("test_props", obj)
    assert props_log.data == expected_logged


def test_log_props_type_hint_inheritance(root_logger: Logger) -> None:
    """
    A logger considers type hints from parent classes when determining which properties
    of an object to log, and child classes can override parent type hints.
    """

    class LogPropsParent:
        p1: LoggedProp[int]
        p2: bool
        p3: LoggedProp[str]

    class LogPropsObj(LogPropsParent):
        p1: int  # type: ignore

    obj = LogPropsObj()
    obj.p1 = 123
    obj.p2 = False
    obj.p3 = "test"
    props_log = root_logger.log_props("test_props", obj)
    assert props_log.data == {"p3": "test"}


@pytest.mark.parametrize(
    "props,expected_converted",
    [
        ({"p1": 123, "p2": 456}, {"p1": 123, "p2": 456}),
        ({"p1": [(1, Obj()), 2]}, {"p1": [[1, "<Obj>"], 2]}),
    ],
)
def test_log_props_convert_to_json(
    root_logger: Logger, props: dict[str, Any], expected_converted: Any
) -> None:
    """A logger converts properties to JSON before logging them."""

    class LogPropsObj:
        __annotations__: dict[str, Any]

    obj = LogPropsObj()
    for k, v in props.items():
        LogPropsObj.__annotations__[k] = LoggedProp
        setattr(obj, k, v)

    props_log = root_logger.log_props("test_props", obj)
    assert props_log.data == expected_converted


@pytest.mark.parametrize(
    "props,convert,expected_converted",
    [
        (
            {"p1": 123, "p2": 456},
            lambda obj: obj + 1 if isinstance(obj, int) else obj,
            {"p1": 124, "p2": 457},
        ),
        (
            {"p1": [(1, Obj()), 2]},
            lambda obj: "Obj()" if isinstance(obj, Obj) else obj,
            {"p1": [[1, "Obj()"], 2]},
        ),
    ],
)
def test_log_props_convert_to_json_convert(
    root_logger: Logger,
    props: dict[str, Any],
    convert: Callable[[Any], Any] | None,
    expected_converted: Any,
) -> None:
    """
    A logger can use a convert function to convert properties to JSON before logging
    them.
    """

    class LogPropsObj:
        __annotations__: dict[str, Any]

    obj = LogPropsObj()
    for k, v in props.items():
        LogPropsObj.__annotations__[k] = LoggedProp
        setattr(obj, k, v)

    props_log = root_logger.log_props("test_props", obj, convert=convert)
    assert props_log.data == expected_converted


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
