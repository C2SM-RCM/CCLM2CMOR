#!/bin/bash
###############################################################################
# Project       : DWD
#
# Program name  : run_cmor.sh
#
# Author        : Christian Steger (christian.steger@dwd.de)
#
# Date created  : 27.03.2018
#
# Purpose       : run script for the cmor tool. Organizes submission of BATCH
#                 jobs.
#                 for each variable defined a batch job is started in order to CMORize the data
#                 from START_PERIOD until STOP_PERIOD
#                 the use of batch jobs will speed up the CMORization consideraby in case that a large no. of variables have to be converted
#
# Dependencies  : PBS, Python, sed, CCLM2CMOR
#
# Modifications for CRAY system at HLRS by H.-J. Panitz, IMK-TRO/KIT, Augsut, 2019
# 
# IMPORTANT NOTE: if you want de-rotate U and V wind components on any level don't do that for U and V simultanously!!
#                 apply this script for all U components first, wait until all jobs are finihed, then apply it for V
#                 otherwise results might become nonsens because during the CMOR-process help files are created that have
#                 identical names for U and V
#
#                 it would be a good advice not to define more variables per application of the script than no. of jobs are allowed on your machine
#
#                 This version of the batch script does not perform the chunking of CMORized data!!
#                 
#
###############################################################################

###############################################################################
# Start of user settings ######################################################
###############################################################################
#set -eux
# Environment variables
export IGNORE_ATT_COORDINATES=1 # grid for derotation

# General settings
BASEDIR="/pf/b/b364034/Bin/CCLM2CMOR/Version_20200115/CCLM2CMOR-master"
TMPLDIR="${BASEDIR}/Batch"
JOBDIR="${BASEDIR}/Batch/batch_jobs"
CMORDIR="${BASEDIR}/src/CMORlight"
CMORPROG="${CMORDIR}/cmorlight.py"
LOGDIR="${BASEDIR}/logs/cmorlight"
#PYTHON="/sw/rhel6-x64/python/python-2.7-ve0-gcc49/bin/python" #python command (e.g. python or python3)
#PYTHON="/sw/rhel6-x64/python/python-3.5.2-gcc49/bin/python" #python command (e.g. python or python3)
PYTHON="/sw/spack-rhel6/anaconda3-2020.02-dqbodz/bin/python" #python command (e.g. python or python3)
#
# some checks
#
  if [ ! -d ${BASEDIR} ]
  then
   echo
   echo Basic Directory ${BASEDIR} does not exist
   echo Script exit
   echo
   exit
  fi
#
  if [ ! -d ${TMPLDIR} ]
  then
   echo
   echo Directory ${TMPLDIR} containing the batch script does not exist
   echo Script exit
   echo
   exit
  fi
#
  if [ ! -d ${CMORDIR} ]
  then
   echo
   echo Directory ${CMORDIR} containing the CMOR script does not exist
   echo Script exit
   echo
   exit
  fi
#
  if [ ! -f ${CMORPROG} ]
  then
   echo
   echo CMOR Mainscript ${CMORPROG}  does not exist
   echo Script exit
   echo
   exit
  fi
#
  if [ ! -d ${JOBDIR} ]
  then
   echo
    mkdir -p ${JOBDIR}
   echo 
   echo Directory ${JOBDIR} has been created, contains the actual runscript for each variable and standard out- end error files of batch jobs
   echo
  fi
#
  if [ ! -d ${LOGDIR} ]
  then
   echo
    mkdir -p ${LOGDIR}
   echo 
   echo Directory ${LOGDIR} has been created, contains log-files created during the CMOR-process
   echo
  fi
#

# Settings for CMOR job
NODES=1             # since shared partition is used on MISTRAL max. no. of nodes is 1
PARTITION="compute2"   # shared Partition is used on MISTRAL
CPUS=36       # define no. of CPUS according to the no. of years that will be treated per batch job; maximum no. of CPUS = max. no. CPUS per node (machine dependent)
                 # for shared partiton max. no of CPUS is 36
MEM=3500              #  1300 = max. memory per CPU for shared partition
WALLTIME="03:00:00"
ACCOUNT="bg1155"    # has to be changed for others users!!

