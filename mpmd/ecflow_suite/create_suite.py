#!/usr/bin/env python2.7
from pycmsaf.logger import setup_root_logger
logger = setup_root_logger(name='root')

import os, sys
import subprocess
import ecflow
import argparse
import datetime
from config_suite import *
from pycmsaf.avhrr_gac.database import AvhrrGacDatabase
from pycmsaf.argparser import str2date
from pycmsaf.utilities import date_from_year_doy
from pycmsaf.ssh_client import SSHClient


# ----------------------------------------------------------------
def str2upper(string_object):
    return string_object.upper()

# ----------------------------------------------------------------
def set_vars(suite):
    """
    Set suite level variables
    """
    #suite.add_variable('TURTLES', 'I like turtles')
    suite.add_variable("ECF_MICRO", "%")

    # Location of the MPMD client:
    suite.add_variable("MPMD_CLIENT", mpmd_client_prog )
    
    # Specify the python interpreter to be used:
    suite.add_variable("PYTHON", \
            "PYTHONPATH=$PYTHONPATH:"+perm+" "+python_path)
    
    # Directory on the remote machine, where all generated 
    # files from "ECF_HOME" will be copied before execution
    suite.add_variable("REMOTE_HOME", remote_home_dir)
    
    # Directory on the remote machine, 
    # where all jobs write their output
    suite.add_variable("REMOTE_LOGDIR", remote_log_dir)

    # Remote user and host names
    suite.add_variable("REMOTE_USER", remote_user_name)
    suite.add_variable("REMOTE_HOST", remote_host_name)
    
    # Network settings for communication with MPMD database:
    suite.add_variable("MPMD_DATABASE", mpmd_database)
    suite.add_variable("MPMD_SUBMIT_SCRIPT", mpmd_submit_script)
    suite.add_variable("MPMD_MODE", mpmd_mode)
    suite.add_variable("MPMD_SUBMIT_CMD", mpmd_submit_cmd)
    
    # Standard ecflow variables:
    suite.add_variable("SUITE_HOME", suite_home_dir)
    suite.add_variable("ECF_HOME", ecf_home_dir)
    suite.add_variable("ECF_FILES", ecf_files_dir)
    suite.add_variable("ECF_INCLUDE", ecf_include_dir)
    suite.add_variable("ECF_OUT", ecf_out_dir)
    
    # Miscellaneous:
    suite.add_variable("ECF_TRIES", '1')
    suite.add_variable("ECF_SUBMIT", ecflow_submit)
    suite.add_variable("TAR_DOWNLOAD", cca_tar_download)
    suite.add_variable("TAR_UPLOAD", cca_tar_upload)
    suite.add_variable("CALL_PYGAC", cca_pygac)
    suite.add_variable("CALL_PYSTAT", cca_pystat)
    suite.add_variable("CALL_ADD2SQLITE", cca_add2sqlite)
    suite.add_variable("CALL_MAKETARFILE", cca_maketarfile)
    suite.add_variable("CALL_STOREDATA", cca_storedata)


# ----------------------------------------------------------------
def add_trigger(node, trigger):
    """
    Make a given node wait for the trigger node to complete.

    @param node: The node that has to wait.
    @param trigger: The trigger node.
    @type node: ecflow.[family/task]
    @type trigger: ecflow.[family/task]
    @return: None
    """

    node.add_trigger('{0} == complete'.
            format(trigger.get_abs_node_path()))


# ----------------------------------------------------------------
def add_mpmd_task(family, taskname):
    task = family.add_task(taskname)
    for event in ('mpmd_queued', 'mpmd_submitted', 'mpmd_error'):
        task.add_event(event)
    return task


# ----------------------------------------------------------------
def add_family_variables(family, first_day, last_day): 
    family.add_variable("START_DATE", first_day)
    family.add_variable("END_DATE", last_day)


# ----------------------------------------------------------------
def add_mpmd_tasks(family):
    pygac       = add_mpmd_task(family, 'pygac')
    pystat      = add_mpmd_task(family, 'pystat')
    add2sqlite  = add_mpmd_task(family, 'add2sqlite')
    maketarfile = add_mpmd_task(family, 'maketarfile')

    add_trigger(pystat, pygac)
    add_trigger(add2sqlite, pystat)
    add_trigger(maketarfile, add2sqlite)

    return dict(pygac=pygac, pystat=pystat,
                add2sqlite=add2sqlite, maketarfile=maketarfile)


# ----------------------------------------------------------------
def add_dearchiving_tasks(family):
    family.add_task('getdata')
    #family.add_task('ecfs')
    #family.add_task('mars')


