#!/usr/bin/env bash

export PATH=/usr/local/bin:$PATH
. ~/.bashrc
. ~/.profile

# set checkpoint interval
export ECF_CHECKINTERVAL=30

# start ecflow server
ecflow_start.sh -p 35818 -d /home/ms/de/sf7/ecflow_logs_cschlund
