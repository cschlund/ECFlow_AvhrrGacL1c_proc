#!/usr/bin/env bash

source config.sh

while [ 1 ]
do
    mpmd_submit.py --dbfile=$MPMD_DATABASE \
                   --mode=$MPMD_MODE \
                   --suite_name=$SUITE \
                   --submit_cmd=$MPMD_SUBMIT_CMD \
                   --remote_user=$REMOTE_USER \
                   --remote_host=$REMOTE_HOST
    sleep $@
done
