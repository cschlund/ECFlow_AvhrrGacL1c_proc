#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: October, 2014
#

import os, sys
import argparse
import subprocess
from datetime import date
from dateutil.rrule import rrule, DAILY
from global_config import *
from pycmsaf.argparser import str2date


# -- parser arguments
parser = argparse.ArgumentParser(description='''%s
reads pyGAC L1c output h5 orbit files and adds to L1b sqlite
database, valuable L1c information for each orbit, 
which has been processed by pyGAC (white-listed L1b). 
Thus, this script adds the start and end time of measurement, 
i.e. timestamp of first and last scanline, as well as the along
and across track dimension. This L1c information will be later 
used for calculating the number of AVHRR GAC overlapping scanlines 
of two consecutive orbits. Additionally information about 
missing scanlines is also stored in this database.
Global paths and settings are defined in "global_config.py". 
The subroutines are defined in "housekeeping.py".
''' % os.path.basename(__file__))

parser.add_argument('-sat', '--satellite', 
        help='String, e.g. NOAA14', required=True)
parser.add_argument('-sd', '--start_date', type=str2date, 
        help='Date String, e.g. 20000101', required=True)
parser.add_argument('-ed', '--end_date', type=str2date, 
        help='Date String, e.g. 20000107', required=True)

args = parser.parse_args()

date_range = str(args.start_date)+"_"+str(args.end_date)


# -- make some screen output
print ( " * %s started for %s : %s - %s! " 
         %( os.path.basename(__file__), 
            args.satellite, args.start_date, args.end_date ) )


# -- define input for add2sqlite
inp = os.path.join( datadir, "output/pygac", args.satellite, 
        str(args.start_date)+"_"+str(args.end_date) )


# -- loop over date range
for dt in rrule( DAILY, dtstart=args.start_date, until=args.end_date):
    dstr = str(dt.strftime("%Y-%m-%d"))

    # -- call pystat: 
    pcmd = ["python", add2sql_runtool, "--date="+dstr, 
            "--satellite="+args.satellite, "--inpdir="+inp, 
            "--sqlite="+sql_gacdb_archive] 
    proc = subprocess.Popen( pcmd, stdout=subprocess.PIPE, 
                             stderr=subprocess.PIPE )
    stdout, stderr = proc.communicate()
    print stdout
    if proc.returncode > 0:
        print stderr


print ( " * %s finished ! " % os.path.basename(__file__) )
print ( " * L1c information added to %s" % sql_gacdb_archive )

