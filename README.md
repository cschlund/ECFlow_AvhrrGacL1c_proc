ECFlow_AvhrrGacL1c_proc
=======================

AVHRR GAC L1c processing using ecflow

Dependencies: You need also to install
    https://github.com/Funkensieper/pycmsaf.git
    https://github.com/cschlund/pytAVHRRGACl1c.git

You have to clone this repository twice:
    1) local machine, e.g. ecgate
    2) remote machine, eg.g cca

If you want to test or run only specific dates and satellites,
please create your suite using "--testcase"
    For more details: ./create_suite.py --help


./sql/
    sqlite databases must be placed here required on remote

./src/
    this is the source code, which is running on the remote machine

./tle/
    here are the TLE files, which are required in pygac (remote machine)

./mpmd/
    this is the source code for ecflow required on local machine

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
        ./cleanup_remote.sh

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

