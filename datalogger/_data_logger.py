"""Data logging classes."""

from __future__ import annotations
from typing import Any
import os
import time
import xarray as xr
from paramdb import ParamDB


class DataLogger:
    """
    Base data logger to generate :py:class:`GraphDataLogger` objects that use the given
    ParamDB and log directory.
    """

    def __init__(self, param_db: ParamDB[Any], log_directory: str) -> None:
        self._param_db = param_db
        self._log_directory = log_directory
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

    def _commit_id_or_latest(
        self, param_db: ParamDB[Any], commit_id: int | None
    ) -> int:
        """
        If the given commit ID is None, return the latest commit ID from the given ParamDB.
        Otherwise, return the given commit ID.
        """
        if commit_id is None:
            latest_commit = param_db.latest_commit
            if latest_commit is None:
                raise IndexError(
                    "cannot tag log with most recent commit because ParamDB at"
                    f" '{self._param_db.path}' is empty"
                )
            commit_id = latest_commit.id
        return commit_id

    @property
    def directory(self) -> str:
        """Directory where this logger saves files."""
        return self._log_directory

    def graph_logger(
        self, graph_description: str, graph_commit_id: int | None = None
    ) -> GraphDataLogger:
        """
        Generate a :py:class:`GraphDataLogger` with the given description and commit ID,
        or the latest commit ID if one is not provided.
        """
        return GraphDataLogger(
            self._param_db, self._log_directory, graph_description, graph_commit_id
        )


class GraphDataLogger(DataLogger):
    def __init__(
        self,
        param_db: ParamDB[Any],
        log_directory: str,
        graph_description: str,
        graph_commit_id: int | None = None,
    ) -> None:
        self._graph_description = graph_description
        self._graph_commit_id = self._commit_id_or_latest(param_db, graph_commit_id)
        super().__init__(param_db, log_directory)

    @property
    def graph_name(self) -> str:
        return f"graph_{self._graph_commit_id}_{self._graph_description}"

    @property
    def directory(self) -> str:
        return os.path.join(super().directory, self.graph_name)

    def node_logger(
        self, node_description: str, node_commit_id: int | None = None
    ) -> NodeDataLogger:
        return NodeDataLogger(
            self._param_db,
            self._log_directory,
            self._graph_description,
            node_description,
            self._graph_commit_id,
            node_commit_id,
        )


class NodeDataLogger(GraphDataLogger):
    def __init__(
        self,
        param_db: ParamDB[Any],
        log_directory: str,
        graph_description: str,
        node_description: str,
        graph_commit_id: int | None = None,
        node_commit_id: int | None = None,
    ) -> None:
        self._node_description = node_description
        self._node_commit_id = self._commit_id_or_latest(param_db, node_commit_id)
        super().__init__(param_db, log_directory, graph_description, graph_commit_id)

    @property
    def node_name(self) -> str:
        return f"node_{self._node_commit_id}_{self._node_description}"

    @property
    def directory(self) -> str:
        return os.path.join(super().directory, self.node_name)

    def _log_filename(
        self, log_type: str, log_description: str, log_commit_id: int
    ) -> str:
        return os.path.join(
            self.directory, f"{log_commit_id}_{log_type}_{log_description}.nc"
        )

    def log(
        self, log_description: str, analysis: bool = False, commit_id: int | None = None
    ) -> xr.Dataset:
        """
        Log the given experiment or analysis data for the given graph and node.

        The default is to create a data log, but an analysis log will be created if
        ``analysis`` is True.

        The log will be tagged with a ParamDB commit ID (``commit_id`` if given, or the
        ID of the latest commit if not).
        """
        log_type = "analysis" if analysis else "data"
        commit_id = self._commit_id_or_latest(self._param_db, commit_id)
        dataset = xr.Dataset(
            attrs={
                "graph": self.graph_name,
                "node": self.node_name,
                "log_type": log_type,
                "paramdb_path": os.path.abspath(self._param_db.path),
                "paramdb_commit_id": commit_id,
                "created_timestamp": time.time(),
            },
        )
        # if not os.path.exists(self.directory):
        #     os.makedirs(self.directory)
        log_filename = self._log_filename(log_type, log_description, commit_id)
        if os.path.exists(log_filename):
            raise FileExistsError(
                f"{log_type} log '{log_description}' for {self.graph_name},"
                f" {self.node_name}, commit {commit_id} already exists"
            )
        dataset.to_netcdf(log_filename)
        return dataset
