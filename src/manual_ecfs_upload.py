#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: November, 2016
#

import sys
import fnmatch
import argparse
import subprocess
import tarfile
from global_config import *
from housekeeping import move_files
from pycmsaf.logger import setup_root_logger

logger = setup_root_logger(name='root')


# -- parser arguments
parser = argparse.ArgumentParser(
    description='''{0} uploads ready AVHRR GAC L1c data on demand.
    Global paths and settings are defined in "global_config.py".
    The subroutines are defined in
    "housekeeping.py". '''.format(os.path.basename(__file__)))

parser.add_argument('-i', '--inpdir', required=True, type=str,
                    help='String, e.g. /path/to/files*{0}'.
                    format(tar_file_suffix))

parser.add_argument('-s', '--satellite', required=True, type=str,
                    help='Satellite string name, e.g. NOAA14')

parser.add_argument('-y', '--year', required=True, type=int,
                    help='Year as integer, e.g. 2001')

parser.add_argument('-m', '--month', required=True, type=int,
                    help='Month as integer, e.g. 1')

args = parser.parse_args()


# -- make some screen output
logger.info("{0} look for tar files here: {1}".
            format(os.path.basename(__file__), args.inpdir))


# -- create ecp_tar_upload directory if not existing
if not os.path.exists(ecp_tar_upload):
    os.makedirs(ecp_tar_upload)

# -- create ecp_tar_upload/manually directory if not existing
manually = os.path.join(ecp_tar_upload, "manually")
if not os.path.exists(manually):
    os.makedirs(manually)

# -- get list of tar files in tmp dir, AVHRR_GAC_L1C_NOAA14_20010102.tar.bz2
tar_files_list = list()
tar_pattern = (tar_file_prefix + args.satellite + '_' +
               str(args.year) + str(args.month).zfill(2) +
               '*' + tar_file_suffix)
for root, dirs, files in os.walk(args.inpdir):
    for filename in fnmatch.filter(files, tar_pattern):
        tar_files_list.append(os.path.join(root, filename))

# -- sort list
tar_files_list.sort()

# -- make monthly tarball
if tar_files_list:

    # -- make monthly tarfilename
    mon_tarbase = (tar_file_prefix + args.satellite + '_' +
                   str(args.year) + str(args.month).zfill(2) +
                   tar_file_suffix2)
    mon_tarfile = os.path.join(manually, mon_tarbase)
    ecfs_target = os.path.join(ecfs_l1c_dir, str(args.year),
                               str(args.month).zfill(2))

    logger.info("manually -> make: {0}".format(mon_tarfile))

    # -- create final tarfile
    tar = tarfile.open(mon_tarfile, "w:")
    for tfile in tar_files_list:
        filedir = os.path.dirname(tfile)
        filenam = os.path.basename(tfile)
        tar.add(tfile, arcname=filenam)
    tar.close()

    # -- make dir in ECFS
    logger.info("emkdir -p {0}".format(ecfs_target))
    p1 = subprocess.Popen(["emkdir", "-p", ecfs_target],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    stdout, stderr = p1.communicate()
    logger.info("STDOUT:{0}".format(stdout))
    logger.info("STDERR:{0}".format(stderr))

    # -- copy file into ECFS dir
    logger.info("ecp -o {0} {1}".format(mon_tarfile, ecfs_target))
    p2 = subprocess.Popen(["ecp", "-o", mon_tarfile, ecfs_target],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    stdout, stderr = p2.communicate()
    logger.info("STDOUT:{0}".format(stdout))
    logger.info("STDERR:{0}".format(stderr))

    # -- change mode of mon_tarfile in ECFS
    logger.info("echmod 555 {0}/{1}".format(ecfs_target, mon_tarbase))
    p3 = subprocess.Popen(["echmod", "555", ecfs_target + "/" + mon_tarbase],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    stdout, stderr = p3.communicate()
    logger.info("STDOUT:{0}".format(stdout))
    logger.info("STDERR:{0}".format(stderr))

    # -- move tar_files_list on $SCRATCH
    logger.info("Move daily tarball-files to {0} ".format(manually))
    move_files(tar_files_list, manually)

else:
    logger.info("No tarfiles have been found!")
    logger.info("Check your arguments!")
    sys.exit(0)

logger.info("{0} finished!".format(os.path.basename(__file__)))