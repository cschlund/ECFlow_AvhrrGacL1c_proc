#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: October, 2014
#

import argparse
import subprocess

from dateutil.rrule import rrule, DAILY

from global_config import *
from pycmsaf.argparser import str2date
from pycmsaf.logger import setup_root_logger

logger = setup_root_logger(name='root')

# -- parser arguments
parser = argparse.ArgumentParser(
    description=u'''{0:s} calculates statistics
    (daily zonal and global means) of AVHRR GAC L1c data obtained
    from pyGAC intercalibration tool. For the VIS channels,
    statistics is based on daytime observations only, i.e. SZA less than 80.
    For the IR channels day/twilight/night observations are considered.
    Statistics are stored in a sqlite db. Orbits are processed in parallel mode.
    You have to parse a satellite name along with a start and end date
    (i.e., matching tarfile date range). Global paths and settings are defined
    in "global_config.py". The subroutines are defined in
    "housekeeping.py". '''.format(os.path.basename(__file__)))

parser.add_argument('-sat', '--satellite',
                    help='String, e.g. NOAA14', required=True)

parser.add_argument('-sd', '--start_date', type=str2date,
                    help='Date String, e.g. 20000101', required=True)

parser.add_argument('-ed', '--end_date', type=str2date,
                    help='Date String, e.g. 20000107', required=True)

args = parser.parse_args()

date_range = str(args.start_date) + "_" + str(args.end_date)


# -- make some screen output
logger.info("{0} started for {1} : {2} - {3}! ".
            format(os.path.basename(__file__), args.satellite,
                   args.start_date, args.end_date))


# -- define input for pystat
inp = os.path.join(datadir, "output/pygac", args.satellite, date_range)


# -- loop over date range
for dt in rrule(DAILY, dtstart=args.start_date, until=args.end_date):

    dstr = str(dt.strftime("%Y-%m-%d"))

    logger.info("call {0} for {1}".
                format(os.path.basename(pystat_runtool), dstr))

    pcmd = ["python", pystat_runtool,
            "--date={0}".format(dstr),
            "--satellite={0}".format(args.satellite),
            "--inpdir={0}".format(inp),
            "--gsqlite={0}".format(sql_pystat_output),
            "--verbose"]

    proc = subprocess.Popen(pcmd, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    stdout, stderr = proc.communicate()
    logger.info("STDOUT:{0}".format(stdout))
    logger.info("STDERR:{0}".format(stderr))


logger.info("{0} finished! ".format(os.path.basename(__file__)))
logger.info("Statistics added to {0}".format(sql_pystat_output))