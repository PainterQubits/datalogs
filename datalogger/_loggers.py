"""Data logging classes."""

from __future__ import annotations
from typing import TypeVar, Any
from collections.abc import Callable, Sequence
from abc import ABC, abstractmethod
import os
from datetime import datetime, timezone
from paramdb import ParamDB
from datalogger._variables import Coord, DataVar
from datalogger._logs import LogMetadata, DataLog, DictLog
from datalogger._get_filename import get_filename


# Log type
_LT = TypeVar("_LT", DataLog, DictLog)


# pylint: disable-next=too-few-public-methods
class _Logger(ABC):
    """Abstract base class for loggers."""

    @property
    @abstractmethod
    def directory(self) -> str:
        """Directory where this logger saves subdirectories or files."""

    def _create_directory(self) -> None:
        """Create the directory for this logger if it does not exist."""
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)


# pylint: disable-next=too-few-public-methods
class _SubLogger(_Logger):
    def __init__(self, description: str):
        self._description = description
        self._timestamp: datetime | None = None
        self._name: str | None = None

    @property
    @abstractmethod
    def _parent_directory(self) -> str:
        """Directory of this sublogger's parent."""

    @property
    def name(self) -> str:
        """Name of this graph, including the timestamp and description."""
        if self._timestamp is None:
            raise TypeError(
                f"timestamp for '{self._description}' has not been generated"
            )
        if self._name is None:
            self._name = get_filename(
                self._parent_directory, self._description, timestamp=self._timestamp
            )
        return self._name

    @property
    def directory(self) -> str:
        return os.path.join(self._parent_directory, self.name)

    def _set_timestamp(self, timestamp: datetime) -> None:
        """Set the timestamp of this logger if it has not been set."""
        if self._timestamp is None:
            self._timestamp = timestamp


class RootLogger(_Logger):
    """
    Logger that generates :py:class:`GraphLogger` objects that use the given ParamDB and
    base directory.
    """

    def __init__(self, param_db: ParamDB[Any], log_directory: str) -> None:
        self._param_db = param_db
        self._directory = log_directory
        self._create_directory()

    @property
    def directory(self) -> str:
        return self._directory

    def graph_logger(self, description: str) -> GraphLogger:
        """Create a new :py:class:`GraphLogger` with the given description."""
        return GraphLogger(self, description)


class GraphLogger(_SubLogger):
    """
    Logger associated with a particular graph that generates :py:class:`NodeLogger`
    objects for nodes within that graph.
    """

    def __init__(self, root_logger: RootLogger, description: str) -> None:
        self._root_logger = root_logger
        super().__init__(description)

    @property
    def _parent_directory(self) -> str:
        return self._root_logger.directory

    def node_logger(self, description: str) -> NodeLogger:
        """Create a new :py:class:`NodeLogger` with the given description."""
        return NodeLogger(self, description)


class NodeLogger(_SubLogger):
    """
    Logger associated with a particular node that generates that generates log files
    within a directory for that node.
    """

    def __init__(self, graph_logger: GraphLogger, description: str) -> None:
        self._root_logger = graph_logger._root_logger
        self._graph_logger = graph_logger
        super().__init__(description)

    @property
    def _parent_directory(self) -> str:
        return self._graph_logger.directory

    def filepath(self, filename: str) -> str:
        """
        Generate a path to a file with the given name within the directory of this
        :py:class:`NodeLogger`.
        """
        return os.path.join(self.directory, filename)

    def _log(
        self,
        make_log: Callable[[LogMetadata], _LT],
        description: str,
        commit_id: int | None = None,
    ) -> _LT:
        """
        Create a log object using the given log creation function, description, commit
        ID. If no commit ID is given, the latest commit ID will be used.
        """
        param_db = self._root_logger._param_db  # pylint: disable=protected-access
        if commit_id is None:
            latest_commit = param_db.latest_commit
            if latest_commit is None:
                raise IndexError(
                    "cannot tag log with most recent commit because ParamDB at"
                    f" '{param_db.path}' is empty"
                )
            commit_id = latest_commit.id
        timestamp = datetime.now(timezone.utc).astimezone()
        self._graph_logger._set_timestamp(timestamp)  # pylint: disable=protected-access
        self._graph_logger._create_directory()  # pylint: disable=protected-access
        self._set_timestamp(timestamp)
        self._create_directory()
        log = make_log(
            LogMetadata(
                log_directory=self._root_logger.directory,
                graph_name=self._graph_logger.name,
                node_name=self.name,
                timestamp=timestamp,
                description=description,
                commit_id=commit_id,
                paramdb_path=param_db.path,
            )
        )
        log.save()
        return log

    def log_data(
        self,
        description: str,
        coords: Coord | Sequence[Coord],
        data_vars: DataVar | Sequence[DataVar],
        commit_id: int | None = None,
    ) -> DataLog:
        """
        Construct an Xarray from the given data and corresponding metadata, save it in a
        NetCDF file, and return a :py:class:`DataLog` with this data and metadata.

        The log will be tagged with the given commit ID, or the latest commit ID if none
        is given.
        """

        def make_log(log_metadata: LogMetadata) -> DataLog:
            return DataLog.from_variables(log_metadata, coords, data_vars)

        return self._log(make_log, description, commit_id)

    def log_dict(
        self, description: str, dict_data: dict[str, Any], commit_id: int | None = None
    ) -> DictLog:
        """
        Save the given dictionary data and corresponding metadata in a JSON file, and
        return a :py:class:`DictLog` with this data and metadata.

        The log will be tagged with the given commit ID, or the latest commit ID if none
        is given.
        """

        def make_log(log_metadata: LogMetadata) -> DictLog:
            return DictLog(log_metadata, dict_data)

        return self._log(make_log, description, commit_id)

    @classmethod
    def _should_save_prop(cls, prop: Any) -> bool:
        """
        Whether the given object property should be saved. For now, this is checking
        whether the given property can be saved as JSON.
        """
        if isinstance(prop, (str, int, float, bool)) or prop is None:
            return True
        if isinstance(prop, (list, tuple)):
            return all(cls._should_save_prop(p) for p in prop)
        if isinstance(prop, dict):
            return all(cls._should_save_prop(p) for p in prop.values())
        return False

    def log_props(
        self, description: str, obj: Any, commit_id: int | None = None
    ) -> DictLog:
        """
        Save a dictionary of the given object's properties and corresponding metadata in
        a JSON file, and return a :py:class:`DictLog` with this data and metadata. Only
        properties that can be parsed into JSON will be saved.

        The log will be tagged with the given commit ID, or the latest commit ID if none
        is given.
        """
        props = {k: v for k, v in vars(obj).items() if self._should_save_prop(v)}
        return self.log_dict(description, props, commit_id)
