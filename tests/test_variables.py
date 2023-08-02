"""Tests for datalogger._variables."""

from numpy.testing import assert_array_equal
import xarray as xr
from datalogger._variables import Coord, DataVar


def test_coord_name(coord: Coord) -> None:
    """Name of a Coord object can be retrieved."""
    assert coord.name == "time"


def test_data_var_name(data_var: DataVar) -> None:
    """Name of a DataVar object can be retrieved."""
    assert data_var.name == "signal"


def test_coord_variable(coord: Coord) -> None:
    """
    Underlying Xarray variable of a Coord object can be retrieved and has the correct
    contents.
    """
    assert isinstance(coord.variable, xr.Variable)
    assert coord.variable.dims == ("time",)
    assert_array_equal(coord.variable.data, [1, 2, 3])
    assert coord.variable.attrs == {"long_name": "Time", "units": "s"}


def test_data_var_variable(data_var: DataVar) -> None:
    """
    Underlying Xarray variable of a DataVar object can be retrieved and has the correct
    contents.
    """
    assert isinstance(data_var.variable, xr.Variable)
    assert data_var.variable.dims == ("time",)
    assert_array_equal(data_var.variable.data, [10, 20, 30])
    assert data_var.variable.attrs == {"long_name": "Signal", "units": "V"}


def test_no_long_name() -> None:
    """``long_name`` is optional for Coord and DataVar objects."""
    coord = Coord("time", data=[1, 2, 3], units="s")
    data_var = DataVar("signal", dims="time", data=[10, 20, 30], units="V")
    assert coord.variable.attrs == {"units": "s"}
    assert data_var.variable.attrs == {"units": "V"}


def test_no_units() -> None:
    """``units`` is optional for Coord and DataVar objects."""
    coord = Coord("time", data=[1, 2, 3], long_name="Time")
    data_var = DataVar("signal", dims="time", data=[10, 20, 30], long_name="Signal")
    assert coord.variable.attrs == {"long_name": "Time"}
    assert data_var.variable.attrs == {"long_name": "Signal"}


def test_no_attrs() -> None:
    """The `attrs` dictionary is empty if no ``long_name`` or ``units`` are given."""
    coord = Coord("time", data=[1, 2, 3])
    data_var = DataVar("signal", dims="time", data=[10, 20, 30])
    assert coord.variable.attrs == {}
    assert data_var.variable.attrs == {}


def test_3d_data_var() -> None:
    """A 3-dimensional DataVar object can be defined."""
    dims = ("x", "y", "time")
    data = [[[1, 2], [3, 4]], [[5, 6], [7, 8]]]
    data_var = DataVar("signal", dims=dims, data=data, long_name="Signal", units="V")
    assert data_var.variable.dims == dims
    assert_array_equal(data_var.variable.data, data)
