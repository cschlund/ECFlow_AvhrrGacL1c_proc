#!/usr/bin/env bash

source config.sh

mpmd_client.py --dbfile=$MPMD_DATABASE --create pass
