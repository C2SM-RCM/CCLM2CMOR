#!/bin/ksh

#-------------------------------------------------------------------------
# Concatenats monthly time series files produced by CCLM chain script post
# to annual file for a given time period of years 
# 
# K. Keuler, Matthias Göbel 
#latest version: 15.09.2017
#-------------------------------------------------------------------------

typeset -Z2 MM MA ME MP MMA MME DHH EHH
typeset -Z4 YY YYA YYE YP


#---------------------------------------------------------------------
MMA=01
MME=12


# create subdirectory for full time series
[[ -d ${OUTDIR2} ]] || mkdir -p  ${OUTDIR2}
#Create and change to WORKDIR
[[ -d ${WORKDIR} ]] || mkdir -p  ${WORKDIR} 
cd ${WORKDIR}
#################################################
YY=$YYA

#copy constant variables
for constVar in ${const_list}
do 
  if [ ! -f ${OUTDIR2}/${constVar}/${constVar}.nc ] || ${overwrite} 
  then
    if [ -f ${INDIR2}/${constVar}.nc ]
    then
      echon "Copy constant variable ${constVar}.nc to output folder"
      [[ -d ${OUTDIR2}/${constVar} ]] || mkdir ${OUTDIR2}/${constVar}
      cp ${INDIR2}/${constVar}.nc ${OUTDIR2}/${constVar}/
    else
      echo "Required constant variable file ${constVar}.nc is not in input folder ${INDIR2}! Skipping this variable..."
    fi
  fi
done


