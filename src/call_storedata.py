#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: November, 2014
#

import sys
import fnmatch
import argparse
import subprocess
import tarfile

from pycmsaf.avhrr_gac.database import AvhrrGacDatabase
from global_config import *
from housekeeping import delete_file


# -- parser arguments
parser = argparse.ArgumentParser(
    description='''{0} looks for ready {1:s}<sat>_<yyyymmdd>{2}
    files to be uploaded into ECFS. However, only if all days of the
    month were processed successfully, a monthly {3}<sat>_<yyyymm>{4}
    is written into ECFS containing all daily zipped files.
    Global paths and settings are defined in "global_config.py".
    The subroutines are defined in
    "housekeeping.py". '''.format(os.path.basename(__file__),
                                  tar_file_prefix, tar_file_suffix,
                                  tar_file_prefix, tar_file_suffix2))

parser.add_argument('-i', '--inpdir', required=True,
                    help='String, e.g. /path/to/files*{0}'.
                    format(tar_file_suffix))

args = parser.parse_args()


# -- make some screen output
print (" * {0} look for tar files here: {1}".format(os.path.basename(__file__),
                                                    args.inpdir))


# -- create ecp_tar_upload directory if not existing
if not os.path.exists(ecp_tar_upload):
    os.makedirs(ecp_tar_upload)


# -- get list of tar files in tmp dir
tar_files_list = list()
tar_pattern = tar_file_prefix + '*' + tar_file_suffix
for root, dirs, files in os.walk(args.inpdir):
    for filename in fnmatch.filter(files, tar_pattern):
        tar_files_list.append(os.path.join(root, filename))

# -- sort list
tar_files_list.sort()


# -- triples list: sat, year, month
triples = list()

if tar_files_list:

    # -- loop over file list
    for tar_file in tar_files_list:

        filename_base = os.path.basename(tar_file).split(".")
        filename_split = filename_base[0].split("_")
        filename_sat = filename_split[3]
        filename_year = filename_split[-1][0:4]
        filename_month = filename_split[-1][4:6]
        filename_day = filename_split[-1][6:8]

        d = dict(sat=filename_sat, year=int(filename_year),
                 month=int(filename_month))

        for item in triples:
            if item == d:
                break
        else:
            triples.append(d)

else:
    print " * There are currently no tarfiles!"
    sys.exit(0)


# -- loop over unique pairs and check if all days ready
for trip in triples:

    sat = trip["sat"]
    year = trip["year"]
    month = trip["month"]

    db = AvhrrGacDatabase(dbfile=sql_gacdb_archive)
    days = db.get_days(sat=sat, year=year, month=month)
    db.close()

    print (" * Check if complete for sat={0}, "
           "year={1}, month={2}".format(sat, year, month))

    check_list = list()
    tfile_list = list()

    for day in days:
        str_bas = (tar_file_prefix + sat + '_' + str(year) +
                   str(month).zfill(2) + str(day).zfill(2) +
                   tar_file_suffix)
        str_fil = os.path.join(args.inpdir, str_bas)

        tfile_list.append(str_fil)
        check_list.append(os.path.isfile(str_fil))

    if False in check_list:
        print "   - not yet complete "

    else:
        # -- make monthly tarfilename
        mon_tarbase = (tar_file_prefix + sat + '_' + str(year) +
                       str(month).zfill(2) + tar_file_suffix2)
        mon_tarfile = os.path.join(ecp_tar_upload, mon_tarbase)
        ecfs_target = os.path.join(ecfs_l1c_dir, str(year),
                                   str(month).zfill(2))

        print "   - complete -> make: {0} ".format(mon_tarfile)

        # -- create final tarfile
        tar = tarfile.open(mon_tarfile, "w:")
        for tfile in tfile_list:
            filedir = os.path.dirname(tfile)
            filenam = os.path.basename(tfile)
            tar.add(tfile, arcname=filenam)
        tar.close()

        # -- make dir in ECFS
        print (" * emkdir -p %s" % ecfs_target)
        p1 = subprocess.Popen(
            ["emkdir", "-p", ecfs_target],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p1.communicate()
        print stdout
        print stderr

        # -- copy file into ECFS dir
        print " * ecp -o {0} {1}".format(mon_tarfile, ecfs_target)
        p2 = subprocess.Popen(
            ["ecp", "-o", mon_tarfile, ecfs_target],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p2.communicate()
        print stdout
        print stderr

        # -- change mode of mon_tarfile in ECFS
        print " * echmod 555 {0}/{1}".format(ecfs_target, mon_tarbase)
        p3 = subprocess.Popen(
            ["echmod", "555", ecfs_target + "/" + mon_tarbase],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p3.communicate()
        print stdout
        print stderr

        # -- delete mon_tarfile on $SCRATCH
        print " * delete {0} ".format(mon_tarfile)
        delete_file(mon_tarfile)

        # -- delete tfile_list on $SCRATCH
        print " * delete corresponding {0} files ".format(tar_file_suffix)
        for tfile in tfile_list:
            delete_file(tfile)

# -- END OF: loop over unique pairs

print u" * {0} finished !".format(os.path.basename(__file__))