"""Example of saving all properties of an object."""

import os
from paramdb import ParamDB
from mock_node import PowerRabiNode
from datalogger import RootLogger, load_log

param_db = ParamDB[int]("qpu.db")
data_logger = RootLogger(param_db, "data_logs")

node = PowerRabiNode(0, 1.1, 0.02, name="q1_powerRabi")

data_logger.graph_logger("graph").node_logger("node").log_props("node", node)

root_dir = data_logger.directory
graph_dir = os.path.join(root_dir, os.listdir(root_dir)[0])
node_dir = os.path.join(graph_dir, os.listdir(graph_dir)[0])

for log_path in os.listdir(node_dir):
    log = load_log(os.path.join(node_dir, log_path))
    print(log, end="\n\n")
