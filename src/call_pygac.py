#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: October, 2014
# C.Schlundt: February, 2015: add2sqlite after pygac added
#

import sys
import argparse
import subprocess
import glob
import quick_l1c_analysis as quick
from datetime import datetime, timedelta
from global_config import *
from housekeeping import create_dir, delete_dir
from housekeeping import def_pygac_cfg
from pycmsaf.avhrr_gac.database import AvhrrGacDatabase
from pycmsaf.argparser import str2date
from pycmsaf.logger import setup_root_logger

logger = setup_root_logger(name='root')

# -- parser arguments
parser = argparse.ArgumentParser(
    description=(u'{0:s}\n'
                 u'is responsible for executing the inter-calibration tool \'pygac\',\n'
                 u'which provides AVHRR GAC L1c data. You have to parse a satellite name\n'
                 u'along with a start and end date (i.e., matching tarfile date range).\n'
                 u'The produced (white-listed) L1c files are then read by '
                 u'\'add2sqlite_l1c_info.py\' in order to collect L1c information, which '
                 u'is necessary for executing \'GAC_overlap.py\'. '
                 u'Global paths and settings are defined in "global_config.py".\n'
                 u'The subroutines are defined in "housekeeping.py".\n').
    format(os.path.basename(__file__)))


parser.add_argument('-sat', '--satellite', required=True,
                    help='String, e.g. NOAA14')

parser.add_argument('-sd', '--start_date', type=str2date, required=True,
                    help='Date String, e.g. 20000101')

parser.add_argument('-ed', '--end_date', type=str2date, required=True,
                    help='Date String, e.g. 20000107')

args = parser.parse_args()

date_range = str(args.start_date) + "_" + str(args.end_date)


# -- make some screen output
logger.info("{0} started for {1} : {2} - {3}! \n".format(
    os.path.basename(__file__), args.satellite,
    args.start_date, args.end_date))


# -- make dirs
inp = create_dir("input", args.satellite,
                 str(args.start_date), str(args.end_date))

out = create_dir("output/pygac", args.satellite,
                 str(args.start_date), str(args.end_date))


# -- create pygac config file
cfgfile = os.path.join(out, "pygac_" + args.satellite +
                       "_" + date_range + ".cfg")
def_pygac_cfg(cfgfile, out)
os.putenv('PYGAC_CONFIG_FILE', cfgfile)


# -- retrieve tar records
db = AvhrrGacDatabase(dbfile=sql_gacdb_archive)

tarfiles = db.get_tarfiles(start_date=args.start_date,
                           end_date=args.end_date,
                           sats=[args.satellite],
                           include_blacklisted=False,
                           strict=False)

