#!/usr/bin/env bash

host=`hostname`
if [[ $host == cc* ]] || [[ $host == nid* ]]; then
    module load ecflow/4.0.6
fi

ECF_NAME=%ECF_NAME%
ECF_NODE=%ECF_NODE%
ECF_PASS=%ECF_PASS%
ECF_PORT=%ECF_PORT%
ECF_TRYNO=%ECF_TRYNO%
ECF_RID=$$
export ECF_NAME ECF_NODE ECF_PASS ECF_TRYNO ECF_PORT ECF_RID

ERROR() { echo ERROR ; ecflow_client --abort=trap; exit 1 ; }
trap ERROR 0

trap '{ echo "Killed by a signal"; ERROR ; }' 1 2 3 4 5 6 7 8 10 12 13 15
set -e
ecflow_client --init=$$