# ----------------------------------------------------------------
def familytree(node, tree=None):
    """
    Given an ecflow node, walk the tree in downward direction 
    and collect all families.

    @param node: The node to start from.
    @type node: ecflow.Node
    @return: All collected families
    @rtype: list
    """
    # Initialize tree on the first call
    if tree is None:
        tree = list()

    # Walk the current node's subnodes
    subnodes = node.nodes
    for subnode in subnodes:
        # Save node to the tree if its type is ecflow.Family
        if isinstance(subnode, ecflow.Family):
            abspath = subnode.get_abs_node_path()
            tree.append(abspath[1:])    # skip initial '/' because otherwise
                                        # os.path.join() doesn't join paths
                                        # correctly.

            # Call function recursively.
            familytree(subnode, tree)

    return tree


# ----------------------------------------------------------------
def build_suite():
    """
    Build the ecflow suite.
    """

    logger.info('Building suite.')


    # ========================
    # GENERAL SUITE PROPERTIES
    # ========================

    defs  = ecflow.Defs()
    suite = defs.add_suite( mysuite )

    # Set suite level variables
    set_vars(suite)
    
    # Set default status
    suite.add_defstatus(ecflow.DState.suspended)

    # Define thread limits
    suite.add_limit("mpmd_threads", mpmd_threads_number)
    suite.add_limit("serial_threads", serial_threads_number)


    # ========================
    # ADD CRON JOB
    # ========================

    start  = ecflow.TimeSlot(0,0)
    finish = ecflow.TimeSlot(23,59)
    incr   = ecflow.TimeSlot(0,1)
    time_series = ecflow.TimeSeries( start, finish, incr, False)
    cron = ecflow.Cron()
    cron.set_time_series( time_series )
    fam_submit = suite.add_family('queue_submitter')
    submit = fam_submit.add_task('submit')
    submit.add_cron( cron )
    fam_submit.add_variable('ECF_JOB_CMD', ecgate_job_cmd)


    # ========================
    # DEFINE TOPLEVEL FAMILIES
    # ========================

    fam_proc   = suite.add_family('proc')
    fam_dearch = suite.add_family('dearchiving')

    start  = ecflow.TimeSlot(0,0)
    finish = ecflow.TimeSlot(23,55)
    incr   = ecflow.TimeSlot(0,5)
    time_series = ecflow.TimeSeries( start, finish, incr, False)
    cron = ecflow.Cron()
    cron.set_time_series( time_series )
    fam_arch  = suite.add_family('archiving')
    storedata = fam_arch.add_task('storedata')
    storedata.add_cron( cron )
    fam_arch.add_variable('ECF_JOB_CMD', serial_job_cmd)

    # Activate thread limits
    fam_proc.add_inlimit('mpmd_threads')
    fam_dearch.add_inlimit('serial_threads')

    # Define job commands
    fam_proc.add_variable('ECF_JOB_CMD', mpmd_job_cmd)
    fam_dearch.add_variable('ECF_JOB_CMD', serial_job_cmd)


    # ===============================
    # DEFINE DYNAMIC FAMILIES & TASKS
    # ===============================

    dearch_interval  = interval_value
    io_hiding_offset = io_offset_value
    dearch_counter   = 0
    tar_counter      = 0

    fam_tar   = None
    fam_chunk = None

    mpmd_families = list()
    tarfiles_within_current_interval = list()


    # Make sure dearchiving interval is at least one 
    # greater than IO hiding offset.
    if not (dearch_interval - io_hiding_offset) >= 1:
        raise ValueError('Dearchiving interval must be at least one greater '
                         'than IO hiding offset.')

    # connect to database and get_sats list
    db = AvhrrGacDatabase( dbfile=gacdb_sqlite_file )

    # ignored satellites
    default_ignore_sats = ['NOAA6', 'NOAA8', 'NOAA10']
    if args.ignoresats:
        add_ignore_sats = args.ignoresats 
        ignore_list = default_ignore_sats + add_ignore_sats
    else:
        ignore_list = default_ignore_sats


    if args.satellite:
        satellites = [args.satellite.upper()]
    else:
        satellites = db.get_sats( start_date=args.sdate, end_date=args.edate,
                                  ignore_sats=ignore_list )

    # -- loop over satellites ------------------------------------------------
    for sat in satellites:
    
        # create sat family
        fam_sat = fam_proc.add_family( sat )

        # add satellite variable
        fam_sat.add_variable("SATELLITE", sat)
    
        # get years list
        years = db.get_years(sat)

    
        # -- loop over years for satellite -----------------------------------
        for year in years: 

            if args.userdatelimit:

                if year >= args.sdate.year and year <= args.edate.year:
                    # create family year for satellite
                    fam_year = fam_sat.add_family( str(year) )

                    # start and end date for year & satellite
                    sd = args.sdate
                    ed = args.edate
                else:
                    continue

            else:

                # create family year for satellite
                fam_year = fam_sat.add_family( str(year) )

                # start and end date for year & satellite
                sd = datetime.date(year, 1, 1)
                ed = datetime.date(year, 12, 31)


            # get tarfile list
            tarfiles = db.get_tarfiles( start_date=sd, end_date=ed, 
                    sats=[sat], include_blacklisted=False )
    
    
            # -- loop over tarfiles for year & satellite ---------------------
            for tarfil in tarfiles:

                # split tarfilename
                tarbase  = os.path.basename(tarfil)
                tardoys  = ((tarbase.split("."))[0].split("_"))[2].split("x")
                taryear  = (tarbase.split("."))[0].split("_")[1]
                tarsdate = date_from_year_doy( int(taryear), int(tardoys[0]) )
                taredate = date_from_year_doy( int(taryear), int(tardoys[1]) )

                first_tar_date = tarsdate
                last_tar_date = taredate

                date_str = first_tar_date.strftime("%Y%m%d")+\
                           '_'+last_tar_date.strftime("%Y%m%d")

                if tar_counter % dearch_interval == 0:
                    if fam_chunk:
                        # Add all collected tarfiles to the current dearchiving family
                        fam_chunk.add_variable('TARFILES', 
                                ' '.join(tarfiles_within_current_interval))

                        # Reset list of tarfiles within current interval
                        tarfiles_within_current_interval = []

                    # Create new family for dearchiving the next chunk of data.
                    fam_chunk = fam_dearch.add_family('chunk{0}'.format(dearch_counter))
                    add_dearchiving_tasks(fam_chunk)
                    fam_chunk.add_variable("ECF_TRIES", 2)
                    dearch_counter += 1

                    # Make it wait for the current MPMD family minus a possible
                    # offset in order to hide IO time behind computation time.
                    if fam_tar:
                        add_trigger(fam_chunk, 
                                mpmd_families[tar_counter - io_hiding_offset - 1])
                    else:
                        # There is no trigger for the first IO chunk.
                        pass

                # Create one MPMD family for each tar_range_archive
                fam_tar = fam_year.add_family('{0}'.format(date_str))
                tar_counter += 1

                # add start and end day of fam_tar
                add_family_variables(fam_tar, 
                        first_tar_date.strftime("%Y%m%d"),
                        last_tar_date.strftime("%Y%m%d"))

                # Make it wait for the current dearchiving family.
                add_trigger(fam_tar, fam_chunk)

                # Add MPMD tasks to each tarfile family
                add_mpmd_tasks(fam_tar)

                # Save the created family for later use
                mpmd_families.append(fam_tar)
                tarfiles_within_current_interval.append(tarfil)

    # -- end of loop over satellites -----------------------------------------

    # Add last chunk of collected tarfiles to the last dearchiving family
    fam_chunk.add_variable('TARFILES', 
            ' '.join(tarfiles_within_current_interval))



    # ============================
    # CREATE SUITE DEFINITION FILE
    # ============================

    # Check job creation
    defs.check_job_creation()

    # Save suite to file
    suite_def_file = mysuite + '.def'
    logger.info('Saving suite definition to file: {0}'.format(
                suite_def_file))
    defs.save_as_defs(suite_def_file)


    # ======================
    # CREATE LOG DIRECTORIES
    # ======================

    logger.info('Creating log directories on both the local and '
                'the remote machine.')

    # Create a tree of all families in the suite 
    # (i.e. families, subfamilies, subsubfamilies etc)
    tree = familytree(suite)

    # Create corresponding log-directory tree:
    # 1.) Local machine
    for node in tree:
        dirname = os.path.join(ecf_out_dir, node)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    # 2.) Remote machine
    ssh = SSHClient(user=remote_user_name, host=remote_host_name)
    for node in tree:
        remote_dir = os.path.join(remote_log_dir, node)
        ssh.mkdir(remote_dir, batch=True)   # batch=True appends this mkdir
                                            # call to the command batch.

    # Create all remote directories in one step (is much faster)
    ssh.execute_batch()

