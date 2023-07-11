"""Example of saving data using DataLogger."""

from paramdb import ParamDB
from datalogger import Coord, DataVar, DataLogger

param_db = ParamDB[int]("qpu.db")
data_logger = DataLogger(param_db, "data_logs")

param_db.commit("Commit 1", 101)
param_db.commit("Commit 2", 102)
param_db.commit("Commit 3", 103)
param_db.commit("Commit 4", 104)
param_db.commit("Commit 5", 105)

for i in range(5):
    graph_logger = data_logger.graph_logger("cross_entropy")
    for j in range(5):
        rabi_calibration_logger = graph_logger.node_logger("rabi_calibration")
        param_db.commit("Commit", 10 * i + j)
        time = Coord("time", data=[1, 2, 3], long_name="Time", units="s")
        signal = DataVar(
            "signal", dims="time", data=[10, 20, 30], long_name="Signal", units="V"
        )
        rabi_calibration_logger.log_data("rabi", [time], [signal])
        rabi_calibration_logger.log_dict("rabi_fit", {"param1": 1, "param2": 2})
