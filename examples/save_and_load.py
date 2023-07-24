"""Example of saving and loading logs."""

import os
from paramdb import ParamDB
from datalogger import Coord, DataVar, RootLogger, load_log

param_db = ParamDB[int]("qpu.db")
data_logger = RootLogger("data_logs", param_db)

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

root_dir = data_logger.directory
graph_dir = os.path.join(root_dir, os.listdir(root_dir)[0])
node_dir = os.path.join(graph_dir, os.listdir(graph_dir)[0])

for log_path in os.listdir(node_dir):
    log = load_log(os.path.join(node_dir, log_path))
    print(log, end="\n\n")
