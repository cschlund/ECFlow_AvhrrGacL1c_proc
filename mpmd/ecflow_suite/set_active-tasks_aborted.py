#!/usr/bin/env python2.7

# NOTE: before executing this script, you have to: 
#   source ../config.sh 
#   for having the right ECF_NODE and ECF_PORT

import ecflow

client = ecflow.Client()
client.sync_local()
defs = client.get_defs()
tasks = defs.get_all_tasks()

for task in tasks:
    if task.get_state() == ecflow.DState.active:
        client.force_state(task.get_abs_node_path(), ecflow.State.aborted)
