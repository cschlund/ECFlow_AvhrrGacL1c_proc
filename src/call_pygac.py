#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: October, 2014
# C.Schlundt: February, 2015: add2sqlite after pygac added
#

import argparse
import subprocess
import glob
from global_config import *
from housekeeping import create_dir, delete_dir
from housekeeping import def_pygac_cfg
from pycmsaf.avhrr_gac.database import AvhrrGacDatabase
from pycmsaf.argparser import str2date

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
print (" * {0} started for {1} : {2} - {3}! \n".
       format(os.path.basename(__file__), args.satellite,
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
                           include_blacklisted=False)


# -- loop tarfiles results
for tarfile in tarfiles:

    # -- collect failed L1b orbits
    failed_l1b_orbits = list()

    # -- get l1bfile records
    l1bfiles = db.get_l1bfiles(tarfile=tarfile, include_blacklisted=False)

    # -- some settings
    tarbase = os.path.basename(tarfile)
    taryear = tarbase[4:-12]
    tarplat = tarbase[:-17]

    source = os.path.join(ecp_tar_download, tarbase)
    l1bcnt = len(l1bfiles)

    print "   +++ TarFile : {0} ({1} orbits)\n".format(tarbase, l1bcnt)

    # -- loop over l1b files
    for i in range(len(l1bfiles)):

        print "   Working on {0}.L1b -> {1}".format(i, l1bfiles[i])
        l1cfile = None

        print "   + get L1b from tarfile"

        f1 = tarplat + "_" + taryear + "/" + l1bfiles[i]
        c1 = ["tar", "xf", source, "-C", inp, f1, "--strip=1"]
        p1 = subprocess.Popen(c1, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p1.communicate()
        print stdout
        print stderr

        print "   + gunzip L1bfile"

        f2 = os.path.join(inp, l1bfiles[i])
        c2 = ["gunzip", f2]
        p2 = subprocess.Popen(c2, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p2.communicate()
        print stdout
        print stderr

        print "   + call {0}".format(os.path.basename(pygac_runtool))

        l1b_basen = os.path.splitext(l1bfiles[i])[0]
        l1b_input = os.path.join(inp, l1b_basen)
        c3 = ["python", pygac_runtool, l1b_input, "0", "0"]
        p3 = subprocess.Popen(c3, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p3.communicate()
        stderr_lines = stderr.split("\n")

        print "     STDOUT ", stdout.strip()
        print "     STDERR "
        for line in stderr_lines:
            print "     ", line

        print "   + get corresponding L1c Filename"

        for line in stderr_lines:
            if "Filename" in line and "avhrr" in line:
                line_list = line.split()
                l1cfile = filter(lambda x: '.h5' in x, line_list)[0]
                if l1cfile:
                    break

        print "     L1c File: {0}\n".format(l1cfile)

        if l1cfile is None:
            failed_l1b_orbits.append(l1bfiles[i])
            continue

        print "   + call {0}".format(os.path.basename(add2sql_runtool))

        c4 = ["python", add2sql_runtool, "--l1b_file={0}".format(l1bfiles[i]),
              "--l1c_file={0}".format(l1cfile), "--l1c_path={0}".format(out),
              "--db_file={0}".format(sql_gacdb_archive), "--verbose"]
        p4 = subprocess.Popen(c4, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        stdout, stderr = p4.communicate()
        print stdout
        print stderr

        # -- end of loop over l1bfiles

    # -- check if output is equal input
    output1 = os.path.join(out, "*avhrr*h5")
    output2 = os.path.join(out, "*sunsatangles*h5")
    output3 = os.path.join(out, "*qualflags*h5")

    avhrr_cnt = len(glob.glob(output1))
    sunsat_cnt = len(glob.glob(output2))
    flags_cnt = len(glob.glob(output3))

    if avhrr_cnt != l1bcnt and sunsat_cnt != l1bcnt and flags_cnt != l1bcnt:
        print "   --- PYGAC FAILED {0} time(s):".format(len(failed_l1b_orbits))
        for failed in failed_l1b_orbits:
            print "       {0}".format(failed)
    else:
        # -- delete dirs: where L1b files are extracted
        delete_dir(inp)

    print "\n   +++ TarFile {0} finished: {1} L1b -> {2} L1c\n".\
        format(tarbase, l1bcnt, avhrr_cnt)

    # -- end of loop over tarfiles

print " * {0} finished \n".format(os.path.basename(__file__))