"""Data logging classes."""

from __future__ import annotations
from typing import TypeVar, Any, overload
from collections.abc import Callable, Sequence
import os
from datetime import datetime, timezone
from datalogger._variables import Coord, DataVar
from datalogger._log import LogMetadata, DataLog, DictLog
from datalogger._get_filename import get_filename

try:
    from paramdb import ParamDB

    PARAMDB_INSTALLED = True
except ImportError:
    PARAMDB_INSTALLED = False


# Log type variable
_LT = TypeVar("_LT", DataLog, DictLog)


def _now() -> datetime:
    """Return the current time as a ``datetime`` object in the current timezone."""
    return datetime.now(timezone.utc).astimezone()


class Logger:
    """
    Logger corresponding to a directory that generates log files and
    sub-:py:class:`Logger` objects corresponding to subdirectories.

    If ``root_directory`` is given, that will be used as the directory, and this
    :py:class:`Logger` will function as a root. Optionally, ``param_db`` can be given to
    enable commit tagging.

    Otherwise, ``parent`` and ``description`` must be given, and this :py:class:`Logger`
    will correspond to a subdirectory within its parent's directory.
    """

    @overload
    def __init__(
        self, *, root_directory: str, param_db: ParamDB[Any] | None = None
    ) -> None:
        ...

    @overload
    def __init__(
        self,
        *,
        parent: Logger,
        description: str,
    ) -> None:
        ...

    def __init__(
        self,
        *,
        root_directory: str | None = None,
        parent: Logger | None = None,
        description: str | None = None,
        param_db: ParamDB[Any] | None = None,
    ) -> None:
        self._name = root_directory
        self._parent = parent
        self._description = description
        self._param_db: ParamDB[Any] | None = (
            parent._param_db if parent is not None else param_db
        )
        if root_directory is not None:
            self._create_directory()

    def sub_logger(self, description: str) -> Logger:
        """
        Create a new sub-:py:class:`Logger` with the given description corresponding to
        a subdirectory within the parent :py:class:`Logger`.
        """
        return Logger(parent=self, description=description)

    @property
    def directory(self) -> str:
        """Directory where this logger saves subdirectories or files."""
        if self._name is None:
            if self._parent is None:
                raise TypeError(f"Logger '{self._description}' has no parent")
            if self._description is None:
                raise TypeError(f"Logger '{self._description}' has no description")
            self._name = get_filename(
                self._parent.directory,
                self._description,
                timestamp=_now(),
            )
        if self._parent is None:
            return self._name
        return os.path.join(self._parent.directory, self._name)

    def filepath(self, filename: str) -> str:
        """
        Generate a path to a file or directory with the given name within the directory
        of this :py:class:`Logger`.

        Note that this simply generates the path, with no checks for whether a file or
        directory with that path exists.
        """
        return os.path.join(self.directory, filename)

    def _create_directory(self) -> None:
        """Create the directory for this logger and its parents if they do not exist."""
        if self._parent is not None:
            self._parent._create_directory()  # pylint: disable=protected-access
        if not os.path.exists(self.directory):
            os.mkdir(self.directory)

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
        if self._param_db is not None and commit_id is None:
            latest_commit = self._param_db.latest_commit
            if latest_commit is None:
                raise IndexError(
                    "cannot tag log with most recent commit because ParamDB at"
                    f" '{self._param_db.path}' is empty"
                )
            commit_id = latest_commit.id
        self._create_directory()
        log = make_log(
            LogMetadata(
                directory=self.directory,
                timestamp=_now(),
                description=description,
                commit_id=commit_id,
                param_db_path=(
                    self._param_db.path if self._param_db is not None else None
                ),
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
        is given (and if this Logger has a corresponding ParamDB).
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
        is given (and if this Logger has a corresponding ParamDB).
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
        properties that can be converted directly to JSON will be saved.

        The log will be tagged with the given commit ID, or the latest commit ID if none
        is given (and if this Logger has a corresponding ParamDB).
        """
        props = {k: v for k, v in vars(obj).items() if self._should_save_prop(v)}
        return self.log_dict(description, props, commit_id)
