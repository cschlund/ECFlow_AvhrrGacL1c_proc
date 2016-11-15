#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: November, 2016
# collects processing log files, sqlite databases and
# invalid AVHRR GAC L1c files and saves all to ECFS.
# Global paths and settings are defined in "global_config.py".
# The subroutines are defined in "housekeeping.py"
#
import fnmatch
import subprocess
from global_config import *
from shutil import make_archive, copy
from housekeeping import delete_dir
from pycmsaf.logger import setup_root_logger

logger = setup_root_logger(name='root')


def exe_sb(cmd):
    ret = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    print_stderr_stdout(ret=ret)


def print_stderr_stdout(ret):
    stdout, stderr = ret.communicate()
    if stdout:
        logger.info("STDOUT:{0}".format(stdout))
    if stderr:
        logger.info("STDERR:{0}".format(stderr))


def copy_to_ecfs_archive(ecfs_dir, ecfs_file):
    """
    Copy tarball to ECFS
    :return:
    """
    # -- make dir in ECFS
    logger.info("emkdir -p {0}".format(ecfs_dir))
    exe_sb(cmd=["emkdir", "-p", ecfs_dir])

    # -- copy file into ECFS dir
    logger.info("ecp -o {0} {1}".format(ecfs_file, ecfs_dir))
    exe_sb(cmd=["ecp", "-o", ecfs_file, ecfs_dir])

    # -- change mode of ecfs_file in ECFS
    ecfs_base = os.path.basename(ecfs_file)
    logger.info("echmod 555 {0}/{1}".format(ecfs_dir, ecfs_base))
    exe_sb(cmd=["echmod", "555", ecfs_dir + "/" + ecfs_base])


def make_temp_dir(temp_dir, temp_sub):
    new_dir = os.path.join(temp_dir, temp_sub)
    if not os.path.exists(new_dir):
        os.makedirs(new_dir)
    return new_dir


def get_file_list(pattern, path):
    result = []
    for root, dirs, files in os.walk(path):
        for name in files:
            if fnmatch.fnmatch(name, pattern):
                result.append(os.path.join(root, name))
    return result


def pygac_sat_list():
    """
    SATELLITE list: pygac nomenclature
    """
    sql_list = ['TIROSN', 'NOAA6',  'NOAA7',  'NOAA8',
                'NOAA9', 'NOAA10', 'NOAA11', 'NOAA12', 'NOAA14',
                'NOAA15', 'NOAA16', 'NOAA17', 'NOAA18', 'NOAA19',
                'METOPA', 'METOPB']
    pyg_list = [s.lower() for s in sql_list]
    return pyg_list


def collect_log_files(tmp_dir):
    """
    Collect and compress log files related to current processing.
    :param tmp_dir: tarballs will be written to this directory
    :return:
    """
    logger.info("Collect mpmd and task log-files")

    tsub = pygac_commit + "-log_files"
    tdir = make_temp_dir(temp_dir=tmp_dir, temp_sub=tsub)

    source = os.path.join(ecfbase, "mpmd/generated")
    exe_sb(cmd=["cp", "-r", source, tdir])

    source = os.path.join(datadir, "mpmd/log")
    exe_sb(cmd=["cp", "-r", source, tdir])

    tar_name = os.path.join(tmp_dir, tsub)
    tar_arch = make_archive(base_name=tar_name, format='gztar', root_dir=tmp_dir)
    delete_dir(tmpdir=tdir)

    edir = os.path.join(ecfs_l1c_dir, "proc_history")
    copy_to_ecfs_archive(ecfs_dir=edir, ecfs_file=tar_arch)

    logger.info("DONE {0}".format(os.path.basename(tar_arch)))


def collect_sql_files(tmp_dir):
    """
    Collect and compress SQLite databases related to current processing.
    :param tmp_dir: tarball will be written to this directory
    :return:
    """
    logger.info("Collect sqlite files")

    tsub = pygac_commit + "-sql_files"
    tdir = make_temp_dir(temp_dir=tmp_dir, temp_sub=tsub)

    copy(src=sql_gacdb_archive, dst=tdir)
    copy(src=sql_pystat_output, dst=tdir)
    copy(src=sql_pygac_logout, dst=tdir)

    tar_name = os.path.join(tmp_dir, tsub)
    tar_arch = make_archive(base_name=tar_name, format='gztar', root_dir=tmp_dir)
    delete_dir(tmpdir=tdir)

    edir = os.path.join(ecfs_l1c_dir, "proc_history")
    copy_to_ecfs_archive(ecfs_dir=edir, ecfs_file=tar_arch)

    logger.info("DONE {0}".format(os.path.basename(tar_arch)))


def collect_invalid_orbits(tmp_dir):
    """
    Collect invalid AVHRR GAC L1c orbits and compress files per satellite.
    :param tmp_dir: tarballs will be written to this directory
    :return:
    """
    logger.info("Collect invalid L1c orbits")

    sats = pygac_sat_list()
    for s in sats:
        pattern = "ECC_GAC*" + s + "*"
        files = get_file_list(pattern=pattern, path=relict_dir)

        if files:
            tsub = pygac_commit + "-invalid_l1c_orbits_" + s
            tdir = make_temp_dir(temp_dir=tmp_dir, temp_sub=tsub)

            for f in files:
                copy(src=f, dst=tdir)

            tar_name = os.path.join(tmp_dir, tsub)
            tar_arch = make_archive(base_name=tar_name, format='gztar', root_dir=tmp_dir)
            delete_dir(tmpdir=tdir)

            edir = os.path.join(ecfs_l1c_dir, "proc_history")
            copy_to_ecfs_archive(ecfs_dir=edir, ecfs_file=tar_arch)

            logger.info("DONE {0}".format(os.path.basename(tar_arch)))


if __name__ == '__main__':

    logger.info("{0} started!".format(os.path.basename(__file__)))

    work_dir = make_temp_dir(temp_dir=datadir, temp_sub=pygac_commit)

    logger.info("Work Dir: {0}".format(work_dir))
    if datadir:
        collect_log_files(tmp_dir=work_dir)

    if sqlite_dir:
        collect_sql_files(tmp_dir=work_dir)

    if relict_dir:
        collect_invalid_orbits(tmp_dir=work_dir)

    logger.info("{0} finished!".format(os.path.basename(__file__)))