#!/bin/bash

#
# Burkhardt Rockel / Helmholtz-Zentrum Geesthacht, modified by Matthias Göbel / ETH Zürich
# Initial Version: 2009/09/02
# Latest Version:  2017/09/15 
#


#function to process constant variables
function constVar {
  if [ ! -f ${OUTDIR1}/$1.nc ] ||  ${overwrite}
  then
    echon "Building file for constant variable $1"
    ncks -h -A -v $1,rotated_pole ${WORKDIR}/${EXPPATH}/cclm_const.nc ${OUTDIR1}/$1.nc
  else
    echov "File for constant variable $1 already exists. Skipping..."
  fi
  }

#... functions for building time series
function timeseries {  # building a time series for a given quantity
  cd ${INDIR1}/${CURRDIR}/$2
  if [ ! -f ${OUTDIR1}/${YYYY_MM}/$1_ts.nc ] ||  ${overwrite}
  then
    echon "Building time series for variable $1"
    ncrcat -h -O -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v $1 lffd${CURRENT_DATE}*[!cpz].nc ${OUTDIR1}/${YYYY_MM}/$1_ts.nc
    ncks -h -A -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v lon,lat,rotated_pole ${INDIR1}/${CURRDIR}/$2/lffd${CURRENT_DATE}0100.nc ${OUTDIR1}/${YYYY_MM}/$1_ts.nc
  else
    echov "Time series for variable $1 already exists. Skipping..."
  fi
}


function timeseriesp {  # building a time series for a given quantity on pressure levels
  NPLEV=0

  while [ ${NPLEV} -lt ${#PLEVS[@]} ]
  do
    PASCAL=$(python -c "print(${PLEVS[$NPLEV]} * 100.)")
    PLEV=$(python -c "print(int(${PLEVS[$NPLEV]}))")
    cd ${INDIR1}/${CURRDIR}/$2

    if [ ! -f ${OUTDIR1}/${YYYY_MM}/${1}${PLEV}p_ts.nc ] ||  ${overwrite}
    then
      echon "Building time series at pressure level ${PLEV} hPa for variable $1"
      ncrcat -h -O -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -d pressure,${PASCAL},${PASCAL} -v $1 lffd${CURRENT_DATE}*p.nc ${OUTDIR1}/${YYYY_MM}/${1}${PLEV}p_ts.nc
      ncks -h -A -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v lon,lat,rotated_pole ${INDIR1}/${CURRDIR}/$2/lffd${CURRENT_DATE}0100p.nc ${OUTDIR1}/${YYYY_MM}/${1}${PLEV}p_ts.nc
    else
      echov "Time series for variable $1 at pressure level ${PLEV}  already exists. Skipping..."
    fi
    let "NPLEV = NPLEV + 1"

  done
  }


function timeseriesz {
  NZLEV=1
  while [ ${NZLEV} -le ${#ZLEVS[@]} ]
  do
    ZLEV=$(python -c "print(int(${ZLEVS[$NZLEV]}))")
    cd ${INDIR1}/${CURRDIR}/$2

    if [ ! -f ${OUTDIR1}/${YYYY_MM}/${1}${ZLEV}z_ts.nc ] ||  ${overwrite}
    then
      echon "Building time series at height level ${ZLEV} m for variable $1"
      ncrcat -h -O -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -d altitude,${ZLEV}.,${ZLEV}. -v $1 lffd${CURRENT_DATE}*z.nc ${OUTDIR1}/${YYYY_MM}/${1}${ZLEV}z_ts.nc
      ncks -h -A -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v lon,lat,rotated_pole ${INDIR1}/${CURRDIR}/$2/lffd${CURRENT_DATE}0100z.nc ${OUTDIR1}/${YYYY_MM}/${1}${ZLEV}z_ts.nc
    else
      echov "Time series for variable $1 at height level ${ZLEV} m  already exists. Skipping..."
    fi
    let "NZLEV = NZLEV + 1"
  done
  }

###################################################

if [ ! -d ${WORKDIR}/${EXPPATH} ]
then
  mkdir -p ${WORKDIR}/${EXPPATH}
fi




if [ ! -d ${INDIR1} ]
then
  mkdir -p ${INDIR1}
fi

YYYY=$(echo ${CURRENT_DATE} | cut -c1-4)
MM=$(echo ${CURRENT_DATE} | cut -c5-6)
MMint=${MM}
if [ $(echo ${MM} | cut -c1) -eq 0 ]
then
  MMint=$(echo ${MMint} | cut -c2  )
fi



#################################################
# Post-processing loop
#################################################


#... set number of boundary lines to be cut off in the time series data
let "IESPONGE = ${IE_TOT} - NBOUNDCUT - 1"
let "JESPONGE = ${JE_TOT} - NBOUNDCUT - 1"



while [ ${CURRENT_DATE} -le ${STOP_DATE} ]
do
  YYYY_MM=${YYYY}_${MM}
  CURRDIR=${YYYY}/output
  echon "################################"
  echon "# Processing time ${YYYY_MM}"
  echon "################################"

  if [ -d ${INDIR1}/${YYYY} ]
  then

    if [ ! -d ${OUTDIR1}/${YYYY_MM} ]
    then
      mkdir -p ${OUTDIR1}/${YYYY_MM}
    fi

    DATE_START=$(date +%s)
    DATE1=${DATE_START}

    ##################################################################################################
    # build time series
    ##################################################################################################

    export IGNORE_ATT_COORDINATES=1  # setting for better rotated coordinate handling in CDO



    #... cut of the boundary lines from the constant data file and copy it
    if [ ! -f ${WORKDIR}/${EXPPATH}/cclm_const.nc ]
    then
      echon "Copy constant file"
      ncks -h -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} ${INDIR1}/${YYYY}/output/out01/lffd${SIM_START}c.nc ${WORKDIR}/${EXPPATH}/cclm_const.nc
    fi
    
    #start timing
    DATE_START=$(date +%s)

    #process constant variables
    constVar FR_LAND
    constVar HSURF
    constDone=true

    # --- build time series for selected variables
    cd ${SRCDIR}
    source ./jobf.sh

    #stop timing and print information
    DATE2=$(date +%s)
    SEC_TOTAL=$(python -c "print(${DATE2}-${DATE_START})")
    echon "Time for postprocessing: ${SEC_TOTAL} s"
    
  else
    echo "Cannot find input directory for year ${YYYY}. Skipping..."
    #tar -xf ${ARCHDIR}/*${YYYY}.tar -C ${INDIR1}
  fi
  # step ahead in time
  MMint=$(python -c "print(int("${MMint}")+1)")
  if [ ${MMint} -ge 13 ]
  then
    MMint=1
    YYYY=$(python -c "print(int("${YYYY}")+1)")
  fi

  if [ ${MMint} -le 9 ]
  then
    MM=0${MMint}
  else
    MM=${MMint}
  fi

  CURRENT_DATE=${YYYY}${MM}

done
