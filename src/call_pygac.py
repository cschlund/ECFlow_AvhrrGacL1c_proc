#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: October, 2014
#

import os, sys
import argparse
import subprocess
import glob
from global_config import *
from housekeeping import create_dir, delete_dir
from housekeeping import def_pygac_cfg
from pycmsaf.avhrr_gac.database import AvhrrGacDatabase
from pycmsaf.argparser import str2date


# -- parser arguments
parser = argparse.ArgumentParser(description='''%s
is responsible for executing the intercalibration tool "pygac",
which provides AVHRR GAC L1c data. You have to parse a satellite name 
along with a start and end date (i.e., matching tarfile date range). 
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


# -- make dirs
inp = create_dir( "input", args.satellite, 
        str(args.start_date), str(args.end_date) )
out = create_dir( "output/pygac", args.satellite, 
        str(args.start_date), str(args.end_date) )


# -- create pygac config file
cfgfile = os.path.join(out, "pygac_"+args.satellite+"_"+date_range+".cfg")
def_pygac_cfg( cfgfile, out )
os.putenv('PYGAC_CONFIG_FILE', cfgfile)


# -- retrieve tar records
db = AvhrrGacDatabase( dbfile=sql_gacdb_archive )
results = db.get( start_date=args.start_date, 
                  end_date=args.end_date, 
                  sats=[args.satellite],
                  include_blacklisted=False, nol1b=False)
db.close()


# -- loop over results
for tarfile, l1bfiles in results.iteritems():

    # -- some settings
    tarbase = os.path.basename(tarfile)
    taryear = tarbase[4:-12]
    tarplat = tarbase[:-17]

    source = os.path.join( ecp_tar_download, tarbase )
    l1bcnt = len(l1bfiles)

    print ( " * TarFile : %s (%s orbits)" % (tarbase, l1bcnt) )

    # -- loop over l1b files
    for i in range(len(l1bfiles)):

        print ( "   - Working on %3s.L1b -> %s" % 
                (i, l1bfiles[i]) )

        #if l1bfiles[i] != "NSS.GHRR.M2.D08045.S0646.E0829.B0685657.SV.gz":
        #    continue

        # -- get L1b from tarfile
        f1 = tarplat+"_"+taryear+"/"+l1bfiles[i]
        p1 = subprocess.Popen(["tar","xf",
                source,"-C",inp,f1,"--strip=1"], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p1.communicate()
        #print stdout
        if p1.returncode > 0:
            print stderr


        # -- gunzip file
        f2 = os.path.join(inp, l1bfiles[i])
        p2 = subprocess.Popen(["gunzip", f2], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p2.communicate()
        #print stdout
        if p2.returncode > 0:
            print stderr


        # -- call pygac
        l1b_basen = os.path.splitext(l1bfiles[i])[0]
        l1b_input = os.path.join( inp, l1b_basen )
        p3 = subprocess.Popen(["python", pygac_runtool, l1b_input, "0", "0"], 
                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = p3.communicate()
        print stdout
        if p3.returncode > 0:
            print stderr

# -- end of loop over results


# -- check if output is equal input
output1 = os.path.join( out, "*avhrr*h5" )
output2 = os.path.join( out, "*sunsatangles*h5" )
output3 = os.path.join( out, "*qualflags*h5" )
avhrr_cnt  = len( glob.glob( output1 ) )
sunsat_cnt = len( glob.glob( output2 ) )
flags_cnt  = len( glob.glob( output3 ) )

if avhrr_cnt != l1bcnt and sunsat_cnt != l1bcnt \
        and flags_cnt != l1bcnt:

    message = ( "! Something went wrong @pyGAC: "
                "output %s(%s, %s) NE %s input" 
                %(avhrr_cnt, sunsat_cnt, flags_cnt, l1bcnt) )
    #sys.exit(message)
    print message

else:

    # -- delete dirs: where L1b files are extracted
    delete_dir( inp )

    print ( " * %s finished -> produced %s *.h5 files " 
            %( os.path.basename(__file__), avhrr_cnt ) )

