#... change this due to your needs

GCM=HadGEM2-ES     
EXP=RCP85



#... directory path settings
IN_SUB=HadGEM2-ES_Hist_RCP85/RCP85 
SPDIR=${PROJECT}/CMOR # this is starter package specific and not necessary, if the full paths are defined in the following lines
ARCH_SRC=/store/c2sm/ch4/ssilje/Archive_cosmo_runs
PFDIR=${SPDIR}/src/cclm_post           # base directory where the scripts for the experiment are stored
WORKDIR=${SPDIR}/work/cclm_work                  # NONE of the created files under this directory will be deleted at the end of the job chain
INPUTPOST=${SPDIR}/input     # do not define SCRATCHDIR as any of your other paths!!!
OUTPUTPOST=${SPDIR}/work/outputpost
INPATH=${ARCH_SRC}/${IN_SUB}


#... batch command
BATCH_CMD=bash                           # the batch command of your computer system

#... start and end date of the simulation

YDATE_START=201001      #Start year and month for processing (if not given in command line) YYYYMM
YDATE_STOP=201012     #End year and month for processing (if not given in command line)  YYYYMM

SIM_START=1949120100 # start date of simulation YYYYMMDDHH[mmss]: needed for constant file
#SIM_STOP=2099123000  # end date of simulation YYYYMMDDHH[mmss]


#... directory and binary path settings for utilities
UTILS_BINDIR=${SPDIR}/src/cfu/bin          # absolute path to directory of utility binaries
CDO=/apps/daint/UES/jenkins/6.0.UP02/gpu/easybuild/software/CDO/1.8.0rc6-CrayGNU-2016.11/bin    # absolute path of the CDO binary 
NCO_BINDIR=/apps/daint/UES/jenkins/6.0.UP02/gpu/easybuild/software/NCO/4.6.7-CrayGNU-2016.11/bin  # absolute path to directory of NCO binaries
NC_BINDIR=/apps/daint/UES/jenkins/6.0.UP02/gpu/easybuild/software/netCDF/4.4.1.1-CrayGNU-2016.11/bin #  absolute path of the netcdf binaries (ncdump, nccopy)

#CDO=/usr/local/bin
#NCO_BINDIR=/usr/local/bin
#NC_BINDIR=/home/mgoebel/anaconda3/bin



#... choose compression type of output in post-processing and archiving
#...    0 = no compression
#...    1 = internal compression (compression in netCDF file, requires netCDF Library with HDF-lib and z-lib)
#...    2 = external compression (compression with gzip, requires gzip to be installed)
ITYPE_COMPRESS_POST=0
ITYPE_COMPRESS_ARCH=0

#... set number of boundary lines to be cut off in the time series data and before evaluating the data with SAMOA
NBOUNDCUT=10

# CCLM settings

IE_TOT=101
JE_TOT=111

#... CCLM specific settings. These are also needed for the post-processing.
#~ HOUT_INC=(7 03:00:00 24:00:00 01:00:00 03:00:00 06:00:00 06:00:00 24:00:00) # time increment for each GRIBOUT hh:mm:ss
                                       #~ # it should be a multiple of the CCLM time step
                                       #~ # first numeric is the number of GRIBOUT namelists
#~ #HINCMXT=${HOUT_INC[7]}  # interval for min/max of temperature (to be consistent with HOUT_INC in global settings above)
#~ #HINCMXU=${HOUT_INC[7]}  # interval for min/max of wind speed (to be consistent with HOUT_INC in global settings above)