while [ ${YY} -le ${YYE} ]      # year loop
do
  echo ""
  echo "####################"
  echo ${YY}
  echo "####################"
  DATE1=$(date +%s)
	
  if ! ${proc_all} 
  then
    FILES=${proc_list} 
  else
    FILES=$(ls ${INDIR2}/${YY}_${MMA}/*_ts.nc)
  fi
  
  #check if directories for all months exist
  MM=${MMA}
  while [ ${MM} -le ${MME} ]
  do 
    if [ ! -d ${INDIR2}/${YY}_${MM} ]
    then
      echo "Directory ${INDIR2}/${YY}_${MM} does not exist! Skipping this year..."
      (( YY=YY+1 ))
      continue 2
    fi
    (( MM=MM+1 ))
  done

  #
  if [ ${LFILE} -ne 2 ]
  then
  # concatenate monthly files to annual file
    for FILE in ${FILES}        # var name loop
    do
      FILEIN=$(basename ${FILE})
      
      if  ${proc_all}  
      then
        (( c2 = ${#FILEIN}-6 ))
        FILEOUT=$(echo ${FILEIN} | cut -c1-${c2}) # cut off "_ts.nc"
      else
        FILEOUT=${FILE} 
      fi
      
      #cut off pressure level information from FILEOUT to find it in acc_list or inst_list
      if [ "${FILEOUT: -1}" == "p" ]
      then
        (( c2 = ${#FILEOUT}-4 ))
        varname=$(echo ${FILEOUT} | cut -c1-${c2})
      else
        varname=${FILEOUT}
      fi

      #process variable if in proc_list or if proc_all is set
      if [[ ${proc_list} =~ (^|[[:space:]])${varname}($|[[:space:]]) ]] || ${proc_all}
      then
        if ls ${OUTDIR2}/${FILEOUT}/${FILEOUT}_${YY}* 1> /dev/null 2>&1 
        then
          if ${overwrite} 
          then    
            echon ""
            echon ${FILEOUT}
            echon "File for variable ${FILEOUT} and year ${YY} already exists. Overwriting..."
          else
            echov ""
            echov "File for variable ${FILEOUT} and year ${YY} already exists. Skipping..."
            continue
          fi
        else
          echon ""
          echon ${FILEOUT}
        fi

      else
        continue
      fi
      


      # determine if current variable is an accumulated quantity
      LACCU=0
      for NAME in ${accu_list}
      do
        if [ ${NAME} == ${varname} ]
        then
          LACCU=1
          echon "${varname} is accumulated variable"
        fi
      done
      
      if [ LACCU -eq 0 ]
      then
        LACCU=1
        for NAME in ${inst_list}
        do
          if [ ${NAME} == ${varname} ]
          then
            LACCU=0
            echon "${varname} is an instantaneous variable"
          fi
        done
        if [ LACCU -eq 1 ]
        then
          echo "Error for ${varname}: neither contained in accu_list nor in inst_list! Skipping..."
          continue
        fi
      fi
      
      

      FILELIST=""
      MA=${MMA}
      ME=${MME}
      MM=${MA}
      while [ ${MM} -le ${ME} ]
      do 
        if [ ! -f ${INDIR2}/${YY}_${MM}/${FILEOUT}_ts.nc ]
        then
          echo "File ${INDIR2}/${YY}_${MM}/${FILEOUT}_ts.nc does not exist! Skipping this variable..."
          continue 2
        fi
        FILELIST="$(echo ${FILELIST}) $(ls ${INDIR2}/${YY}_${MM}/${FILEOUT}_ts.nc)"
        (( MM=MM+1 ))
      done
      
      echon "Concatenate files"
      echov "${FILELIST}"
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
      echov "First date: ${VT[0]} "
      echov "Last date: ${VT[-1]} "
      echov "Number of timesteps: $NT"
      echov "Time step: $DHH h"
      echov "New reference time: ${REFTIME}"
      
      #create output directory
      [[ -d ${OUTDIR2}/${FILEOUT} ]] || mkdir ${OUTDIR2}/${FILEOUT}
      
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
          echo "Error: Start date  ${TDA} ${THA}"
          echo in "${FILEIN} "
          echo "is not correct! Exiting..."
          continue
        fi
        if [[ ${TDE} -ge 28 && ${THE} -eq ${EHH} ]]
        then
          YP=${YY}
          (( MP=TME+1 ))
          if [ ${MP} -gt 12 ]
          then
            MP=01
            (( YP=YP+1 ))
          fi
          FILENEXT=${INDIR2}/${YP}_${MP}/${FILEOUT}_ts.nc
          if [ -f ${FILENEXT} ]
          then
            echov "Append first date from next month's file to the end of current month"
            ncks -O -h -d time,0 ${FILENEXT} ${FILEOUT}_tmp2.nc
            ncrcat -O -h  ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp2.nc ${FILEOUT}_tmp3.nc
          else
            echo "Try to append first date from next month's file but"
            echo ${FILENEXT} does not exist
            continue
          fi
        elif [[ ${TDE} -eq 01 &&  ${THE} -eq 00 ]]
        then
          (( MP=TME ))
          (( YP=TYE ))
          echov "Last timestep in tmp3-File is OK"
          mv ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp3.nc
        else
          echo "END date  ${TDE} ${THE}"
          echo in "${FILEIN} "
          echo "is not correct"
          continue
        fi
        ENDFILE=${OUTDIR2}/${FILEOUT}/${FILEOUT}_${TYA}${TMA}${TDA}00-${YP}${MP}0100.nc
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
          continue       
        fi
        if [[ ${TDE} -ge 28  && ${THE} -eq ${EHH} ]]
        then
          echov "Last date of instantaneous file is OK"
          mv ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp3.nc
        elif  [[ ${TDE} -eq 01 && ${THE} -eq 00 ]]
        then
          (( NTM=NT-2 )) 
          echov "Last date of instantaneous file is removed"
          ncks -O -h -d time,0,${NTM} ${FILEOUT}_tmp1.nc ${FILEOUT}_tmp3.nc 
          #change TDE
          VT=($(cdo -s showtimestamp ${FILEOUT}_tmp3.nc))
          TDE=$(echo ${VT} | cut -c9-10)
        else
          echo "END date " ${TDE} ${THE}
          echo in "${FILEIN} "
          echo "is not correct"
          echo ${EHH}
          continue       
        fi
        ENDFILE=${OUTDIR2}/${FILEOUT}/${FILEOUT}_${TYA}${TMA}${TDA}00-${YY}${ME}${TDE}${EHH}.nc
  #     transfer time from seconds in days and remove time_bnds from instantaneous fields
        echov "Modifying time values and attributes"
        ncap2 -O -h  -s "time=time/86400" ${FILEOUT}_tmp3.nc ${ENDFILE}
        ncks -O -C -h -x -v time_bnds ${ENDFILE} ${ENDFILE}
        ncatted -O -h -a units,time,o,c,"${REFTIME}" -a bounds,time,d,, ${ENDFILE}    
      fi


  #   change permission of final file
      chmod ${PERM} ${ENDFILE}
  #
  #   clean temporary files
      rm -f ${FILEOUT}_tmp?.nc
      rm ${FILEIN}

    done                    # var name loopende
#
  fi                              #concatenate part



  #
  # create additional fields required by ESGF
  #
  
  if [ ${LFILE} -ne 1 ]
  then

    echon ""
    echon " Create additional fields for CORDEX"
  # Mean wind spdeed at 10m height: SP_10M
    name1=U_10M
    name2=V_10M
    name3=SP_10M
    file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
    file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
    if [ -f ${file1} -a -f ${file2} ]
    then
      ((c1 = ${#file1}-23 )) 
      ((c2 = ${#file1}-3 ))
      DATE=`ls ${file1} |cut -c${c1}-${c2}`
      file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
      if [ ! -f ${file3} ] ||  ${overwrite}
      then
        echon "Create SP_10M"
        [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
        cp ${file1} temp1.nc
        ncks -h -a -A -v ${name2} ${file2} temp1.nc
        ncap2 -h -O -s "${name3}=sqrt(${name1}^2+${name2}^2)" temp1.nc temp1.nc 
        ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
        ncatted -h -a long_name,${name3},m,c,"wind speed of 10m wind" -a standard_name,${name3},m,c,"wind_speed" ${file3}
        chmod ${PERM} ${file3}
        rm temp1.nc
      else
        echov "$(basename ${file3})  already exists. Use option -o to overwrite. Skipping..."
      fi
    else
      echo "Input Files for generating SP_10M are not available"
    fi
  #
  # Total downward global radiation at the surface: ASWD_S
    name1=ASWDIR_S
    name2=ASWDIFD_S
    name3=ASWD_S
    file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
    file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
    if [ -f ${file1} -a -f ${file2} ]
    then
      ((c1 = ${#file1}-23 )) 
      ((c2 = ${#file1}-3 ))
      DATE=`ls ${file1} |cut -c${c1}-${c2}`
      file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
      if [ ! -f ${file3} ] ||  ${overwrite}
      then
        echon "Create ASWD_S"
        [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
        cp ${file1} temp1.nc
        ncks -h -a -A -v ${name2} ${file2} temp1.nc
        ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
        ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
        ncatted -h -a long_name,${name3},m,c,"averaged total downward sw radiation at the surface" ${file3}
        chmod ${PERM} ${file3}
        rm temp1.nc 
      else
        echov "$(basename ${file3})  already exists. Use option -o to overwrite. Skipping..." 
      fi
    else
      echo "Input Files for generating ASWD_S are not available"
    fi
  #
  # upward solar radiation at TOA: ASOU_T
    name1=ASOD_T
    name2=ASOB_T
    name3=ASOU_T
    file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
    file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
    if [ -f ${file1} -a -f ${file2} ]
    then
      ((c1 = ${#file1}-23 )) 
      ((c2 = ${#file1}-3 ))
      DATE=`ls ${file1} |cut -c${c1}-${c2}`
      file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
      if [ ! -f ${file3} ] ||  ${overwrite}
      then
        echon "Create ASOU_T"
        [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
        cp ${file1} temp1.nc
        ncks -h -a -A -v ${name2} ${file2} temp1.nc
        ncap2 -h -O -s "${name3}=${name1}-${name2}" temp1.nc temp1.nc 
        ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
        ncatted -h -a long_name,${name3},m,c,"averaged solar upward radiataion at top" ${file3}
        chmod ${PERM} ${file3}
        rm temp1.nc 
      else
        echov "$(basename ${file3})  already exists. Use option -o to overwrite. Skipping..." 
      fi
    else
      echo "Input Files for generating ASOU_T are not available"
    fi
  #
  # Total runoff: RUNOFF_T
    name1=RUNOFF_S
    name2=RUNOFF_G
    name3=RUNOFF_T
    file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
    file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
    if [ -f ${file1} -a -f ${file2} ]
    then
      ((c1 = ${#file1}-23 )) 
      ((c2 = ${#file1}-3 ))
      DATE=`ls ${file1} |cut -c${c1}-${c2}`
      file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
      if [ ! -f ${file3} ] ||  ${overwrite}
      then
        echon "Create RUNOFF_T"
        [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
        cp ${file1} temp1.nc
        ncks -h -a -A -v ${name2} ${file2} temp1.nc
        ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
        ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
        ncatted -h -a long_name,${name3},m,c,"total runoff" -a standard_name,${name3},m,c,"total_runoff_amount" ${file3}
        chmod ${PERM} ${file3}
        rm temp1.nc 
      else
        echov "$(basename ${file3}) already exists. Use option -o to overwrite. Skipping..." 
      fi
    else
      echo "Input Files for generating RUNOFF_T are not available"
    fi
  #
  # Total convective precipitation: PREC_CON
    name1=RAIN_CON
    name2=SNOW_CON
    name3=PREC_CON
    file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
    file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
    if [ -f ${file1} -a -f ${file2} ]
    then
      ((c1 = ${#file1}-23 )) 
      ((c2 = ${#file1}-3 ))
      DATE=`ls ${file1} |cut -c${c1}-${c2}`
      file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
      if [ ! -f ${file3} ] ||  ${overwrite}
      then
        echon "Create PREC_CON"
        [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
        cp ${file1} temp1.nc
        ncks -h -a -A -v ${name2} ${file2} temp1.nc
        ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
        ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
        ncatted -h -a long_name,${name3},m,c,"convective precipitation" -a standard_name,${name3},m,c,"convective_precipitation_amount" ${file3}
        chmod ${PERM} ${file3}
        rm temp1.nc 
      else
        echov "$(basename ${file3}) already exists. Use option -o to overwrite. Skipping..." 
      fi
    else
      echo "Input Files for generating PREC_CON are not available"
    fi
  #
  # Total snow: TOT_SNOW
    name1=SNOW_GSP
    name2=SNOW_CON
    name3=TOT_SNOW
    file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
    file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
    if [ -f ${file1} -a -f ${file2} ]
    then
     ((c1 = ${#file1}-23 )) 
     ((c2 = ${#file1}-3 ))
      DATE=`ls ${file1} |cut -c${c1}-${c2}`
      file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
      if [ ! -f ${file3} ] ||  ${overwrite}
      then
        echon "Create TOT_SNOW"
        [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
        cp ${file1} temp1.nc
        ncks -h -a -A -v ${name2} ${file2} temp1.nc
        ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
        ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
        ncatted -h -a long_name,${name3},m,c,"total snowfall" -a standard_name,${name3},m,c,"total_snowfall_amount" ${file3}
        chmod ${PERM} ${file3}
        rm temp1.nc 
      else
        echov "$(basename ${file3}) already exists. Use option -o to overwrite. Skipping..." 
      fi
    else
      echo "Input Files for generating TOT_SNOW are not available"
    fi
  #
  # cloud condensed water content TQW
    name1=TQC
    name2=TQI
    name3=TQW
    file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
    file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
    if [ -f ${file1} -a -f ${file2} ]
    then
      ((c1 = ${#file1}-23 )) 
      ((c2 = ${#file1}-3 ))
      DATE=`ls ${file1} |cut -c${c1}-${c2}`
      file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
      if [ ! -f ${file3} ] ||  ${overwrite}
      then
        echon "Create TQW"
        [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
        cp ${file1} temp1.nc
        ncks -h -a -A -v ${name2} ${file2} temp1.nc
        ncap2 -h -O -s "${name3}=${name1}+${name2}" temp1.nc temp1.nc 
        ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1.nc ${file3}
        ncatted -h -a long_name,${name3},m,c,"vertiacl integrated cloud condensed water" -a standard_name,${name3},m,c,"atmosphere_cloud_condensed_water_content" ${file3}
        chmod ${PERM} ${file3}
        rm temp1.nc 
      else
        echov "$(basename ${file3}) already exists. Use option -o to overwrite. Skipping..."
      fi
    else
      echo "Input Files for generating TQW are not available"
    fi
  #
  fi
  (( YY=YY+1 ))
  DATE2=$(date +%s)
	SEC_TOTAL=$(python -c "print(${DATE2}-${DATE1})")
	echon "Time for postprocessing: ${SEC_TOTAL} s"
  done                                      # year loopend



  # Remove monthly subdirs YYYY_MM
  #YY=${YYA}
  #MM=${MMA}
  #while [ ${YY}${MM} -le ${YYE}${MME} ]      # year loop
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