# Settings for CMORization
START_PERIOD=2000      #    Start year for processing,e.g. 1999. If start month is not January add the month, e.g.199912) Format: YYYY[MM]
STOP_PERIOD=2001      # end year of the period to process
USE_VERSION="v20200801"     # vYYYYMMDD for directory structure
# Total list FPSC
# VAR_LIST=(tasmax tasmin tas ts pr wsgsmax sfcWindmax huss ps psl rsds rlds hfls hfss rsus rlus evspsbl clt snc snd mrros mrro mrso1 mrso prw clivi clwvi orog sftlf zmla CAPE CIN ua1000 ua925 ua850 ua700 ua500 ua200 va1000 va925 va850 va700 va500 va200 ua100m va100m uas vas wa1000 wa925 wa850 wa700 wa500 wa200 ta1000 ta925 ta850 ta700 ta500 ta200 zg1000 zg925 zg850 zg700 zg500 zg200 hus1000 hus925 hus850 hus700 hus500 hus200)
#
# FPSC Var-list separated
#daily
#VAR_LIST=(CAPE CIN mrso mrso1 sfcWindmax wsgsmax snc snd tasmax tasmin)
#
#6hr
#VAR_LIST=(ps psl zg1000 zg200 zg500 zg700 zg850 zg925)
#3hr
#VAR_LIST=(ua1000 ua925 ua850 ua700 ua500 ua200 va1000 va925 va850 va700 va500 va200 wa1000 wa925 wa850 wa700 wa500 wa200)
#VAR_LIST=(ta1000 ta925 ta850 ta700 ta500 ta200 hus1000 hus925 hus850 hus700 hus500 hus200)
#1hr
#VAR_LIST=(clgvi clivi clt clwvi evspsbl hfls hfss huss mrro mrros pr prw)
VAR_LIST=(rlds rlus rsds rsus tas ts ua100m uas va100m vas zmla)
FREQ_LIST="-r 1hr,3hr,6hr,day,mon,sem" # remove to get all frequencies for a variable
#FREQ_LIST="-r 1hr,3hr,6hr,day,mon" # remove to get all frequencies for a variable
#FREQ_LIST="-r sem" # remove to get all frequencies for a variable

###############################################################################
# End of user settings ########################################################
###############################################################################

# Loop over variables #########################################################
for VAR in ${VAR_LIST[*]}
do
    echo "### Start processing  variable: " ${VAR} " #########################"
    # Set options for CMOR program
    ARGS="-M ${CPUS} -v ${VAR} ${FREQ_LIST} -n ${USE_VERSION} -O"
#   ARGS="-M 2 -v ${VAR} ${FREQ_LIST} -n ${USE_VERSION} -O"
#   ARGS="-v ${VAR} ${FREQ_LIST} -n ${USE_VERSION} -O"
    # Initialize array for job IDs
    JOB_IDS=()
    # Create job script ###########################################################
    START=${START_PERIOD}
    START_YEAR=`echo $START} | cut -c 1-4`
    echo START_YEAR ${START_YEAR}
    # Loop until all years are processed
    while [ ${START_YEAR} -le ${STOP_PERIOD} ]
    do
        # Calculate stop year for job
        (( STOP = START_YEAR + CPUS - 1))
        if [ ${STOP} -gt ${STOP_PERIOD} ]
        then
            STOP=${STOP_PERIOD}
        fi
        # Create job script for current period from template
        sed \
            -e s%@{ARGS}%"${ARGS}"%g \
            -e s%@{CMORPROG}%${CMORPROG}%g \
            -e s%@{CPUS}%${CPUS}%g \
            -e s%@{JOBDIR}%${JOBDIR}%g \
            -e s%@{NODES}%${NODES}%g \
            -e s%@{PARTITION}%${PARTITION}%g \
            -e s%@{MEM}%${MEM}%g \
            -e s%@{PYTHON}%${PYTHON}%g \
            -e s%@{START}%${START}%g \
            -e s%@{STOP}%${STOP}%g \
            -e s%@{VAR}%${VAR}%g \
            -e s%@{WALLTIME}%${WALLTIME}%g \
            -e s%@{ACCOUNT}%${ACCOUNT}%g \
            <${TMPLDIR}/cmor.job.tmpl.sh>${JOBDIR}/cmor_${VAR}_${START}-${STOP}.job
        # Submit CMOR job
        echo "******************************************"
        echo \* submitting CMOR job for years ${START}-${STOP} \*
        echo "******************************************"
         JOB_ID=$(sbatch ${JOBDIR}/cmor_${VAR}_${START}-${STOP}.job)
        # Wait until last job of period has finished
         JOB_IDS+=" ${JOB_ID%.*}"
        (( START = ${STOP} + 1 ))
        (( START_YEAR = ${STOP} + 1 ))
    done
done # end loop over variables
# chunking will not yet been done; therefore, exit

echo "########################################################################"
echo "### All variables processed. Regular exit. #############################"
echo "########################################################################"
exit

