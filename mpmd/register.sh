#!/usr/bin/env bash

source config.sh

# register suite
mpmd_client.py --dbfile=$MPMD_DATABASE \
   register_suite --name=$SUITE \
   --job_template=$JOB_TEMPLATE \
   --mpmd_jobdir=$MPMD_JOBDIR \
   --mpmd_submit_logdir=$MPMD_SUBMIT_LOGDIR \
   --remote_mpmd_jobdir=$REMOTE_MPMD_JOBDIR \
   --ecf_host=$ECF_NODE --ecf_port=$ECF_PORT \
   --ecf_home=$ECF_HOME --remote_home=$REMOTE_HOME


# register pygac queue
mpmd_client.py --dbfile=$MPMD_DATABASE \
               register_queue --name=pygac \
               --length=$LENGTH --memory=1024 \
               --threads_per_task=1 \
               --walltime=24:00:00 --suite=$SUITE \
               --pbs_queue=np

# register pystat queue
mpmd_client.py --dbfile=$MPMD_DATABASE \
               register_queue --name=pystat \
               --length=$LENGTH --memory=3000 \
               --threads_per_task=48 \
               --walltime=24:00:00 --suite=$SUITE \
               --pbs_queue=np

# register archiving queue (uses ECFS)
mpmd_client.py --dbfile=$MPMD_DATABASE \
               register_queue --name=maketarfile \
               --length=$LENGTH --memory=1024 \
               --threads_per_task=1 \
               --walltime=12:00:00 --suite=$SUITE \
               --ecfs --pbs_queue=np

