#!/usr/bin/env bash

for ext in sub mpmdsub pbs tsk 1 job1 log 
do
    find generated -type f | grep "\.$ext" | xargs rm -f 
    find mpmd* -type f | grep "\.$ext" | xargs rm -f 
done

