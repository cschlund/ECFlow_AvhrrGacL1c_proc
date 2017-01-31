ECFlow_AvhrrGacL1c_proc
=======================

AVHRR GAC L1c processing using ecflow

BRANCH information:

    *master* branch operates on monthly tarfiles, e.g. NOAA7_1985_01.tar

    *weekly_tarfiles* branch operates on weekly tarfiles, e.g. n07_1985_001x008.tar


Dependencies: You need also to install

    on remote machine (CCA)
        https://github.com/pytroll/pygac.git
            branch = feature-clock

    on local (ECGATE) & remote machine (CCA)
        https://github.com/Funkensieper/pycmsaf.git
        https://github.com/cschlund/pytAVHRRGACl1c.git


You have to clone this repository twice:

    1) local machine, e.g. ecgate: /path/to/repo
    2) remote machine, eg.g cca: /path/to/repo


If you want to test or run only specific dates and satellites,
please create your suite using "--testcase"
    For more details: ./create_suite.py --help


./sql/

    "AVHRR_GAC_archive_filled.sqlite3": 
    sqlite database must be placed here required on remote;
    while processing this database will be filled;

        (1) remote machine (CCA) for processing
            cp /perm/ms/de/sf1/gacdb/AVHRR_GAC_archive_l1bonly_20161130.sqlite3 /path/to/ECFlow_AvhrrGacL1c_proc/sql/AVHRR_GAC_archive_proc_v3.sqlite3

        (2) local machine (ECGATE) for suite creation
            ln -s /perm/ms/de/sf1/gacdb/AVHRR_GAC_archive_l1bonly_20161130.sqlite3 BASIS_AVHRR_GAC_archive.sqlite3


./src/

    this is the source code, which is running on the remote machine


./tle/

    here are the TLE files, which are required in pygac (remote machine)


./mpmd/

    this is the source code for ecflow required on local machine (ECGATE)

    edit config.sh
        adapt all variables and paths!

    start ecflow server
        ecflow_start -p 3500 -d $HOME/ecflow_logs

    stop ecflow server, if you do not need it anymore!
        ecflow_stop -p 3500

    create mpmd database
        ./createdb.sh    

    edit suite config file
        cd ecflow_suite
        edit config_suite.py

    clear directories if necessary
        ./cleanup_local.sh

    generate suite definition
        ./create_suite.py -h
        ./create_suite.py --sdate 20080101 --edate 20081231

    register and load suite
        cd ..
        [./reset.sh]
        ./register.sh
        ./load.sh

    open ecflowview GUI
        ecflowview &

    and resume suite

