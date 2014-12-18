ECFlow_AvhrrGacL1c_proc
=======================

AVHRR GAC L1c processing using ecflow

After you have cloned this repository 
(local [ecgate] and remote machine [cca]), 
you have to rename the clone:
clone == suite name, 
for example:
ECFlow_AvhrrGacL1c_proc == proc_avhrrgac_l1c


sql/
    sqlite databases must be placed here


src/
    this is the source code, which
    is running on the remote machine


tle/
    here are the TLE files, which are
    required in pygac


mpmd/
    this is the source code for ecflow

    edit config.sh
        export ECF_NODE=ecgb11
        export ECF_PORT=3500
        etc.

    start ecflow server
        ecflow_start -p 3500 -d $HOME/ecflow_logs

    stop ecflow server, if you do not need it anymore!
        ecflow_stop -p 3500

    create mpmd database
        ./createdb.sh    

    edit suite config file
        cd ecflow_suite
        edit config_suite.py

    clear generated/ and log/ directories - if necessary!
    on ecgate and cca $SCRATCH !!
        ./cleanup.sh

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

