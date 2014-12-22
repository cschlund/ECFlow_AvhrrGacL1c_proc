#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: November, 2014
#

import os, sys, fnmatch
import argparse
import tarfile
from datetime import date
from dateutil.rrule import rrule, DAILY
from global_config import *
from housekeeping import move_files ,delete_file
from housekeeping import create_dir, delete_dir
from pycmsaf.avhrr_gac.database import AvhrrGacDatabase
from pycmsaf.argparser import str2date
from pycmsaf.utilities import date_from_year_doy


# -- parser arguments
parser = argparse.ArgumentParser(description='''%s
creates tar files per day and per satellite. 
Global paths and settings are defined in "global_config.py". 
The subroutines are defined in "housekeeping.py".
''' % (os.path.basename(__file__)))

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


# -- define input
inp = os.path.join( datadir, "output/pygac", args.satellite, 
        str(args.start_date)+"_"+str(args.end_date) )


# -- define temp. subfolder for tar creation
#    cron job will upload tarfiles!
make_tar_tmp_dir = create_dir( "tmp_make_tarfile", 
    args.satellite, str(args.start_date), str(args.end_date) )


# -- get all files in one list of inp directory
files_list = []
pattern = 'ECC_GAC_*.h5'
for root, dirs, files in os.walk(inp):
    for filename in fnmatch.filter(files, pattern):
        files_list.append(os.path.join(root, filename))

files_list.sort()


# -- loop over date range
for dt in rrule( DAILY, dtstart=args.start_date, until=args.end_date):

    # -- some settings
    date_split     = str(dt.date()).split("-")
    date_string    = str(dt.strftime("%Y%m%d"))
    date_pattern   = 'ECC_GAC_*_%sT*.h5' % date_string
    date_file_list = [] #file list for one day
    date_tar_list  = [] #file list for tarfile
    
    tar_base    = tar_file_prefix+args.satellite+"_"+\
                  date_string+tar_file_suffix
    tar_file    = os.path.join(make_tar_tmp_dir, tar_base)
    ecfs_target = os.path.join(ecfs_l1c_dir, 
                               date_split[0], date_split[1])


    # -- get file list for one day
    for root, dirs, files in os.walk(inp):
        for filename in fnmatch.filter(files, date_pattern):
            date_file_list.append(os.path.join(root, filename))
    
    date_file_list.sort()


    # -- delete file from files_list if this file will be tared
    #    this should prevent that the last orbit is tared twice!
    #    i.e. last orbit crosses dateline!
    for file in date_file_list:
        if file in files_list:
            idx = files_list.index(file)
            fff = files_list.pop(idx)
            date_tar_list.append(fff)


    # -- create tarfile
    if date_tar_list:
        print (" * create %s " % tar_file)
        tar = tarfile.open(tar_file, "w:bz2")
        for tfile in date_tar_list:
            filedir = os.path.dirname(tfile)
            filenam = os.path.basename(tfile)
            tar.add(tfile, arcname=filenam)
        tar.close()
    else:
        print (" * No L1c files for %s" % date_string)

# -- end of loop over date range


# -- all files zipped?
if len(files_list) > 0:
    files_left_over = []
    print (" * These L1c files are left over:")
    for i in files_list:
        print ("   - %s" % i)
        files_left_over.append(i)

    if not os.path.exists( relict_dir ):
        os.makedirs( relict_dir )

    move_files( files_left_over, relict_dir )


# -- get list of tar files in tmp dir
tar_files_list = []
tar_pattern = tar_file_prefix+'*'+tar_file_suffix
for root, dirs, files in os.walk( make_tar_tmp_dir ):
    for filename in fnmatch.filter(files, tar_pattern):
        tar_files_list.append(os.path.join(root, filename))

# -- sort list
tar_files_list.sort()


# -- create ecp_tar_upload directory
if not os.path.exists( ecp_tar_upload  ): 
    os.makedirs( ecp_tar_upload )


# -- move all tarfiles to final subfolder
move_files( tar_files_list, ecp_tar_upload )


# -- delete tar tmp directory
delete_dir( make_tar_tmp_dir )


# -- delete pygac results
delete_dir( inp )


# -- delete l1b main input tarfile
db = AvhrrGacDatabase( dbfile=sql_gacdb_archive )
results = db.get( start_date=args.start_date, 
                  end_date=args.end_date, 
                  sats=[args.satellite],
                  include_blacklisted=False, nol1b=True)
db.close()

for res in results:
    base = os.path.basename(res)
    file = os.path.join(ecp_tar_download, base)

    # only delete l1b tarfile if start and end dates are matching
    tardoys  = ((base.split("."))[0].split("_"))[2].split("x")
    taryear  = (base.split("."))[0].split("_")[1]
    tarsdate = date_from_year_doy(int(taryear), int(tardoys[0]))
    taredate = date_from_year_doy(int(taryear), int(tardoys[1]))

    if args.start_date == tarsdate and args.end_date == taredate: 
        print ( " * delete %s " % file )
        delete_file( file )
    else:
        print ( " * cannot delete %s due to date mismatch" % file )


print ( " * %s finished !" % os.path.basename(__file__) )