# ----------------------------------------------------------------

# end of defs
# start of main code

# ================================================================

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=sys.argv[0]+'''
    creates the suite '''+mysuite+''' required by ecflow.''')
    
    parser.add_argument('--sdate', type=str2date, \
            help='start date, e.g. 20090101', required=True)
    parser.add_argument('--edate', type=str2date, \
            help='end date, e.g. 20091231',required=True)
    parser.add_argument('--satellite', type=str,
            help='''satellite name, e.g. noaa15, metopa, 
            terra, aqua''')
    parser.add_argument('--ignoresats', type=str2upper, 
            nargs='*', help='''List of satellites 
            which should be ignored.''')
    parser.add_argument('--userdatelimit', help='''Take args.sdate
            and args.edate instead of start- and enddate of each
            satellite (i.e. database date limits).''', 
            action="store_true")
    
    args = parser.parse_args()
    
    print "\n"
    print (" * Script         : %s" % sys.argv[0])
    print (" * start date     : %s" % args.sdate)
    print (" * end date       : %s" % args.edate)
    print (" * user date limit: %s" % args.userdatelimit)
    print (" * ignore sats    : %s" % args.ignoresats)
    print (" * Creating suite definition %s" % mysuite)
    print "\n"

    build_suite()

# ================================================================
