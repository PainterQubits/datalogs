"""Data logging classes."""

from __future__ import annotations
from typing import TypeVar, Any
from collections.abc import Sequence
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

    def __init__(self, param_db: ParamDB[Any], log_directory: str) -> None:
        self._param_db = param_db
        self._log_directory = log_directory

    @property
    @abstractmethod
    def directory(self) -> str:
        """Directory where this logger saves subdirectories or files."""

    def _commit_id_or_latest(self, commit_id: int | None) -> int:
        """
        Return the given commit ID if it is not None. Otherwise, return the latest
        commit ID from the ParamDB.
        """
        if commit_id is None:
            latest_commit = self._param_db.latest_commit
            if latest_commit is None:
                raise IndexError(
                    "cannot tag log with most recent commit because ParamDB at"
                    f" '{self._param_db.path}' is empty"
                )
            commit_id = latest_commit.id
        return commit_id


class DataLogger(_Logger):
    """
    Logger to generate :py:class:`GraphLogger` using the given ParamDB and base
    directory.
    """

    @property
    def directory(self) -> str:
        return self._log_directory

    def graph_logger(
        self, description: str, commit_id: int | None = None
    ) -> GraphLogger:
        """
        Create a :py:class:`GraphLogger` with the given description and commit ID, which
        are used to uniquely identify the graph.

        If no commit ID is given, the latest commit ID at the time this method is called
        will be used.
        """
        return GraphLogger(self, description, commit_id)


class GraphLogger(_Logger):
    """
    Logger associated with a particular graph that generates :py:class:`NodeLogger`s for
    nodes within that graph.

    A description and commit ID are used to identify the graph. If no commit ID is
    given, the latest commit ID at the time this object is created will be used.
    """

    def __init__(
        self, data_logger: DataLogger, description: str, commit_id: int | None = None
    ) -> None:
        super().__init__(data_logger._param_db, data_logger._log_directory)
        self._graph_name = f"graph_{self._commit_id_or_latest(commit_id)}_{description}"

    @property
    def directory(self) -> str:
        return os.path.join(self._log_directory, self._graph_name)

    def node_logger(self, description: str, commit_id: int | None = None) -> NodeLogger:
        """
        Generate a :py:class:`NodeLogger` with the given description and commit ID,
        which are used to uniquely identify the node.

        If no commit ID is given, the latest commit ID at the time this method is
        called will be used.
        """
        return NodeLogger(self, description, commit_id)


class NodeLogger(_Logger):
    """
    Logger associated with a particular node that generates that generates log files
    within a directory for that node.

    A description and commit ID are used to uniquely identify the node. If no commit ID
    is given, the latest commit ID at the time this object is created will be used.
    """

    def __init__(
        self, graph_logger: GraphLogger, description: str, commit_id: int | None = None
    ) -> None:
        super().__init__(graph_logger._param_db, graph_logger._log_directory)
        self._graph_name = graph_logger._graph_name
        self._node_name = f"node_{self._commit_id_or_latest(commit_id)}_{description}"

    @property
    def directory(self) -> str:
        return os.path.join(self._log_directory, self._graph_name, self._node_name)

    def _log_metadata(self, description: str, commit_id: int | None) -> LogMetadata:
        """
        Metadata to store in the log file, including the given description and commit
        ID.
        """
        return LogMetadata(
            self._log_directory,
            self._graph_name,
            self._node_name,
            self._commit_id_or_latest(commit_id),
            description,
            datetime.now(timezone.utc).astimezone(),
            self._param_db.path,
        )

    def _save_and_return(self, log: _LT) -> _LT:
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
        return self._save_and_return(
            DataLog.from_variables(
                self._log_metadata(description, commit_id), coords, data_vars
            )
        )

    def log_dict(
        self, description: str, dict_data: dict[str, Any], commit_id: int | None = None
    ) -> DictLog:
        """
        Save the given dictionary data in a JSON file, along with metadata containing
        the graph and node names, the log description, the commit ID, the timestamp of
        when this log was created, and the ParamDB path.
        """
        return self._save_and_return(
            DictLog(self._log_metadata(description, commit_id), dict_data)
        )
