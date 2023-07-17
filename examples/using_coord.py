import xarray as xr
from datalogger import Coord, DataVar


time = Coord("time", data=[1, 2, 3], long_name="Time", units="s")
signal = DataVar(
    "signal", dims="time", data=[0.12, 0.34, 0.56], long_name="Signal", units="V"
)

data = xr.Dataset(
    data_vars={signal.name: signal.variable}, coords={time.name: time.variable}
)
