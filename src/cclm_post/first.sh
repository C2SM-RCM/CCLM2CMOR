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
  if [ ! -f lffd${CURRENT_DATE}*[!cpz].nc ]
  then
    echo "No files found for variable $1 for current month in  ${INDIR1}/${CURRDIR}/$2. Skipping month..." 
  elif [ ! -f ${OUTDIR1}/${YYYY_MM}/$1_ts.nc ] ||  ${overwrite}
  then
    echon "Building time series for variable $1"
    FILES="$(ls lffd${CURRENT_DATE}*[!cpz].nc )"
    
    if [ ${MM} -eq 12 ]
    then  
      FILES="$(echo ${FILES}) $(ls lffd${NEXT_DATE}0100.nc )"
    fi
    ncrcat -h -O -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v $1 ${FILES} ${OUTDIR1}/${YYYY_MM}/$1_ts.nc
    ncks -h -A -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v lon,lat,rotated_pole ${INDIR1}/${CURRDIR}/$2/lffd${CURRENT_DATE}0100.nc ${OUTDIR1}/${YYYY_MM}/$1_ts.nc
  else
    echov "Time series for variable $1 already exists. Skipping..."
  fi
}


function timeseriesp {  # building a time series for a given quantity on pressure levels
  NPLEV=0
  cd ${INDIR1}/${CURRDIR}/$2
  if [ ! -f lffd${CURRENT_DATE}*p.nc ]
  then
    echo "No files found for variable $1 for current month in  ${INDIR1}/${CURRDIR}/$2. Skipping month..."
  else
  while [ ${NPLEV} -lt ${#PLEVS[@]} ]
  do
    PASCAL=$(python -c "print(${PLEVS[$NPLEV]} * 100.)")
    PLEV=$(python -c "print(int(${PLEVS[$NPLEV]}))")
    FILES="$(ls lffd${CURRENT_DATE}*p.nc )"
    if [ ${MM} -eq 12 ]
    then  
      FILES="$(echo ${FILES}) $(ls lffd${NEXT_DATE}0100p.nc )"
    fi

    if [ ! -f ${OUTDIR1}/${YYYY_MM}/${1}${PLEV}p_ts.nc ] ||  ${overwrite}
    then
      echon "Building time series at pressure level ${PLEV} hPa for variable $1"
      ncrcat -h -O -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -d pressure,${PASCAL},${PASCAL} -v $1 ${FILES} ${OUTDIR1}/${YYYY_MM}/${1}${PLEV}p_ts.nc
      ncks -h -A -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v lon,lat,rotated_pole ${INDIR1}/${CURRDIR}/$2/lffd${CURRENT_DATE}0100p.nc ${OUTDIR1}/${YYYY_MM}/${1}${PLEV}p_ts.nc
    else
      echov "Time series for variable $1 at pressure level ${PLEV}  already exists. Skipping..."
    fi
    let "NPLEV = NPLEV + 1"

  done
  fi
  }


function timeseriesz {
  NZLEV=0
  cd ${INDIR1}/${CURRDIR}/$2
  if [ ! -f lffd${CURRENT_DATE}*z.nc ]
  then
    echo "No files for current month found. Skipping month..."
  else
  
  while [ ${NZLEV} -lt ${#ZLEVS[@]} ]
  do
    ZLEV=$(python -c "print(int(${ZLEVS[$NZLEV]}))")
    FILES="$(ls lffd${CURRENT_DATE}*z.nc )"
    if [ ${MM} -eq 12 ]
    then  
      FILES="$(echo ${FILES}) $(ls lffd${NEXT_DATE}0100z.nc )"
    fi

    if [ ! -f ${OUTDIR1}/${YYYY_MM}/${1}${ZLEV}z_ts.nc ] ||  ${overwrite}
    then
      echon "Building time series at height level ${ZLEV} m for variable $1"
      ncrcat -h -O -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -d height,${ZLEV}.,${ZLEV}. -v $1 ${FILES} ${OUTDIR1}/${YYYY_MM}/${1}${ZLEV}z_ts.nc
      ncks -h -A -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v lon,lat,rotated_pole ${INDIR1}/${CURRDIR}/$2/lffd${CURRENT_DATE}0100z.nc ${OUTDIR1}/${YYYY_MM}/${1}${ZLEV}z_ts.nc
    else
      echov "Time series for variable $1 at height level ${ZLEV} m  already exists. Skipping..."
    fi
    let "NZLEV = NZLEV + 1"
  done
  fi
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

  skip=false
  if [ ! -d ${INDIR1}/${YYYY} ]
  then
    if ${batch}
    then
      echo "Cannot find input directory for year ${YYYY} in ${INDIR1}. Skipping..."
      skip=true
    else
      echo "Cannot find input directory for year ${YYYY}. Transfering from ${ARCHDIR}..."
      if [ -d ${ARCHDIR}/*${YYYY} ] 
      then
        mv ${ARCHDIR}/*${YYYY} ${INDIR1}
      elif [ -f ${ARCHDIR}/*${YYYY}.tar ]
      then
        tar -xf ${ARCHDIR}/*${YYYY}.tar -C ${INDIR1}
      else
        echo "Cannot find .tar file or extracted archive in archive directory! Exiting..."
        skip=true 
      fi      
    fi
  fi
  # step ahead in time
  MMint=$(python -c "print(int("${MMint}")+1)")
  if [ ${MMint} -ge 13 ]
  then
    MMint=1
    YYYY_next=$(python -c "print(int("${YYYY}")+1)")
  else
    YYYY_next=${YYYY}
  fi

  if [ ${MMint} -le 9 ]
  then
    MM_next=0${MMint}
  else
    MM_next=${MMint}
  fi

  NEXT_DATE=${YYYY_next}${MM_next}
  NEXT_DATE2=${YYYY_next}_${MM_next}

  if ! ${skip}
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
      ncks -h -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} ${INDIR1}/${YYYY}/output/out01/lffd*c.nc ${WORKDIR}/${EXPPATH}/cclm_const.nc
    fi
  
    #start timing
    DATE_START=$(date +%s)

    #process constant variables
    constVar FR_LAND
    constVar HSURF
    constDone=true

    #build time series for selected variables
    source ${SRCDIR_POST}/timeseries.sh

    #stop timing and print information
    DATE2=$(date +%s)
    SEC_TOTAL=$(python -c "print(${DATE2}-${DATE_START})")
    echon "Time for postprocessing: ${SEC_TOTAL} s"
  
  fi

  if [ ! "$(ls -A ${OUTDIR1}/${YYYY_MM})" ] 
  then
    rmdir ${OUTDIR1}/${YYYY_MM}
  fi

  CURRENT_DATE=${NEXT_DATE}
  YYYY=${YYYY_next}
  MM=${MM_next}
done
