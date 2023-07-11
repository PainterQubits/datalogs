"""Data logging classes."""

from __future__ import annotations
from typing import Any
from collections.abc import Sequence
import os
import json
from datetime import datetime, timezone
from paramdb import ParamDB
from datalogger._variables import Coord, DataVar
from datalogger._logs import LogMetadata, DataLog


class DataLogger:
    """
    Base logger that generates :py:class:`GraphLogger` that use the given ParamDB and
    log directory.
    """

    def __init__(self, param_db: ParamDB[Any], log_directory: str) -> None:
        self._param_db = param_db
        self._log_directory = log_directory
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

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

    @property
    def directory(self) -> str:
        """Directory where this logger saves subdirectories or files."""
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


class GraphLogger(DataLogger):
    """
    Logger associated with a particular graph that generates :py:class:`NodeLogger`s for
    nodes within that graph.

    A description and commit ID are used to identify the graph. If no commit ID is
    given, the latest commit ID at the time this object is created will be used.
    """

    def __init__(
        self, parent: DataLogger, description: str, commit_id: int | None = None
    ) -> None:
        self._graph_description = description
        self._graph_commit_id = parent._commit_id_or_latest(commit_id)
        super().__init__(parent._param_db, parent._log_directory)

    @property
    def graph_name(self) -> str:
        """
        Name of the graph, composed of the commit ID and description. Used for the graph
        log directory and saved in each log's metadata.
        """
        return f"graph_{self._graph_commit_id}_{self._graph_description}"

    @property
    def directory(self) -> str:
        return os.path.join(super().directory, self.graph_name)

    def node_logger(self, description: str, commit_id: int | None = None) -> NodeLogger:
        """
        Generate a :py:class:`NodeLogger` with the given description and commit ID,
        which are used to uniquely identify the node.

        If no commit ID is given, the latest commit ID at the time this method is
        called will be used.
        """
        return NodeLogger(self, description, commit_id)


class NodeLogger(GraphLogger):
    """
    Logger associated with a particular node that generates that generates log files
    within a directory for that node.

    A description and commit ID are used to uniquely identify the node. If no commit ID
    is given, the latest commit ID at the time this object is created will be used.
    """

    def __init__(
        self, parent: GraphLogger, description: str, commit_id: int | None = None
    ) -> None:
        self._node_description = description
        self._node_commit_id = parent._commit_id_or_latest(commit_id)
        super().__init__(parent, parent._graph_description, parent._graph_commit_id)

    @property
    def node_name(self) -> str:
        """
        Name of the node, composed of the commit ID and description. Used for the node
        log directory and saved in each log's metadata.
        """
        return f"node_{self._node_commit_id}_{self._node_description}"

    @property
    def directory(self) -> str:
        return os.path.join(super().directory, self.node_name)

    def _log_metadata(self, description: str, commit_id: int) -> LogMetadata:
        """
        Metadata to store in the log file, including the given description and commit
        ID.
        """
        return LogMetadata(
            self._log_directory,
            self.graph_name,
            self.node_name,
            commit_id,
            description,
            datetime.now(timezone.utc).astimezone(),
            self._param_db.path,
        )

    def log_data(
        self,
        description: str,
        coords: Coord | Sequence[Coord],
        data_vars: DataVar | Sequence[DataVar],
        commit_id: int | None = None,
    ) -> DataLog:
        """
        Construct an Xarray ``Dataset`` from the given data, save it in a NetCDF file,
        and return the ``Dataset``.

        The filename will include the commit ID and the given description. If no commit
        ID is given, the latest commit ID at the time this function is called will be
        used.

        The ``Dataset``'s attribute dictionary will contain the graph and node names,
        the log description, the commit ID, the timestamp of when this log was created,
        and the ParamDB path.
        """
        commit_id = self._commit_id_or_latest(commit_id)
        data_log = DataLog.from_variables(
            self._log_metadata(description, commit_id), coords, data_vars
        )
        data_log.save()
        return data_log

    def log_dict(
        self, description: str, dict_data: dict[str, Any], commit_id: int | None = None
    ) -> dict[str, Any]:
        """
        Save the given dictionary data in a JSON file, along with metadata containing
        the graph and node names, the log description, the commit ID, the timestamp of
        when this log was created, and the ParamDB path.
        """
        commit_id = self._commit_id_or_latest(commit_id)
        log_path = self._log_path(description, commit_id, is_data_log=False)
        dict_data_with_metadata = {
            **dict_data,
            "__metadata": self._log_metadata(description, commit_id),
        }
        with open(log_path, "x", encoding="utf-8") as f:
            json.dump(dict_data_with_metadata, f, indent=2)
        return dict_data_with_metadata
