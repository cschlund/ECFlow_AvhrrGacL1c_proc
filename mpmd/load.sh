#!/usr/bin/env bash

source config.sh

# Delete the submitter's all time logfile
rm -f "$ECF_OUT/$SUITE/queue_submitter/submit.log.all"

ecflow_client --load=ecflow_suite/${SUITE}.def force
ecflow_client --begin=/${SUITE}
