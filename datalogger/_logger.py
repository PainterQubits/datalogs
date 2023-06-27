"""Data logging functions."""

import xarray as xr


def save(path: str) -> None:
    """Save data in a NetCDF file at the given path."""
    data = xr.Dataset()
    data.to_netcdf(path)
