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


# Log type
_LT = TypeVar("_LT", DataLog, DictLog)


# pylint: disable-next=too-few-public-methods
class _Logger(ABC):
    """Abstract base class for loggers."""

    @property
    @abstractmethod
    def directory(self) -> str:
        """Directory where this logger saves subdirectories or files."""


class RootLogger(_Logger):
    """
    Logger that generates :py:class:`GraphLogger` objects that use the given ParamDB and
    base directory.
    """

    def __init__(self, param_db: ParamDB[Any], log_directory: str) -> None:
        self._param_db = param_db
        self._log_directory = log_directory

    @property
    def directory(self) -> str:
        return self._log_directory

    def graph_logger(
        self, description: str, commit_id: int | None = None
    ) -> GraphLogger:
        """
        Create a :py:class:`GraphLogger` for the graph specified by the given
        description and commit ID.

        If no commit ID is given, the commit ID of the first log created within this
        graph will be used.
        """
        return GraphLogger(self, description, commit_id)


class GraphLogger(_Logger):
    """
    Logger associated with a particular graph that generates :py:class:`NodeLogger`
    objects for nodes within that graph.

    A description and commit ID are used to identify the graph. If no commit ID is
    given, the commit ID of the first log created within this graph will be used.
    """

    def __init__(
        self, root_logger: RootLogger, description: str, commit_id: int | None = None
    ) -> None:
        self._root_logger = root_logger
        self._description = description
        self._commit_id = commit_id

    @property
    def name(self) -> str:
        """Name of this graph, including the commit ID and description."""
        if self._commit_id is None:
            raise TypeError(
                f"commit ID for graph '{self._description}' has not been set"
            )
        return f"graph_{self._commit_id}_{self._description}"

    @property
    def directory(self) -> str:
        return os.path.join(self._root_logger.directory, self.name)

    def node_logger(self, description: str, commit_id: int | None = None) -> NodeLogger:
        """
        Generate a :py:class:`NodeLogger` for the node specified by the given
        description and commit ID.

        If no commit ID is given, the commit ID of the first log created within this
        graph will be used.
        """
        return NodeLogger(self, description, commit_id)


class NodeLogger(_Logger):
    """
    Logger associated with a particular node that generates that generates log files
    within a directory for that node.

    A description and commit ID are used to identify the node. If no commit ID is given,
    the commit ID of the first log created within this graph will be used.
    """

    def __init__(
        self, graph_logger: GraphLogger, description: str, commit_id: int | None = None
    ) -> None:
        self._root_logger = graph_logger._root_logger
        self._graph_logger = graph_logger
        self._description = description
        self._commit_id = commit_id

    @property
    def name(self) -> str:
        """Name of this node, including the commit ID and description."""
        if self._commit_id is None:
            raise TypeError(
                f"commit ID for node '{self._description}' has not been set"
            )
        return f"node_{self._commit_id}_{self._description}"

    @property
    def directory(self) -> str:
        return os.path.join(self._graph_logger.directory, self.name)

    def _log(
        self,
        make_log: Callable[[LogMetadata], _LT],
        description: str,
        commit_id: int | None = None,
    ) -> _LT:
        """
        Create a log object using the given description, commit ID, and log creation
        function. If no commit ID is given,
        """
        # pylint: disable=protected-access
        if commit_id is None:
            latest_commit = self._root_logger._param_db.latest_commit
            if latest_commit is None:
                raise IndexError(
                    "cannot tag log with most recent commit because ParamDB at"
                    f" '{self._root_logger._param_db.path}' is empty"
                )
            commit_id = latest_commit.id
        log_metadata = LogMetadata(
            self._root_logger._log_directory,
            self._graph_logger.name,
            self.name,
            commit_id,
            description,
            datetime.now(timezone.utc).astimezone(),
            self._root_logger._param_db.path,
        )
        log = make_log(log_metadata)
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
        Construct a :py:class:`DataLog` from the given data (which internally converts
        the given :py:class:`Coord`s and :py:class:`DataVar`s into an Xarray
        ``Dataset``), save it as a NetCDF file, and return the :py:class:`DataLog`.
        Metadata, including the log directory, graph and node names, commit ID,
        description, created timestamp, and ParamDB path, will also be saved.

        The filename will include the commit ID and the given description. If no commit
        ID is given, the latest commit ID at the time this function is called will be
        used.
        """

        def make_log(log_metadata: LogMetadata) -> DataLog:
            return DataLog.from_variables(log_metadata, coords, data_vars)

        return self._log(make_log, description, commit_id)

    def log_dict(
        self, description: str, dict_data: dict[str, Any], commit_id: int | None = None
    ) -> DictLog:
        """
        Save the given dictionary data in a JSON file, along with metadata containing
        the graph and node names, the log description, the commit ID, the timestamp of
        when this log was created, and the ParamDB path.
        """

        def make_log(log_metadata: LogMetadata) -> DictLog:
            return DictLog(log_metadata, dict_data)

        return self._log(make_log, description, commit_id)
