#!/usr/bin/env python2.7

import shutil
from global_config import *


# move files to another directory 
def move_files(list_of_files, destination):
    for fil in list_of_files:
        os.system("mv" + " " + fil + " " + destination)


# get_temp_dir("input", "NOAA14", "20000101", "20000107")
def create_dir(where, satellite, start_date, end_date):
    tmpdir = os.path.join(datadir, where, satellite,
                          start_date + '_' + end_date)

    if not os.path.exists(tmpdir):
        os.makedirs(tmpdir)

    return tmpdir


# os.remove() will remove a file.
# os.rmdir() will remove an empty directory.
# shutil.rmtree() will delete a directory and all its contents.
def delete_dir(tmpdir):
    if os.path.exists(tmpdir):
        shutil.rmtree(tmpdir)


# def delete_file(/path/to/file.dat)
def delete_file(fil):
    if os.path.exists(fil):
        os.remove(fil)


# def_pygac_cfg("/path/to/pygac.cfg", "/path/to/h5out")
def def_pygac_cfg(fil, h5outdir, logger):
    try:
        f = open(fil, mode="w")
        f.write("[tle]\n")
        f.write("tledir = " + pygac_tle_dir + "\n")
        f.write("tlename = " + pygac_tle_txt + "\n")
        f.write("\n")
        f.write("[output]\n")
        f.write("output_dir = " + h5outdir + "\n")
        f.write("output_file_prefix = " + pygac_prefix + "\n")
        f.close()
    except Exception as e:
        logger.info("FAILED: {0}".format(e))