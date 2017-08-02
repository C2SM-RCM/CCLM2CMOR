#!/bin/ksh
#SBATCH --job-name=CCLM2CMOR_R26MPI
#SBATCH --output=ts_build.o%J
#SBATCH --error=ts_build.o%J
#SBATCH --partition=prepost
#SBATCH --nodes=1
##SBATCH --mem-per-cpu=5120
#SBATCH --mem-per-cpu=20480
#SBATCH --time=12:00:00
##SBATCH --time=24:00:00
##SBATCH --share
#SBATCH --mail-user=klaus.keuler@b-tu.de
#SBATCH --mail-type=FAIL
#SBATCH --account=bb0931
###SBATCH --begin=11:45:00
#
#-------------------------------------------------------------------------
# Concatenats monthly time series files produced by CCLM chain script post
# to annual file for a given time period of years 
# 
# K. Keuler, Stand: 06.04.2017
#-------------------------------------------------------------------------

# EXPID  - simulation ID
# WORKDIR- directory of monthly time series
# YYA    - start year
# MMA    - start month
# YYE    - end year
# MME    - end month
# FILET  - start of the file names of the tar-files
typeset -Z2 MM MA ME MP MMA MME DHH EHH
typeset -Z4 YY YYA YYE YP

GCM=HadGEM2-ES
EXP=RCP85

YYA=2005
MMA=01
YYE=2005
MME=12

LASTDAY=30   #Last day of each month (e.g. 30 or 31)
#

n=true #normal printing mode
v=false #verbose printing mode

while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
      -g|--gcm)
      GCM=$2
      shift 
      ;;
      -x|--exp)
      EXP=$2
      shift 
      ;;     
       -s|--start)
      YYA=$2         
      shift
      ;;
      -e|--end)
      YYE=$2 
      shift 
      ;;
      -S|--silent)
      n=false
      ;;
      -V|--verbose)
      v=true
      ;;
      *)
      echo unknown option!
      ;;  
  esac
  shift 
done

EXPPATH=${GCM}/${EXP}
EXPID=${GCM}_${EXP}

WORKDIR=${SCRATCH}/experiments/${EXPPATH}/post${YYA}_${YYE}
INDIR=${PROJECT}/CMOR/work/outputpost/${EXPPATH}
OUTDIR=${PROJECT}/CMOR/work/input_CMORlight/${EXPPATH}
PERM=755

echo ${EXPPATH}

#
# module Befehl verfügbar machen
#source /sw/rhel6-x64/etc/profile.mistral
#module load getrusage
# getrusage <command>  shows time and memory consumption of specific <command>
#
# Global attributes to be added or changed with respect to CORDEX standards
experiment="HadGEM2-ES downscaled with CCLM_5.0 over Europe"
experiment_id=hist
driving_experiment="HadGEM2-ES, historical, r1i1p1"
driving_model_id=HadGEM2-ES,
driving_model_ensemble_member=r1i1p1
driving_experiment_name=historical
institute_id=ETHZ
institution="Institute for Atmospheric and Climate Science, ETH Zurich, Switzerland"
contact="Silje Soerland (silje.soerland@env.ethz.ch)"
source="Climate Limited-area Modelling Community (CLM-Community) cosmo_131108_5.00_clm1, int2lm_131101_2.00_clm1"
references="http://cordex.clm-community.eu/"
title="HadGEM2-ES downscaled with CCLM_5.0 over Europe"
model_id=CLMcom-CCLM4-8-17
rcm_version_id=v1
project_id="CORDEX-EU_0.44_HadGEM2-ES"
CORDEX_domain=EUR-11
product=output


# Additional individual own attributes	
#btu_run_id=${EXPID}
#dwd_run_id=${EXPID}

# lists of accumulted and instantaneous variables

#accu_list="AEVAP_S ALHFL_S ALWD_S ALWU_S ASHFL_S  ASOB_S  ASOB_T ASOD_T
#           ASWDIFD_S ASWDIFU_S ASWDIR_S ATHB_S ATHB_T DURSUN
#           RAIN_CON RAIN_GSP RUNOFF_G RUNOFF_S SNOW_CON SNOW_GSP SNOW_MELT 
#           TMAX_2M TMIN_2M TOT_PREC VABSMX_10M VMAX_10M"
#inst_list="ALB_RAD  CLCH CLCL CLCM CLCT FI200p FI500p FI850p FI925p  HPBL H_SNOW
#           PMSL PS QV_2M QV200p QV500p QV850p QV925p RELHUM_2M RELHUM200p
#           RELHUM500p RELHUM850p RELHUM925p T_2M T200p T500p T850p T925p
#          TQC TQI TQV T_S U_10M U200p U500p U850p U925p V_10M V200p V500p
#           V850p V925p W_SNOW W_SO_ICE W_SO"
           
