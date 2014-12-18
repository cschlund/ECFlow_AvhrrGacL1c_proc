#!/usr/bin/env bash

. config.sh

for ext in sub mpmdsub pbs tsk 1 job1 log 
do
    find $REMOTE_HOME/generated -type f | grep "\.$ext" | xargs rm -f 
    find $REMOTE_LOGDIR* -type f | grep "\.$ext" | xargs rm -f 
done

