"""Classes to mirror """

from typing import cast
import numpy as np
import xarray as xr


class _Variable(xr.Variable):
    pass


# pylint: disable-next=too-many-ancestors
class Coord(xr.Variable):  # type: ignore
    """
    Xarray ``Variable`` representing a coordinate in the dataset.

    This class inherits from the Xarray ``Variable`` class. See
    https://docs.xarray.dev/en/latest/generated/xarray.Variable.html for documentation
    on the properties, operations, and methods that can be used.
    """

    def __init__(
        self, name: str, long_name: str, units: str, values: list[int]
    ) -> None:
        """
        Create an Xarray ``Variable`` representing a coordinate variable in the dataset.
        The given name will also be used as the dimension name. The given ``long_name``
        and ``units`` will be stored in the ``attrs`` dictionary.

        See https://docs.xarray.dev/en/stable/user-guide/data-structures.html for more
        information on coordinates.

        This class inherits from the Xarray ``Variable`` class. See
        https://docs.xarray.dev/en/latest/generated/xarray.Variable.html for
        documentation on the properties, operations, and methods that can be used.
        """
        attrs = {"long_name": long_name, "units": units}
        super().__init__(name, values, attrs)  # type: ignore

    @property
    def long_name(self) -> str:
        return cast(str, self.attrs["long_name"])

    @long_name.setter
    def long_name(self, value: str) -> None:
        self.attrs["long_name"] = value

    @property
    def units(self) -> str:
        return cast(str, self.attrs["units"])

    @units.setter
    def units(self, value: str) -> None:
        self.attrs["units"] = value


class DataVar(xr.Variable):  # type: ignore
    """Data variable."""

    def __init__(self) -> None:
        """Data variable."""
        pass
