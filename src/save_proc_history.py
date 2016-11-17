#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# C.Schlundt: November, 2016
# collects processing log files, sqlite databases and
# invalid AVHRR GAC L1c files and saves all to ECFS.
# Global paths and settings are defined in "global_config.py".
# The subroutines are defined in "housekeeping.py"
#
import sys
import argparse
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
    cmd = ["emkdir", "-p", ecfs_dir]
    logger.info("{cmd}".format(cmd=cmd))
    exe_sb(cmd=cmd)

    cmd = ["ecp", "-o", ecfs_file, ecfs_dir]
    logger.info("{cmd}".format(cmd=cmd))
    exe_sb(cmd=cmd)

    ecfs_base = os.path.basename(ecfs_file)
    cmd = ["echmod", "555", ecfs_dir + "/" + ecfs_base]
    logger.info("{cmd}".format(cmd=cmd))
    exe_sb(cmd=cmd)


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


def collect_log_files(tmp_dir, tar_dir, test=None):
    """
    Collect and compress log files related to current processing.
    :param tmp_dir: copy files for tarball creation to this directory
    :param tar_dir: tarball written to this directory
    :return:
    """
    logger.info("Collect mpmd and task log-files")

    tsub = pygac_commit + "-log_files"
    tdir = make_temp_dir(temp_dir=tmp_dir, temp_sub=tsub)

    source = os.path.join(ecfbase, "mpmd/generated")
    cmd = ["cp", "-r", source, tdir]
    logger.info("{cmd}".format(cmd=cmd))
    exe_sb(cmd=cmd)

    source = os.path.join(datadir, "mpmd/log")
    cmd = ["cp", "-r", source, tdir]
    logger.info("{cmd}".format(cmd=cmd))
    exe_sb(cmd=cmd)

    tar_name = os.path.join(tar_dir, tsub)
    tar_arch = make_archive(base_name=tar_name, format='gztar', root_dir=tmp_dir)
    delete_dir(tmpdir=tdir)

    if not test:
        copy_to_ecfs_archive(ecfs_dir=proc_history, ecfs_file=tar_arch)

    logger.info("DONE {0}".format(os.path.basename(tar_arch)))


def collect_sql_files(tmp_dir, tar_dir, test=None):
    """
    Collect and compress SQLite databases related to current processing.
    :param tmp_dir: copy files for tarball creation to this directory
    :param tar_dir: tarball written to this directory
    :return:
    """
    logger.info("Collect sqlite files")

    tsub = pygac_commit + "-sql_files"
    tdir = make_temp_dir(temp_dir=tmp_dir, temp_sub=tsub)

    copy(src=sql_gacdb_archive, dst=tdir)
    copy(src=sql_pystat_output, dst=tdir)
    copy(src=sql_pygac_logout, dst=tdir)

    tar_name = os.path.join(tar_dir, tsub)
    tar_arch = make_archive(base_name=tar_name, format='gztar', root_dir=tmp_dir)
    delete_dir(tmpdir=tdir)

    if not test:
        copy_to_ecfs_archive(ecfs_dir=proc_history, ecfs_file=tar_arch)

    logger.info("DONE {0}".format(os.path.basename(tar_arch)))


def collect_invalid_orbits(tmp_dir, tar_dir, sy, ey, test=None):
    """
    Collect invalid AVHRR GAC L1c orbits and compress files per satellite.
    :param tmp_dir: copy files for tarball creation to this directory
    :param tar_dir: tarball written to this directory
    :param sy: start year
    :param ey: end year
    :return:
    """
    logger.info("Collect invalid L1c orbits")

    sats = pygac_sat_list()

    for s in sats:

        year = sy

        while year <= ey:
            pattern = "ECC_GAC_*" + s + "*_" + str(year) + "*.h5"
            files = get_file_list(pattern=pattern, path=relict_dir)

            if files:
                logger.info("Working on {sat} and {year}".format(sat=s, year=str(year)))

                files.sort()
                tsub = pygac_commit + "-invalid_l1c_orbits_" + s + "_" + str(year)
                tdir = make_temp_dir(temp_dir=tmp_dir, temp_sub=tsub)

                for f in files:
                    copy(src=f, dst=tdir)

                tar_name = os.path.join(tar_dir, tsub)
                tar_arch = make_archive(base_name=tar_name, format='gztar', root_dir=tmp_dir)
                delete_dir(tmpdir=tdir)

                if not test:
                    copy_to_ecfs_archive(ecfs_dir=proc_history, ecfs_file=tar_arch)

                logger.info("DONE {0}".format(os.path.basename(tar_arch)))
                year += 1

            else:
                year += 1
                continue


if __name__ == '__main__':

    # -- parser arguments
    parser = argparse.ArgumentParser(description='''{0}
    collects log files, sql files and invalid AVHRR GAC L1c orbits
    on demand making tarballs, which are saved to ECFS archive.
    Global paths and settings are defined in
    "global_config.py.'''.format(os.path.basename(__file__)))

    parser.add_argument('--logs', action="store_true",
                        help="Collect and save log files (perm, scratch).")

    parser.add_argument('--sqls', action="store_true",
                        help="Collect and save SQL databases.")

    parser.add_argument('--invalids', action="store_true",
                        help="Collect and save invalid AVHRR GAC "
                        "L1c orbits per satellite and per year.")

    parser.add_argument('--syear', type=int, default='1979',
                        help='Start Year, e.g. 2000')

    parser.add_argument('--eyear', type=int, default='2017',
                        help='End Year, e.g. 2006')

    parser.add_argument('--test', action="store_true",
                        help="Testing option, copy to ECFS disabled.")

    args = parser.parse_args()

    # Call function associated with the selected subcommand
    logger.info("{0} start for {1}".format(sys.argv[0], args))

    save_dir = make_temp_dir(temp_dir=datadir, temp_sub=pygac_commit)

    if args.logs:
        work_dir = make_temp_dir(temp_dir=datadir, temp_sub="save_logs")
        collect_log_files(tmp_dir=work_dir, tar_dir=save_dir, test=args.test)
        delete_dir(tmpdir=work_dir)

    if args.sqls:
        work_dir = make_temp_dir(temp_dir=datadir, temp_sub="save_sqls")
        collect_sql_files(tmp_dir=work_dir, tar_dir=save_dir, test=args.test)
        delete_dir(tmpdir=work_dir)

    if args.invalids:
        work_dir = make_temp_dir(temp_dir=datadir, temp_sub="save_invalids")
        collect_invalid_orbits(tmp_dir=work_dir, tar_dir=save_dir,
                                sy=args.syear, ey=args.eyear, test=args.test)
        delete_dir(tmpdir=work_dir)

    logger.info("{0} finished!".format(os.path.basename(__file__)))
