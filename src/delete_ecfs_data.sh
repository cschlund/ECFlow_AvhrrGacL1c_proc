#!/usr/bin/env bash

year=$1
ecfs=ec:/sf7/data/AVHRR_GAC_L1c_archive
backup=ec:/sf7/backup

if [ $year ]; then 
    #els -l $ecfs/$year
    del=$(els $ecfs/$year/)
    #for i in $del; do els -l $ecfs/$year/$i*.*; done
    echo "*** (1) remove tarfiles first ***"
    for i in $del; do erm $ecfs/$year/$i*.*; done
    #for i in $del; do els -l $ecfs/$year/$i*.*; erm $ecfs/$year/$i*.*; done
    echo "*** (2) now remove month subfolders ***"
    ermdir $ecfs/$year/*
    echo "*** (3) last but not least remove year subfolder ***"
    ermdir $ecfs/$year
    echo "*** :-) FINISHED with $1 ***"
else 
    echo
    els -l $ecfs/
    echo
    echo "*** Give me a year <yyyy> ***"
    echo
fi
