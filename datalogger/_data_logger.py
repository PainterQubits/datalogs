"""Data logging functions."""

from typing import Any
import os
import xarray as xr
from paramdb import ParamDB


class DataLogger:
    """Logger for saving experiment and analysis data."""

    def __init__(self, param_db: ParamDB[Any], log_directory: str) -> None:
        self.param_db = param_db
        self.log_directory = log_directory
        if not os.path.exists(log_directory):
            os.mkdir(log_directory)

    def _log_filename(
        self, graph: str, node: str, log_type: str, commit_id: int
    ) -> str:
        node_directory = self.node_directory(graph, node)
        os.makedirs(node_directory, exist_ok=True)
        return os.path.join(node_directory, f"{log_type}_{commit_id}.nc")

    def node_directory(self, graph: str, node: str) -> str:
        """Directory path for the given graph and node."""
        return os.path.join(self.log_directory, graph, node)

    def log(
        self,
        graph: str,
        node: str,
        analysis: bool = False,
        commit_id: int | None = None,
    ) -> None:
        """
        Log the given experiment or analysis data for the given graph and node.

        The default is to create a data log, but an analysis log will be created if
        ``analysis`` is True.

        The log will be tagged with a ParamDB commit ID (``commit_id`` if given, or the
        ID of the latest commit if not).
        """
        log_type = "analysis" if analysis else "data"
        if commit_id is None:
            latest_commit = self.param_db.latest_commit
            if latest_commit is None:
                raise IndexError(
                    "cannot tag the log with the most recent commit because database"
                    f" {self.param_db.path} is empty"
                )
            commit_id = latest_commit.id
        data = xr.Dataset()
        log_filename = self._log_filename(graph, node, log_type, commit_id)
        if os.path.exists(log_filename):
            raise FileExistsError(
                f"{log_type} log for graph {graph}, node {node}, commit {commit_id}"
                f" already exists"
            )
        data.to_netcdf(log_filename)
