#!/usr/bin/env bash

. config.sh

# Destination for generated ecflow jobfiles
#export ECF_HOME=$SCRATCH_BASE/generated
rm -rf $ECF_HOME/*

# Destination for ecflow logfiles
#export ECF_OUT=$SCRATCH_BASE/log
rm -rf $ECF_OUT/*

