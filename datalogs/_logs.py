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
import pprint
from textwrap import indent
from typing_extensions import Self
import xarray as xr
from datalogs._variables import Coord, DataVar
from datalogs._get_filename import get_filename


_T = TypeVar("_T")


@dataclass
class LogMetadata:
    """
    Metadata for a log, including the directory path, commit ID, description, created
    timestamp, and ParamDB path.
    """

    directory: str
    """Directory this log was created in."""
    timestamp: datetime
    """When the log was created."""
    description: str
    """Log description."""
    commit_id: int | None
    """Commit ID in the ParamDB."""
    param_db_path: str | None
    """Path to the ParamDB."""

    def __repr__(self) -> str:
        field_values = ""
        for field in fields(self):
            field_values += f"{field.name:<15}{getattr(self, field.name)}\n"
        return field_values[:-1]


def _metadata_to_dict(metadata: LogMetadata, prefix: str = "") -> dict[str, Any]:
    metadata_dict = {}
    for field in fields(LogMetadata):
        value = getattr(metadata, field.name)
        if value is not None:
            if field.name == "timestamp" and isinstance(value, datetime):
                value = value.isoformat()
            metadata_dict[prefix + field.name] = value
    return metadata_dict


def _metadata_from_dict(metadata_dict: dict[Any, Any], prefix: str = "") -> LogMetadata:
    metadata_kwargs = {}
    for field in fields(LogMetadata):
        prefixed_name = prefix + field.name
        value = (
            metadata_dict.pop(prefixed_name) if prefixed_name in metadata_dict else None
        )
        if field.name == "timestamp" and isinstance(value, str):
            value = datetime.fromisoformat(value)
        metadata_kwargs[field.name] = value
    return LogMetadata(**metadata_kwargs)


class _Log(ABC, Generic[_T]):
    """Abstract base class for logs."""

    _ext: str

    def __init_subclass__(cls, /, ext: str, *args: Any, **kwargs: Any) -> None:
        super().__init_subclass__(*args, **kwargs)
        cls._ext = ext

    def __init__(self, metadata: LogMetadata, data: _T, path: str | None = None):
        self._metadata = metadata
        self._data = data
        self._path = path

    @property
    def metadata(self) -> LogMetadata:
        """Metadata associated with this log."""
        return self._metadata

    @property
    def data(self) -> _T:
        """Data stored in this log."""
        return self._data

    @property
    def path(self) -> str:
        """Path to the log file."""
        if self._path is None:
            directory = self._metadata.directory
            self._path = os.path.join(
                directory,
                get_filename(directory, self._metadata.description, ext=self._ext),
            )
        return self._path

    @abstractmethod
    def _save(self, path: str) -> None:  # pragma: no cover
        ...

    def save(self) -> None:
        """Save log to a file."""
        path = self.path
        if os.path.exists(path):
            raise FileExistsError(f"log '{path}' already exists")
        self._save(path)

    @classmethod
    @abstractmethod
    def load(cls, path: str) -> Self:
        """Load from the log file specified by the given path."""

    def __repr__(self) -> str:
        if isinstance(self.data, dict):
            data_repr = pprint.pformat(self.data, sort_dicts=False, compact=True)
        else:
            data_repr = repr(self.data)
        data_repr = indent(data_repr, "  ")
        metadata_repr = indent(repr(self.metadata), "  ")
        return (
            f"<{type(self).__name__} '{self.path}'>\n"
            f"Data:\n{data_repr}\n"
            f"Metadata:\n{metadata_repr}"
        )


class DataLog(_Log[xr.Dataset], ext=".nc"):
    """
    Log containing an Xarray ``Dataset`` which can be saved to a NetCDF (".nc") file.

    See https://docs.xarray.dev/en/stable/generated/xarray.Dataset.html.
    """

    def __init__(
        self, metadata: LogMetadata, dataset: xr.Dataset, path: str | None = None
    ):
        self._dataset = dataset
        super().__init__(metadata, dataset, path)

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

    # Allows return type to show properly in Sphinx autodoc
    @property
    def data(self) -> xr.Dataset:
        return super().data

    def _save(self, path: str) -> None:
        attrs_with_metadata = {
            **self._dataset.attrs,
            **_metadata_to_dict(self.metadata, prefix="__metadata_"),
        }
        dataset_with_metadata = self._dataset.assign_attrs(attrs_with_metadata)
        dataset_with_metadata.to_netcdf(path)

    @classmethod
    def load(cls, path: str) -> DataLog:
        dataset = xr.load_dataset(path)
        metadata = _metadata_from_dict(dataset.attrs, prefix="__metadata_")
        return DataLog(metadata, dataset, path)


class DictLog(_Log[dict[str, Any]], ext=".json"):
    """Log containing a dictionary which can be saved to a JSON (".json") file."""

    def __init__(
        self, metadata: LogMetadata, data_dict: dict[str, Any], path: str | None = None
    ):
        if not isinstance(data_dict, dict):
            raise TypeError(
                f"'{type(data_dict).__name__}' data given for dict log"
                f" '{metadata.description}'"
            )
        self._data_dict = data_dict
        super().__init__(metadata, data_dict, path)

    # Allows return type to show properly in Sphinx autodoc
    @property
    def data(self) -> dict[str, Any]:
        return super().data

    def _save(self, path: str) -> None:
        data_dict_with_metadata = {
            **self.data,
            "__metadata": _metadata_to_dict(self.metadata),
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_dict_with_metadata, f, indent=2)

    @classmethod
    def load(cls, path: str) -> DictLog:
        with open(path, "r", encoding="utf-8") as f:
            data_dict = json.load(f)
            if not isinstance(data_dict, dict):
                raise TypeError(f"'{path}' does not contain a dictionary")
        metadata = _metadata_from_dict(data_dict.pop("__metadata"))
        return DictLog(metadata, data_dict, path)
