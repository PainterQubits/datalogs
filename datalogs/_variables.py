"""
Wrappers for the Xarray ``Variable`` class to represent data and dimensional
coordinates when creating a data log.
"""

from __future__ import annotations
from collections.abc import Sequence
from numpy.typing import ArrayLike
import xarray as xr


class _Variable:
    """Wrapper for an Xarray ``Variable``."""

    # pylint: disable-next=too-many-arguments
    def __init__(
        self,
        name: str,
        dims: str | Sequence[str],
        data: ArrayLike,
        long_name: str | None = None,
        units: str | None = None,
    ) -> None:
        self._name = name
        attrs = {}
        if long_name is not None:
            attrs["long_name"] = long_name
        if units is not None:
            attrs["units"] = units
        self._variable = xr.Variable(dims, data, attrs)

    @property
    def name(self) -> str:
        """Name of this coordinate or data."""
        return self._name

    @property
    def variable(self) -> xr.Variable:
        """
        Underlying Xarray ``Variable`` object.

        See https://docs.xarray.dev/en/stable/generated/xarray.Variable.html.
        """
        return self._variable


class Coord(_Variable):
    """
    Wrapper for an Xarray ``Variable`` representing a dimensional coordinate.

    - ``name`` is used as the coordinate and dimension name.
    - ``data`` should be a 1D array labeling points along the dimension.
    - ``long_name`` and ``units`` are stored in the underlying variable's attribute
      dictionary.

    See https://docs.xarray.dev/en/stable/user-guide/data-structures.html#coordinates
    for more information on coordinates in Xarray.
    """

    def __init__(
        self,
        name: str,
        data: ArrayLike,
        long_name: str | None = None,
        units: str | None = None,
    ) -> None:
        super().__init__(name, name, data, long_name, units)


class DataVar(_Variable):
    """
    Wrapper for an Xarray ``Variable`` representing a data variable along particular
    dimensions.

    - ``data`` should be an array that aligns with the named dimensions.
    - ``long_name`` and ``units`` are stored in the underlying variable's attribute
      dictionary.
    """
