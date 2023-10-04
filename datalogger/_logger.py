"""Data logging classes."""

from __future__ import annotations
from typing import TypeVar, Any, overload
from collections.abc import Callable, Sequence, Collection, Mapping
import os
from datetime import datetime, timezone
from datalogger._variables import Coord, DataVar
from datalogger._logs import LogMetadata, DataLog, DictLog
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

    Otherwise, ``parent`` and ``description`` must be given, and this will be a
    sub-:py:class:`Logger` object that corresponds to a subdirectory within its parent's
    directory (and uses its parent's ParamDB, if given). See
    :py:meth:`Logger.sub_logger` for an explanation of the ``timestamp`` option.
    """

    @overload
    def __init__(
        self, root_directory: str, param_db: ParamDB[Any] | None = None
    ) -> None:  # pragma: no cover
        ...

    @overload
    def __init__(
        self, *, parent: Logger, description: str, timestamp: bool = True
    ) -> None:  # pragma: no cover
        ...

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        root_directory: str | None = None,
        param_db: ParamDB[Any] | None = None,
        *,
        parent: Logger | None = None,
        description: str | None = None,
        timestamp: bool = True,
    ) -> None:
        if root_directory is None:
            if parent is None:
                raise TypeError("Logger with no root_directory must have a parent")
            if description is None:
                raise TypeError("Logger with no root_directory must have a description")
        else:
            if parent is not None:
                raise TypeError("Logger with a root_directory cannot have a parent")
            if description is not None:
                raise TypeError(
                    "Logger with a root_directory cannot have a description"
                )
        self._name = root_directory
        self._parent = parent
        self._description = description
        self._timestamp = timestamp
        self._param_db: ParamDB[Any] | None = (
            parent._param_db if parent is not None else param_db
        )
        if root_directory is not None or not timestamp:
            # Generate this logger's directory, if it is a root Logger or a sub-Logger
            # with no timestamp.
            self.directory  # pylint: disable=pointless-statement

    def sub_logger(self, description: str, timestamp: bool = True) -> Logger:
        """
        Create a new sub-:py:class:`Logger` with the given description corresponding to
        a subdirectory within the parent :py:class:`Logger`.

        By default, ``timestamp`` is True, meaning that the directory name will include
        a timestamp corresponding to when it was created. (Note that the directory will
        be created when first needed so that the timestamp more accurately reflects when
        its content was created.)

        If ``timestamp`` is False, the directory name will not include a timestamp. If
        there is an existing directory, it will be used. If not, a new directory will be
        created immediately.
        """
        return Logger(parent=self, description=description, timestamp=timestamp)

    @property
    def directory(self) -> str:
        """
        Directory where this logger saves subdirectories or files.

        If the directory does not yet exist (i.e. if this is a sub-:py:class:`Logger`
        with a timestamp), it is created.
        """
        if self._name is None:
            # If self._name is None, both self._parent and self._description should have
            # been defined in self.__init__().
            assert self._parent is not None, "sub-Logger must have a parent"
            assert self._description is not None, "sub-Logger must have a description"
            self._name = (
                get_filename(
                    self._parent.directory,
                    self._description,
                    timestamp=_now(),
                )
                if self._timestamp
                else self._description
            )
        directory = (
            self._name
            if self._parent is None
            else os.path.join(self._parent.directory, self._name)
        )
        if not os.path.exists(directory):
            os.mkdir(directory)
        return directory

    def file_path(self, filename: str) -> str:
        """
        Generate a path to a file or directory with the given name within the directory
        of this :py:class:`Logger`.

        Note that this simply generates the path, with no checks for whether a file or
        directory with that path exists.
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
        if self._param_db is not None and commit_id is None:
            latest_commit = self._param_db.latest_commit
            if latest_commit is None:
                raise IndexError(
                    f"cannot tag log '{description}' with most recent commit because"
                    f" ParamDB '{self._param_db.path}' is empty"
                )
            commit_id = latest_commit.id
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
    def _convert_to_json(cls, obj: Any) -> Any:
        """
        Return a JSON-serializable version of the given object by converting ``Mapping``
        and ``Collection`` objects to dictionaries and lists, converting other
        non-JSON-serializable values to ``repr`` strings, and converting all dictionary
        keys to strings.
        """
        if isinstance(obj, (str, int, float, bool)) or obj is None:
            return obj
        if isinstance(obj, Mapping):
            return {str(k): cls._convert_to_json(v) for k, v in obj.items()}
        if isinstance(obj, Collection):
            return [cls._convert_to_json(v) for v in obj]
        return repr(obj)

    def log_props(
        self, description: str, obj: Any, commit_id: int | None = None
    ) -> DictLog:
        """
        Save a dictionary of the given object's properties and corresponding metadata in
        a JSON file, and return a :py:class:`DictLog` with this data and metadata. The
        object must be one with properties (i.e. one that has a ``__dict__`` property).

        This function will attempt to convert values that are not JSON-serializable to
        lists or dictionaries, and otherwise will convert them to string
        representations. This is intended to save a snapshot of the current properties
        of the given object, but makes no guarentees that all information is saved.

        The log will be tagged with the given commit ID, or the latest commit ID if none
        is given (and if this Logger has a corresponding ParamDB).
        """
        try:
            obj_vars = vars(obj)
        except TypeError as exc:
            raise TypeError(
                f"'{type(obj).__name__}' object is not supported by log_props"
            ) from exc
        return self.log_dict(description, self._convert_to_json(obj_vars), commit_id)
