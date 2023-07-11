"""
Log objects that contain data and metadata, and can save data to and load data from a
file.
"""

from __future__ import annotations
from typing import TypeVar, Generic, Any
from collections.abc import Sequence
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
import os
from datetime import datetime

# import json
from typing_extensions import Self
import xarray as xr
from datalogger._variables import Coord, DataVar

T = TypeVar("T")


@dataclass
class LogPathInfo:
    """Metadata required to determine the path for a given log."""

    log_directory: str
    graph: str
    node: str
    commit_id: int
    description: str


@dataclass
class LogMetadata(LogPathInfo):
    """
    Metadata for a log, including the required path information as well as the created
    timestamp and ParamDB path.
    """

    created_timestamp: datetime
    paramdb_path: str


class _Log(ABC, Generic[T]):
    """Abstract base class for logs."""

    _ext: str

    def __init_subclass__(cls, /, ext: str, *args: Any, **kwargs: Any) -> None:
        super().__init_subclass__()
        cls._ext = ext

    def __init__(self, metadata: LogPathInfo, data: T):
        self._metadata = metadata
        self._data = data

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> Self:
        """Load from the log file at the given path."""

    @abstractmethod
    def save(self) -> None:
        """Save log to a file."""

    # pylint: disable=too-many-arguments
    def _get_path(
        self,
        log_directory: str,
        graph_name: str,
        node_name: str,
        commit_id: int,
        description: str,
    ) -> str:
        """
        Path to the log file determined by the given log directory, graph and node
        names, commit ID, description, and extension.
        """
        log_path = os.path.join(
            log_directory,
            graph_name,
            node_name,
            f"{commit_id}_{description}.{self._ext}",
        )
        if os.path.exists(log_path):
            raise FileExistsError(f"log '{log_path}' already exists")
        return log_path

    @property
    def path(self) -> str:
        """Path to the log file to save to."""
        metadata = self._metadata
        return self._get_path(
            metadata.log_directory,
            metadata.graph,
            metadata.node,
            metadata.commit_id,
            metadata.description,
        )

    @property
    def metadata(self) -> LogPathInfo:
        """Metadata associated with this log."""
        return self._metadata

    @property
    def data(self) -> T:
        """Data stored in this log."""
        return self._data


class DataLog(_Log[xr.Dataset], ext="nc"):
    """
    Log containing an Xarray ``Dataset`` which can be saved to a NetCDF (".nc") file.

    See https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html.
    """

    def __init__(self, metadata: LogMetadata, dataset: xr.Dataset):
        self._dataset = dataset
        super().__init__(metadata, dataset)

    @classmethod
    def from_variables(
        cls,
        metadata: LogMetadata,
        coords: Coord | Sequence[Coord],
        data_vars: DataVar | Sequence[DataVar],
    ) -> DataLog:
        """
        Create a data log containing an Xarray ``Dataset`` constructed from the given
        coordinate and data variables.
        """
        coords = [coords] if isinstance(coords, Coord) else coords
        data_vars = [data_vars] if isinstance(data_vars, DataVar) else data_vars
        dataset = xr.Dataset(
            data_vars={data_var.name: data_var.variable for data_var in data_vars},
            coords={coord.name: coord.variable for coord in coords},
            attrs=asdict(metadata),
        )
        return DataLog(metadata, dataset)

    @classmethod
    def load(cls, path: str) -> DataLog:
        dataset = xr.open_dataset(path)
        return DataLog(LogMetadata(**dataset.attrs), dataset)

    def save(self) -> None:
        self._dataset.to_netcdf(self.path)


class DictLog(_Log[dict[str, Any]], ext="json"):
    """
    Log containing a dictionary which can be saved to a JSON (".json") file.
    """

    def __init__(self, metadata: LogMetadata, data_dict: dict[str, Any]):
        self._data_dict = data_dict
        super().__init__(metadata, data_dict)

    @classmethod
    def load(cls, path: str) -> DictLog:
        with open(path, "r") as f:
            data_dict = json.load(f)
            if not isinstance(data_dict, dict):
                raise TypeError("")
        metadata = data_dict.pop("__metadata")
        return DictLog(LogMetadata(**metadata), data_dict)
