#!/bin/bash

#-------------------------------------------------------------------------
# Settings for the first step of the CMOR process
# 
# Matthias Göbel 
#
#-------------------------------------------------------------------------


post_step=0 #to limit post processing to step 1 or 2, for all other values both steps are executed

#Simulation details used for creating a directory structure 

GCM=ICHEC-EC-EARTH #driving GCM
EXP=RCP85      #driving experiment name

#-------------------------------------------
# time settings

#processing range for step 1:
START_DATE=2006      #Start year and month for processing (if not given in command line YYYYMM
STOP_DATE=2100    #End year and month for processing (if not given in command line  YYYYMM

#for step 2 (if different from step 1:
YYA=  #Start year for processing YYYY
YYE= #End year for processing YYYY

#-------------------------------------------
# Directory path settings

BASEDIR=/scratch/snx3000/ssilje/CCLM2CMOR #Directory where the scripts are placed 
DATADIR=${SCRATCH}/CMOR  #Directory where all the data will be placed (typically at /scratch/)

#ARCH_BASE=/store/archive/c2sm/pr04/cosmo_CORDEXruns # directory where the raw data of the simulations are archived
#ARCH_BASE=/store/c2sm/ch4/ssilje/Archive_cosmo_runs/ # directory where the raw data of the simulations are archived
ARCH_BASE=/scratch/snx3000/ssilje/CORDEX_SIMULATION/ # directory where the raw data of the simulations are archived
SRCDIR=${BASEDIR}/src       # directory where the post processing scripts are stored
SRCDIR_POST=${BASEDIR}/src/cclm_post    # directory where the subscripts are stored

WORKDIR=${DATADIR}/work/post # work directory, CAUTION: WITH OPTION "--clean" ALL FILES IN THIS FOLDER WILL BE DELETED AFTER PROCESSING!
LOGDIR=${BASEDIR}/logs/shell #logging directory

#input/output directory for first step
INDIR_BASE1=${DATADIR}/input     # directory to where the raw data archives are extracted
OUTDIR_BASE1=${DATADIR}/work/outputpost # output directory of the first step

#for second step
INDIR_BASE2=${OUTDIR_BASE1}
OUTDIR_BASE2=${DATADIR}/work/input_CMORlight


#-------------------------------------------
#Special settings for first step
num_extract=10 #number of archived years to extract/move at once (depends e.g. on the file number limit you have on your working director (scratch))
NBOUNDCUT=13 # number of boundary lines to be cut off in the time series data 
IE_TOT=132 # number of gridpoints in longitudinal direction?
JE_TOT=129 # number of gridpoints in latitudinal direction
PLEVS=(200. 500. 850. 925.)  # list of pressure levels to output if not set in timeseries.sh.The list must be the same as or a subset	of the list in the specific GRIBOUT. 

#-------------------------------------------
#Special settings for second step

proc_list="AEVAP_S" #which variables to process (set proc_all=false for this to take effect); separated by spaces
proc_all=true #process all available variables (not only those in proc_list)
LFILE=0  # Set LFILE=1 if only primary fields (given out by COSMO) should be created and =2 for only secondary fields (additionally calculated for CORDEX); for any other number both types of fields are calculated


