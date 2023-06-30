"""Example of saving data using DataLogger."""

from paramdb import ParamDB
from datalogger import DataLogger

param_db = ParamDB[int]("qpu.db")
data_logger = DataLogger(param_db, "data_logs")

param_db.commit("Commit 1", 101)
param_db.commit("Commit 2", 102)
param_db.commit("Commit 3", 103)
param_db.commit("Commit 4", 104)
param_db.commit("Commit 5", 105)

for i in range(5):
    graph_data_logger = data_logger.graph_logger("cross_entropy")
    for j in range(5):
        node_data_logger = graph_data_logger.node_logger("rabi_calibration")
        param_db.commit("Commit", 10 * i + j)
        node_data_logger.log("rabi")
        node_data_logger.log("rabi_computed", analysis=True)
