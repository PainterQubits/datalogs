"""
Log objects that contain data and metadata, and can save data to and load data from a
file.
"""

from __future__ import annotations
from typing import TypeVar, Generic, Any
from collections.abc import Sequence
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
import os
from datetime import datetime
import json
from typing_extensions import Self
import xarray as xr
from datalogger._variables import Coord, DataVar

T = TypeVar("T")


@dataclass
class LogMetadata:
    """
    Metadata for a log, including the log directory, graph and node names, commit ID,
    description, created timestamp, and ParamDB path.
    """

    log_directory: str
    graph: str
    node: str
    commit_id: int
    description: str
    created_timestamp: datetime | None = None
    paramdb_path: str | None = None


def _metadata_to_dict(metadata: LogMetadata, prefix: str = "") -> dict[str, Any]:
    metadata_dict = {}
    for field in fields(LogMetadata):
        value = getattr(metadata, field.name)
        if field.name == "created_timestamp" and isinstance(value, datetime):
            value = value.isoformat()
        metadata_dict[prefix + field.name] = value
    return metadata_dict


def _metadata_from_dict(metadata_dict: dict[Any, Any], prefix: str = "") -> LogMetadata:
    metadata_kwargs = {}
    for field in fields(LogMetadata):
        value = metadata_dict.pop(prefix + field.name)
        if field.name == "created_timestamp" and isinstance(value, str):
            value = datetime.fromisoformat(value)
        metadata_kwargs[field.name] = value
    return LogMetadata(**metadata_kwargs)


class _Log(ABC, Generic[T]):
    """Abstract base class for logs."""

    _ext: str

    def __init_subclass__(cls, /, ext: str, *args: Any, **kwargs: Any) -> None:
        super().__init_subclass__()
        cls._ext = ext

    def __init__(self, metadata: LogMetadata, data: T):
        self._metadata = metadata
        self._data = data

    @property
    def metadata(self) -> LogMetadata:
        """Metadata associated with this log."""
        return self._metadata

    @property
    def data(self) -> T:
        """Data stored in this log."""
        return self._data

    @classmethod
    def _path(cls, metadata: LogMetadata) -> str:
        """Path to the log file determined by the given metadata."""
        log_path = os.path.join(
            metadata.log_directory,
            metadata.graph,
            metadata.node,
            f"{metadata.commit_id}_{metadata.description}.{cls._ext}",
        )
        return log_path

    @property
    def path(self) -> str:
        """Path to the log file to save to."""
        return self._path(self._metadata)

    @abstractmethod
    def _save(self, path: str) -> None:
        ...

    def save(self) -> None:
        """Save log to a file."""
        path = self.path
        if os.path.exists(path):
            raise FileExistsError(f"log '{path}' already exists")
        self._save(path)

    @classmethod
    @abstractmethod
    def _load(cls, path: str) -> Self:
        ...

    @classmethod
    def load(cls, path_or_metadata: str | LogMetadata) -> Self:
        """Load from the log file specified by the given path or metadata."""
        return cls._load(
            path_or_metadata
            if isinstance(path_or_metadata, str)
            else cls._path(path_or_metadata)
        )


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
        )
        return DataLog(metadata, dataset)

    def _save(self, path: str) -> None:
        attrs_with_metadata = {
            **self._dataset.attrs,
            **_metadata_to_dict(self.metadata, prefix="__metadata_"),
        }
        dataset_with_metadata = self._dataset.assign_attrs(attrs_with_metadata)
        dataset_with_metadata.to_netcdf(path)

    @classmethod
    def _load(cls, path: str) -> DataLog:
        dataset = xr.open_dataset(path)
        metadata = _metadata_from_dict(dataset.attrs, prefix="__metadata_")
        return DataLog(metadata, dataset)


class DictLog(_Log[dict[str, Any]], ext="json"):
    """
    Log containing a dictionary which can be saved to a JSON (".json") file.
    """

    def __init__(self, metadata: LogMetadata, data_dict: dict[str, Any]):
        self._data_dict = data_dict
        super().__init__(metadata, data_dict)

    def _save(self, path: str) -> None:
        data_dict_with_metadata = {
            **self.data,
            "__metadata": _metadata_to_dict(self.metadata),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_dict_with_metadata, f, indent=2)

    @classmethod
    def _load(cls, path: str) -> DictLog:
        with open(path, "r", encoding="utf-8") as f:
            data_dict = json.load(f)
            if not isinstance(data_dict, dict):
                raise TypeError("")
        metadata = _metadata_from_dict(data_dict.pop("__metadata"))
        return DictLog(metadata, data_dict)