# -- loop tarfiles results
for tarfile in tarfiles:

    # -- collect failed L1b orbits
    failed_l1b_orbits = list()

    # -- get l1bfile records
    l1bfiles = db.get_l1bfiles(tarfile=tarfile, include_blacklisted=False,
                               start_date=args.start_date,
                               end_date=args.end_date)

    # -- some settings
    tarbase = os.path.basename(tarfile)
    tarplat = ((tarbase.split("."))[0].split("_"))[0]
    taryear = ((tarbase.split("."))[0].split("_"))[1]

    source = os.path.join(ecp_tar_download, tarbase)
    l1bcnt = len(l1bfiles)

    logger.info("TarFile : {0} ({1} orbits)\n".format(tarbase, l1bcnt))

    # -- loop over l1b files
    for i in range(len(l1bfiles)):

        logger.info("Working on {0}.L1b -> {1}".format(i, l1bfiles[i]))

        logger.info("get L1b from tarfile")

        # extract L1b file to "-C inp", different location
        c1 = ["tar", "xf", source, "-C", inp, l1bfiles[i]]
        p1 = subprocess.Popen(c1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p1.communicate()
        logger.info("STDOUT:{0}".format(stdout))
        logger.info("STDERR:{0}".format(stderr))

        logger.info("gunzip L1bfile")

        f2 = os.path.join(inp, l1bfiles[i])
        c2 = ["gunzip", f2]
        p2 = subprocess.Popen(c2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p2.communicate()
        logger.info("STDOUT:{0}".format(stdout))
        logger.info("STDERR:{0}".format(stderr))

        logger.info("call {0}".format(os.path.basename(pygac_runtool)))

        l1b_basen = os.path.splitext(l1bfiles[i])[0]
        l1b_input = os.path.join(inp, l1b_basen)
        c3 = ["python", pygac_runtool, l1b_input, "0", "0"]
        p3 = subprocess.Popen(c3, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p3.communicate()
        stdout_lines = stdout.split("\n")
        stderr_lines = stderr.split("\n")
        std_lines = stdout_lines + stderr_lines

        logger.info("PyGAC STDOUT")
        for line in stdout_lines:
            print line

        logger.info("PyGAC STDERR:")
        for line in stderr_lines:
            print line

        l1cfile = None
        l1cfile_fully_qualified = None
        pygac_took = None
        p_warnings = list()
        p_errors = list()

        logger.info("collect information from STDOUT & STDERR")
        for line in std_lines:
            if "warning" in line.lower():
                p_warnings.append(line)
            elif "error" in line.lower():
                p_errors.append(line)
            elif "Filename: "+pygac_prefix+"_avhrr" in line:
                line_list = line.split()
                l1cfile = filter(lambda x: '.h5' in x, line_list)[0]
                l1cfile_fully_qualified = os.path.join(out, l1cfile)
            elif "pygac took" in line.lower():
                ll = line.split()
                t = datetime.strptime(ll[-1], "%H:%M:%S.%f")
                pygac_took = timedelta(hours=t.hour, minutes=t.minute, seconds=t.second,
                                       microseconds=t.microsecond).total_seconds()
            else:
                continue

        logger.info("L1c File: {0}".format(l1cfile_fully_qualified))
        logger.info("Errors  : {0}".format(p_errors))
        logger.info("Warnings: {0}".format(p_warnings))
        logger.info("RunTime : {0}".format(pygac_took))

        logger.info("Collect records for quick L1c analysis\n")
        quick.collect_records(l1b_file=l1bfiles[i], 
                              l1c_file=l1cfile_fully_qualified, 
                              sql_file=sql_pygac_logout, 
                              pygac_version=pygac_commit, 
                              pygac_took=pygac_took, 
                              pygac_errors=p_errors, 
                              pygac_warnings=p_warnings)

        if l1cfile is None:
            failed_l1b_orbits.append(l1bfiles[i])
            continue

        logger.info("call {0}".format(os.path.basename(add2sql_runtool)))

        c4 = ["python", add2sql_runtool, "--l1b_file={0}".format(l1bfiles[i]),
              "--l1c_file={0}".format(l1cfile), "--l1c_path={0}".format(out),
              "--db_file={0}".format(sql_gacdb_archive), 
              "--tmp_dir={0}".format(relict_dir), "--verbose"]
        p4 = subprocess.Popen(c4, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p4.communicate()
        logger.info("add2sqlite_l1c_info STDOUT:{0}".format(stdout))
        logger.info("add2sqlite_l1c_info STDERR:{0}".format(stderr))

        # -- end of loop over l1bfiles

    # -- check if output is equal input
    output1 = os.path.join(out, "*avhrr*h5")
    output2 = os.path.join(out, "*sunsatangles*h5")
    output3 = os.path.join(out, "*qualflags*h5")

    avhrr_cnt = len(glob.glob(output1))
    sunsat_cnt = len(glob.glob(output2))
    flags_cnt = len(glob.glob(output3))

    if avhrr_cnt != l1bcnt and sunsat_cnt != l1bcnt and flags_cnt != l1bcnt:
        logger.info("PYGAC FAILED {0} time(s):".format(len(failed_l1b_orbits)))
        for failed in failed_l1b_orbits:
            logger.info("{0}".format(failed))
    else:
        # -- delete dirs: where L1b files are extracted
        delete_dir(inp)

    logger.info("TarFile {0} finished: {1} L1b -> {2} L1c\n".
                format(tarbase, l1bcnt, avhrr_cnt))

    # -- end of loop over tarfiles

logger.info("{0} finished!".format(os.path.basename(__file__)))
