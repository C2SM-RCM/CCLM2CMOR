#!/bin/bash
###############################################################################
# Project       : DWD
#
# Program name  : run_cmor_chunk.sh
#
# Author        : Christian Steger (christian.steger@dwd.de)
#
# Date created  : 27.03.2018
#
# Purpose       : run script for the chunking of CMORized variables. Organizes submission of BATCH
#                 jobs.
#                 for each variable defined a batch job is started in order to chunk the data
#                 for the period START_PERIOD until STOP_PERIOD
#
# Dependencies  : PBS, Python, sed, CCLM2CMOR
#
# Modifications for CRAY system at HLRS by H.-J. Panitz, IMK-TRO/KIT, Augsut, 2019
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
JOBDIR="${BASEDIR}/${TMPLDIR}/batch_jobs"
CMORDIR="${BASEDIR}/src/CMORlight"
CMORPROG="${CMORDIR}/cmorlight.py"
LOGDIR="${BASEDIR}/logs"
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
   echo Directory ${JOBDIR} has been created, contains standard out- end error files of batch jobs
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

# Settings for CHUNK job
MEM_CHUNK="3500"      # in GB
WALLTIME_CHUNK="00:20:00"
ACCOUNT="bg1155"    # has to be changed for others users!!

START_PERIOD=1999
STOP_PERIOD=2016
#
# Settings for Chunking
# Total list FPSC
# VAR_LIST=(tasmax tasmin tas ts pr wsgsmax sfcWindmax huss ps psl rsds rlds hfls hfss rsus rlus evspsbl clt snc snd mrros mrro mrsol mrso prw clivi clwvi orog sftlf zmla CAPE CIN ua1000 ua925 ua850 ua700 ua500 ua200 va1000 va925 va850 va700 va500 va200 ua100m va100m uas vas wa1000 wa925 wa850 wa700 wa500 wa200 ta1000 ta925 ta850 ta700 ta500 ta200 zg1000 zg925 zg850 zg700 zg500 zg200 hus1000 hus925 hus850 hus700 hus500 hus200)
#
# FPSC Var-list separated
VAR_LIST=(tasmax tasmin)
#VAR_LIST=(tasmax tasmin tas ts pr wsgsmax sfcWindmax)
#VAR_LIST=(huss ps psl rsds rlds hfls hfss rsus rlus evspsbl clt snc snd mrros mrro mrsol mrso prw clivi clwvi zmla CAPE CIN)
#VAR_LIST=(ua1000 ua925 ua850 ua700 ua500 ua200 va1000 va925 va850 va700 va500 va200 ua100m va100m uas vas)
#VAR_LIST=(wa1000 wa925 wa850 wa700 wa500 wa200 ta1000 ta925 ta850 ta700 ta500 ta200 zg1000 zg925 zg850 zg700 zg500 zg200 hus1000 hus925 hus850 hus700 hus500 hus200)
FREQ_LIST_CHUNK="-r 1hr,3hr,6hr,day,mon,sem,fx" # remove to get all frequencies for a variable
#FREQ_LIST_CHUNK="-r sem"

###############################################################################
# End of user settings ########################################################
###############################################################################

# Loop over variables #########################################################
for VAR in ${VAR_LIST[*]}
do
# Loop over variables #########################################################
    echo "### Start chunking for  variable: " ${VAR} " #########################"
    # Concatenate files to chunks #############################################
    # Create job for chunking
    # Note: whne chunking the multiprocessing option -M makes no sense!
    # Note_ using the option -remove the oroginal files will be removed, only chunked files are retained
#   ARGS_CHUNK="--chunk-var --remove -v ${VAR} ${FREQ_LIST_CHUNK} -n ${USE_VERSION} -O"
    ARGS_CHUNK="--chunk-var  -v ${VAR} ${FREQ_LIST_CHUNK} -O"
    echo "Create job to chunk variable " ${VAR} " for years " ${START_PERIOD} "-" ${STOP_PERIOD}
    sed \
        -e s%@{ARGS_CHUNK}%"${ARGS_CHUNK}"%g \
        -e s%@{CMORPROG}%${CMORPROG}%g \
        -e s%@{JOBDIR}%${JOBDIR}%g \
        -e s%@{PYTHON}%${PYTHON}%g \
        -e s%@{START_PERIOD}%${START_PERIOD}%g \
        -e s%@{STOP_PERIOD}%${STOP_PERIOD}%g \
        -e s%@{VAR}%${VAR}%g \
        -e s%@{NODES}%${NODES}%g \
        -e s%@{WALLTIME_CHUNK}%${WALLTIME_CHUNK}%g \
        -e s%@{MEM_CHUNK}%${MEM_CHUNK}%g \
        -e s%@{ACCOUNT}%${ACCOUNT}%g \
        -e s%@{PARTITION}%${PARTITION}%g \
        <${TMPLDIR}/cmor_chunk.job.tmpl.sh>${JOBDIR}/cmor_chunk_${VAR}_${START_PERIOD}-${STOP_PERIOD}.job
        # Submit job for chunking
        echo "******************************************"
        echo \* submitting CHUNK job for ${VAR} for years ${START_PERIOD}-${STOP_PERIOD} \*
        echo "******************************************"
        echo ""
    sbatch ${JOBDIR}/cmor_chunk_${VAR}_${START_PERIOD}-${STOP_PERIOD}.job
    echo ""
done # end loop over variables

echo "########################################################################"
echo "### All variables processed. Regular exit. #############################"
echo "########################################################################"
exit

