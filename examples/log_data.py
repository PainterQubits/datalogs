"""Example of saving data using DataLogger."""

from paramdb import ParamDB
from datalogger import DataLogger

param_db = ParamDB[int](":memory:")
data_logger = DataLogger(param_db, "data_logs")

param_db.commit("Commit 1", 101)
param_db.commit("Commit 2", 102)
param_db.commit("Commit 3", 103)
param_db.commit("Commit 4", 104)
param_db.commit("Commit 5", 105)

data_logger.log(graph="cross_entropy", node="rabi_calibration")
