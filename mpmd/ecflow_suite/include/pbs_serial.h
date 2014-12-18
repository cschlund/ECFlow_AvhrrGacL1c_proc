#!/usr/bin/env bash

#PBS -q ns
#PBS -N %TASK%
#PBS -l EC_threads_per_task=1
#PBS -l EC_total_tasks=1
#PBS -l EC_ecfs=1
#PBS -l EC_memory_per_task=1024MB