accu_list="AEVAP_S ALHFL_S ALWD_S ALWU_S ASHFL_S ASOB_S ASOB_T ASOD_T ASWDIFD_S ASWDIFU_S 
  ASWDIR_S ATHB_S ATHB_T DURSUN RAIN_CON RAIN_GSP RUNOFF_G RUNOFF_S SNOW_CON SNOW_GSP
  SNOW_MELT TMAX_2M TMIN_2M  TOT_PREC VABSMX_10M VMAX_10M"
inst_list="ALB_RAD CLCH CLCL CLCM CLCT HPBL H_SNOW PMSL PS QV_2M RELHUM_2M 
 T_2M TQC TQI TQV T_S U_10M V_10M W_SNOW W_SO_ICE W_SO"
 
 
function echov {
if ${v}
then 
echo $1
fi
} 

function echon {
if ${n}
then 
echo $1
fi
} 
#---------------------------------------------------------------------


# create subdirectory for full time series
[[ -d ${OUTDIR} ]] || mkdir  ${OUTDIR}
#Create and change to WORKDIR
[[ -d ${WORKDIR} ]] || mkdir -p  ${WORKDIR} 
cd ${WORKDIR}
#################################################
YY=$YYA

while [ ${YY} -le ${YYE} ]		# year loop
do
echo ${YY}
FILES=$(ls ${INDIR}/${YYA}_${MMA}/*_ts.nc)

# Set LFILE=0 if only secondary fields should be created
LFILE=1
#
if [ ${LFILE} == 1 ]
then
# concatenate monthly files to annual file

  for FILE in ${FILES}        # var name loop
  do
    FILEIN=$(basename ${FILE})
    (( c2 = ${#FILEIN}-6 ))
    FILEOUT=$(echo ${FILEIN} | cut -c1-${c2})
    echon ${FILEOUT}
    [[ -d ${OUTDIR}/${FILEOUT} ]] || mkdir ${OUTDIR}/${FILEOUT}
    # determine if current variable is an accumulated quantity
    LACCU=0
    for NAME in ${accu_list}
    do
      if [ ${NAME} == ${FILEOUT} ]
      then
        LACCU=1
        echon "${FILEOUT} is accumulated variable"
      fi
    done
    
    if [ LACCU -eq 0 ]
    then
      LACCU=1
      for NAME in ${inst_list}
      do
        if [ ${NAME} == ${FILEOUT} ]
        then
          LACCU=0
          echon "${FILEOUT} is an instantaneous variable"
        fi
      done
      if [ LACCU -eq 1 ]
      then
        echon "error for ${FILEOUT}: neither contained in accu_list nor in inst_list! Skipping..."
      fi
    fi

    
    FILELIST=""
    MA=${MMA}
    ME=${MME}
    MM=${MA}
    while [ ${MM} -le ${ME} ]
    do 
      FILELIST="$(echo ${FILELIST}) $(ls ${INDIR}/${YY}_${MM}/${FILEOUT}_ts.nc)"
      (( MM=MM+1 ))
    done

    echon "Concatenate files"
    echov ${FILELIST}
    # concatenate monthly files to yearly file
    FILEIN=${FILEOUT}_${YY}${MA}-${YY}${ME}.nc
    ncrcat -O -h ${FILELIST} ${FILEIN}
    # extract attribute units from variable time -> REFTIME in seconds since XX-XX-XX ...
    RT=$(ncks -m -v time ${FILEIN} | grep -E 'time '|grep -E 'seconds since' | cut -f 13- -d ' ')
    REFTIME="days since "${RT}
    # extract number of timesteps and timestamps
    NT=$(cdo -s ntime ${FILEIN})
    VT=($(cdo -s showtimestamp ${FILEIN}))
    TYA=$(echo ${VT[0]} | cut -c1-4)
    TMA=$(echo ${VT[0]} | cut -c6-7)
    TDA=$(echo ${VT[0]} | cut -c9-10)
    THA=$(echo ${VT[0]} | cut -c12-13)
    TDN=$(echo ${VT[1]} | cut -c9-10)
    THN=$(echo ${VT[1]} | cut -c12-13)
    TYE=$(echo ${VT[-1]} | cut -c1-4)
    TME=$(echo ${VT[-1]} | cut -c6-7)
    TDE=$(echo ${VT[-1]} | cut -c9-10)
    THE=$(echo ${VT[-1]} | cut -c12-13)
    (( DHH=(TDN-TDA)*24+THN-THA ))
    (( EHH=24-DHH ))
    (( DTS=DHH*1800 ))
    echov "First date:" ${VT[0]}
    echov "Last date:" ${VT[-1]}
    echov "Number of timesteps:" $NT
    echov "Time step:" $DHH "h"
    echov "New reference time:" ${REFTIME}

    if [ ${LACCU} -eq 1 ] 
    then
#   Check dates in files for accumulated variables
#   if necessary: delete first date apend first date of next year
      if [[ ${TDA} -eq 01 && ${THA} -eq 00 ]]
      then
        echov "Eliminating first time step from tmp1-File"
        ncks -O -h -d time,1, ${FILEIN} ${FILEOUT}_tmp1.nc
      elif [[ ${TDA} -eq 01 &&  ${THA} -eq ${DHH} ]]
      then
        echov "Number of timesteps in tmp1-File is OK"
        cp ${FILEIN} ${FILEOUT}_tmp1.nc
      else
        echo "Start date " ${TDA} ${THA}
        echo in "${FILEIN} "
        echo "is not correct"
        exit
      fi
      if [[ ${TDE} -eq ${LASTDAY} && ${THE} -eq ${EHH} ]]
      then
        YP=${YY}
        (( MP=TME+1 ))
        if [ ${MP} -gt 12 ]
        then
          MP=01
          (( YP=YP+1 ))
        fi
        FILENEXT=${INDIR}/${YP}_${MP}/${FILEOUT}_ts.nc
        if [ -f ${FILENEXT} ]
        then
          echov "Append first date from next month's file to the end of current month"
          ncks -O -h -d time,0 ${FILENEXT} ${FILEOUT}_tmp2.nc
          ncrcat -O -h  ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp2.nc ${FILEOUT}_tmp3.nc
        else
          echo "Try to append first date from next month's file but"
          echo ${FILENEXT} does not exist
          exit
        fi
      elif [[ ${TDE} -eq 01 &&  ${THE} -eq 00 ]]
      then
        (( MP=TME ))
        (( YP=TYE ))
        echov "Last timestep in tmp3-File is OK"
        mv ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp3.nc
      else
        echo "END date " ${TDE} ${THE}
        echo in "${FILEIN} "
        echo "is not correct"
        exit
      fi
      ENDFILE=${OUTDIR}/${FILEOUT}/${FILEOUT}_${TYA}${TMA}${TDA}00-${YP}${MP}0100.nc
#     shift time variable by DHH/2*3600 and transfer time from seconds in days       
      echov "Modifying time and time_bnds values and attributes"
      ncap2 -O -h -s "time_bnds=time_bnds/86400" -s "time=(time-${DTS})/86400" ${FILEOUT}_tmp3.nc ${ENDFILE}
      ncatted -O -h -a units,time,o,c,"${REFTIME}" -a units,time_bnds,o,c,"${REFTIME}" ${ENDFILE}
    else
#   Check dates in files for instantaneous variables
      if [[ ${TDA} -eq 01 && ${THA} -eq 00 ]]
      then
        echov "First date of instantaneous file is OK"
        cp ${FILEIN} ${FILEOUT}_tmp1.nc          
      else
        echo "Start date " ${TDA} ${THA}
        echo in "${FILEIN} "
        echo "is not correct"
        exit       
      fi
      if [[ ${TDE} -eq ${LASTDAY}  && ${THE} -eq ${EHH} ]]
      then
        echov "Last date of instantaneous file is OK"
        mv ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp3.nc
      elif  [[ ${TDE} -eq 01 && ${THE} -eq 00 ]]
      then
        (( NTM=NT-2 )) 
        echov "Last date of instantaneous file is removed"
        ncks -O -h -d time,0,${NTM} ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp3.nc 
      else
        echo "END date " ${TDE} ${THE}
        echo in "${FILEIN} "
        echo "is not correct"
        exit        
      fi
      ENDFILE=${OUTDIR}/${FILEOUT}/${FILEOUT}_${TYA}${TMA}${TDA}00-${YY}${ME}${LASTDAY}${EHH}.nc
#     transfer time from seconds in days and remove time_bnds from instantaneous fields
      echov "Modifying time values and attributes"
#      ncap2 -O -h -s "time_bnds=time_bnds/86400" -s "time_bnds(:,0)=time_bnds(:,1)" ${FILEOUT}_tmp3.nc ${ENDFILE}
#      ncatted -O -h -a units,time_bnds,o,c,"${REFTIME}" ${ENDFILE}
      ncap2 -O -h  -s "time=time/86400" ${FILEOUT}_tmp3.nc ${ENDFILE}
      ncks -O -C -h -x -v time_bnds ${ENDFILE} ${ENDFILE}
      ncatted -O -h -a units,time,o,c,"${REFTIME}" -a bounds,time,d,, ${ENDFILE}    
    fi
#   add global attributes according to CORDEX requirements 
#    echo "Add global attributes"
    ncatted -O -h -a experiment,global,a,c,"${experiment}" -a experiment_id,global,o,c,${experiment_id}  -a source,global,o,c,"${source}" ${ENDFILE}
    ncatted -O -h -a driving_experiment,global,a,c,"${driving_experiment}" -a driving_model_id,global,a,c,${driving_model_id} -a driving_model_ensemble_member,global,a,c,${driving_model_ensemble_member} -a driving_experiment_name,global,a,c,${driving_experiment_name} ${ENDFILE}
    ncatted -O -h -a institution,global,o,c,"${institution}" -a institute_id,global,a,c,${institute_id} -a model_id,global,a,c,${model_id}  -a rcm_version_id,global,a,c,${rcm_version_id} -a project_id,global,o,c,${project_id}  ${ENDFILE}
    ncatted -O -h -a CORDEX_domain,global,a,c,${CORDEX_domain} -a product,global,a,c,${product} ${ENDFILE}
    ncatted -O -h -a title,global,o,c,"${title}" -a contact,global,o,c,"${contact}" -a references,global,o,c,"${references}" ${ENDFILE}
#
#   add global attributes for own requirements
#   these attributes are not required by CORDEX archive specifications but may help to 
#   identify own simulation series
    ncatted -O -h -a btu_run_id,global,a,c,${btu_run_id} ${ENDFILE}
#    ncatted -O -h -a dwd_run_id,global,a,c,${dwd_run_id} ${ENDFILE}
#
#   change permission of final file
    chmod ${PERM} ${ENDFILE}
#
#   clean temporary files
    rm -f ${FILEOUT}_tmp?.nc
    rm ${FILEIN}

  done					  # var name loopende
#
fi                              #concatenate part
#
# create additional fields required by ESGF
#
  echon " Create additional fields for CORDEX"
# Mean wind spdeed at 10m height: SP_10M
  name1=U_10M
  name2=V_10M
  name3=SP_10M
  file1=$(ls ${OUTDIR}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
  file2=$(ls ${OUTDIR}/${name2}/${name2}_${YY}${MMA}0100*.nc)
  if [ -f ${file1} -a -f ${file2} ]
  then
    ((c1 = ${#file1}-23 )) 
    ((c2 = ${#file1}-3 ))
    DATE=`ls ${file1} |cut -c${c1}-${c2}`
    file3=${OUTDIR}/${name3}/${name3}_${DATE}.nc
    if [ ! -f ${file3} ]
    then
      echon "Create SP_10M"
      [[ -d ${OUTDIR}/${name3} ]] || mkdir  ${OUTDIR}/${name3} 
      cp ${file1} temp1.nc
      ncks -h -a -A -v ${name2} ${file2} temp1.nc
      ncap2 -h -O -s "${name3}=sqrt(${name1}^2+${name2}^2)" temp1.nc temp1.nc 
      ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
      ncatted -h -a long_name,${name3},m,c,"wind speed of 10m wind" -a standard_name,${name3},m,c,"wind_speed" ${file3}
      chmod ${PERM} ${file3}
      rm temp1.nc
    else
      echo $(basename ${file3}) "already exists" 
    fi
  else
    echo "Input Files for generating SP_10M are not available"
  fi
#
# Total downward global radiation at the surface: ASWD_S
  name1=ASWDIR_S
  name2=ASWDIFD_S
  name3=ASWD_S
  file1=$(ls ${OUTDIR}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
  file2=$(ls ${OUTDIR}/${name2}/${name2}_${YY}${MMA}0100*.nc)
  if [ -f ${file1} -a -f ${file2} ]
  then
    ((c1 = ${#file1}-23 )) 
    ((c2 = ${#file1}-3 ))
    DATE=`ls ${file1} |cut -c${c1}-${c2}`
    file3=${OUTDIR}/${name3}/${name3}_${DATE}.nc
    if [ ! -f ${file3} ]
    then
      echon "Create ASWD_S"
      [[ -d ${OUTDIR}/${name3} ]] || mkdir  ${OUTDIR}/${name3} 
      cp ${file1} temp1.nc
      ncks -h -a -A -v ${name2} ${file2} temp1.nc
      ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
      ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
      ncatted -h -a long_name,${name3},m,c,"averaged total downward sw radiation at the surface" ${file3}
      chmod ${PERM} ${file3}
      rm temp1.nc 
    else
      echo $(basename ${file3}) " already exists" 
    fi
  else
    echo "Input Files for generating ASWD_S are not available"
  fi
#
# upward solar radiation at TOA: ASOU_T
  name1=ASOD_T
  name2=ASOB_T
  name3=ASOU_T
  file1=$(ls ${OUTDIR}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
  file2=$(ls ${OUTDIR}/${name2}/${name2}_${YY}${MMA}0100*.nc)
  if [ -f ${file1} -a -f ${file2} ]
  then
    ((c1 = ${#file1}-23 )) 
    ((c2 = ${#file1}-3 ))
    DATE=`ls ${file1} |cut -c${c1}-${c2}`
    file3=${OUTDIR}/${name3}/${name3}_${DATE}.nc
    if [ ! -f ${file3} ]
    then
      echon "Create ASOU_T"
      [[ -d ${OUTDIR}/${name3} ]] || mkdir  ${OUTDIR}/${name3} 
      cp ${file1} temp1.nc
      ncks -h -a -A -v ${name2} ${file2} temp1.nc
      ncap2 -h -O -s "${name3}=${name1}-${name2}" temp1.nc temp1.nc 
      ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
      ncatted -h -a long_name,${name3},m,c,"averaged solar upward radiataion at top" ${file3}
      chmod ${PERM} ${file3}
      rm temp1.nc 
    else
      echo $(basename ${file3}) " already exists" 
    fi
  else
    echo "Input Files for generating ASOU_T are not available"
  fi
#
# Total runoff: RUNOFF_T
  name1=RUNOFF_S
  name2=RUNOFF_G
  name3=RUNOFF_T
  file1=$(ls ${OUTDIR}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
  file2=$(ls ${OUTDIR}/${name2}/${name2}_${YY}${MMA}0100*.nc)
  if [ -f ${file1} -a -f ${file2} ]
  then
    ((c1 = ${#file1}-23 )) 
    ((c2 = ${#file1}-3 ))
    DATE=`ls ${file1} |cut -c${c1}-${c2}`
    file3=${OUTDIR}/${name3}/${name3}_${DATE}.nc
    if [ ! -f ${file3} ]
    then
      echon "Create RUNOFF_T"
      [[ -d ${OUTDIR}/${name3} ]] || mkdir  ${OUTDIR}/${name3} 
      cp ${file1} temp1.nc
      ncks -h -a -A -v ${name2} ${file2} temp1.nc
      ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
      ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
      ncatted -h -a long_name,${name3},m,c,"total runoff" -a standard_name,${name3},m,c,"total_runoff_amount" ${file3}
      chmod ${PERM} ${file3}
      rm temp1.nc 
    else
      echo $(basename ${file3}) " already exists" 
    fi
  else
    echo "Input Files for generating RUNOFF_T are not available"
  fi
#
# Total convective precipitation: PREC_CON
  name1=RAIN_CON
  name2=SNOW_CON
  name3=PREC_CON
  file1=$(ls ${OUTDIR}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
  file2=$(ls ${OUTDIR}/${name2}/${name2}_${YY}${MMA}0100*.nc)
  if [ -f ${file1} -a -f ${file2} ]
  then
    ((c1 = ${#file1}-23 )) 
    ((c2 = ${#file1}-3 ))
    DATE=`ls ${file1} |cut -c${c1}-${c2}`
    file3=${OUTDIR}/${name3}/${name3}_${DATE}.nc
    if [ ! -f ${file3} ]
    then
      echon "Create PREC_CON"
      [[ -d ${OUTDIR}/${name3} ]] || mkdir  ${OUTDIR}/${name3} 
      cp ${file1} temp1.nc
      ncks -h -a -A -v ${name2} ${file2} temp1.nc
      ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
      ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
      ncatted -h -a long_name,${name3},m,c,"convective precipitation" -a standard_name,${name3},m,c,"convective_precipitation_amount" ${file3}
      chmod ${PERM} ${file3}
      rm temp1.nc 
    else
      echo $(basename ${file3}) " already exists" 
    fi
  else
    echo "Input Files for generating PREC_CON are not available"
  fi
#
# Total snow: TOT_SNOW
  name1=SNOW_GSP
  name2=SNOW_CON
  name3=TOT_SNOW
  file1=$(ls ${OUTDIR}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
  file2=$(ls ${OUTDIR}/${name2}/${name2}_${YY}${MMA}0100*.nc)
  if [ -f ${file1} -a -f ${file2} ]
  then
   ((c1 = ${#file1}-23 )) 
   ((c2 = ${#file1}-3 ))
    DATE=`ls ${file1} |cut -c${c1}-${c2}`
    file3=${OUTDIR}/${name3}/${name3}_${DATE}.nc
    if [ ! -f ${file3} ]
    then
      echon "Create TOT_SNOW"
      [[ -d ${OUTDIR}/${name3} ]] || mkdir  ${OUTDIR}/${name3} 
      cp ${file1} temp1.nc
      ncks -h -a -A -v ${name2} ${file2} temp1.nc
      ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
      ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
      ncatted -h -a long_name,${name3},m,c,"total snowfall" -a standard_name,${name3},m,c,"total_snowfall_amount" ${file3}
      chmod ${PERM} ${file3}
      rm temp1.nc 
    else
      echo $(basename ${file3}) " already exists" 
    fi
  else
    echo "Input Files for generating TOT_SNOW are not available"
  fi
#
# cloud condensed water content TQW
  name1=TQC
  name2=TQI
  name3=TQW
  file1=$(ls ${OUTDIR}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
  file2=$(ls ${OUTDIR}/${name2}/${name2}_${YY}${MMA}0100*.nc)
  if [ -f ${file1} -a -f ${file2} ]
  then
    ((c1 = ${#file1}-23 )) 
    ((c2 = ${#file1}-3 ))
    DATE=`ls ${file1} |cut -c${c1}-${c2}`
    file3=${OUTDIR}/${name3}/${name3}_${DATE}.nc
    if [ ! -f ${file3} ]
    then
      echon "Create TQW"
      [[ -d ${OUTDIR}/${name3} ]] || mkdir  ${OUTDIR}/${name3} 
      cp ${file1} temp1.nc
      ncks -h -a -A -v ${name2} ${file2} temp1.nc
      ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
      ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
      ncatted -h -a long_name,${name3},m,c,"vertiacl integrated cloud condensed water" -a standard_name,${name3},m,c,"atmosphere_cloud_condensed_water_content" ${file3}
      chmod ${PERM} ${file3}
      rm temp1.nc 
    else
      echo $(basename ${file3}) " already exists" 
    fi
  else
    echo "Input Files for generating TQW are not available"
  fi
#
  (( YY=YY+1 ))
done                                      # year loopend
# Remove monthly subdirs YYYY_MM
#YY=${YYA}
#MM=${MMA}
#while [ ${YY}${MM} -le ${YYE}${MME} ]		# year loop
#do
#  Remove the input files if you are shure that they are no longer needed:
#  Files with monthly time series of single variables generated by subchain-script "post.job"
#
#  rm -rf ${YY}_${MM}
 # (( MM=MM+1 ))
  #if [ ${MM} -gt 12 ]
  #then
  #  (( YY=YY+1 ))
   # MM=1
  #fi
#done

exit

