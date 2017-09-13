#!/bin/ksh
#-------------------------------------------------------------------------
# Concatenats monthly time series files produced by CCLM chain script post
# to annual file for a given time period of years and creates additional 
# fields required by CORDEX
# 
# K. Keuler, Matthias Göbel 
#latest version: 15.09.2017
#-------------------------------------------------------------------------

typeset -Z2 MM MA ME MP MMA MME DHH EHH
typeset -Z4 YY YYA YYE YP


#---------------------------------------------------------------------
MMA=01 #first month of each yearly time-series
MME=12 #last month of each yearly time-series
PERM=755 #Permission settings for output files

#variables
# all CCLM variables representing a time interval (min,max,average, accumulated)
accu_list="AEVAP_S ALHFL_BS ALHFL_PL ALHFL_S ALWD_S ALWU_S APAB_S ASHFL_S ASOB_S ASOB_T ASOD_T ASWDIFD_S ASWDIFU_S ASWDIR_S ATHB_S ATHB_T AUMFL_S AUSTRSSO AVDISSSO AVMFL_S AVSTRSSO DURSUN DURSUN_M DURSUN_R GRAU_GSP HAIL_GSP RAIN_CON RAIN_GSP RUNOFF_G RUNOFF_S SNOW_CON SNOW_GSP SNOW_MELT T_2M_AV TD_2M_AV TDIV_HUM TMAX_2M TMIN_2M TOT_PREC U_10M_AV V_10M_AV VABSMX_10M VGUST_CON VGUST_DYN VMAX_10M"
  
#all instantaneous variables
inst_list="AER_BC AER_DUST AER_ORG AER_SO4 AER_SS ALB_DIF ALB_DRY ALB_RAD ALB_SAT BAS_CON BRN C_T_LK CAPE_3KM CAPE_CON CAPE_ML CAPE_MU CEILING CIN_ML CIN_MU CLC CLC_CON CLC_SGS CLCH CLCL CLCM CLCT CLCT_MOD CLDEPTH CLW_CON DBZ DBZ_850 DBZ_CMAX DD_ANAI DEPTH_LK DP_BS_LK DPSDT DQC_CON DQI_CON DQV_CON DQVDT DT_CON DT_SSO DTKE_CON DTKE_HSH DTKE_SSO DU_CON DU_SSO DV_CON DV_SSO EDR EMIS_RAD EVATRA_SUM FC FETCH_LK FF_ANAI FI FI_ANAI FIS FOR_D FOR_E FR_ICE FR_LAKE FRESHSNW GAMSO_LK H_B1_LK H_ICE H_ML_LK H_SNOW H_SNOW_M HBAS_CON HBAS_SC HHL HMO3 HORIZON HPBL HTOP_CON HTOP_DC HTOP_SC HZEROCL LAI LAI_MN LAI_MX LCL_ML LFC_ML LHFL_S LWD_S LWU_S MFLX_CON MSG_RAD MSG_RADC MSG_TB MSG_TBC O3 OMEGA P P_ANAI PABS_RAD PLCOV PLCOV_MN PLCOV_MX PMSL PMSL_ANAI POT_VORTIC PP PRG_GSP PRH_GSP PRR_CON PRR_GSP PRS_CON PRS_GSP PS Q_SEDIM QC QC_ANAI QC_RAD QCVG_CON QG QH QI QI_RAD QNCLOUD QNGRAUPEL QNHAIL QNICE QNRAIN QNSNOW QR QRS QS QV QV_2M QV_ANAI QV_S QVSFLX RCLD RELHUM RELHUM_2M RESID_WSO RHO_SNOW RHO_SNOW_M RLAT RLON ROOTDP RSMIN RSTOM SDI_1 SDI_2 SHFL_S SI SKYVIEW SLI SLO_ANG SLO_ASP SNOWLMT SOBS_RAD SOBT_RAD SOD_T SOHR_RAD SOILTYP SP_10M SSO_GAMMA SSO_SIGMA SSO_STDH SSO_THETA SWDIFD_S SWDIFU_S SWDIR_COR SWDIR_S SWISS00 SWISS12 SYNME5 SYNME6 SYNME7 SYNMSG T T_2M T_ANAI T_B1_LK T_BOT_LK T_BS_LK T_CL T_G T_ICE T_M T_MNW_LK T_S T_SNOW T_SNOW_M T_SO T_WML_LK TCH TCM TD_2M THBS_RAD THBT_RAD THHR_RAD TINC_LH TKE TKE_CON TKETENS TKVH TKVM TO3 TOP_CON TOT_PR TOTFORCE_S TQC TQC_ANAI TQG TQH TQI TQR TQS TQV TQV_ANAI TRA_SUM TWATER U U_10M UMFL_S USTR_SSO V V_10M VDIS_SSO VIO3 VMFL_S VORTIC_U VORTIC_V VORTIC_W VSTR_SSO W W_CL W_G1 W_G2 W_G3 W_I W_SNOW W_SNOW_M W_SO W_SO_ICE WLIQ_SNOW Z0 ZHD ZTD ZWD"

# constant variables
const_list="FR_LAND HSURF"

#additional variables
add_list="SP_10M ASWD_S ASOU_T RUNOFF_T PREC_CON TOT_SNOW TQW"

#-----------------------------------------------------------------------

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
  if [[ ! -f ${OUTDIR2}/${constVar}/${constVar}.nc ]] || ${overwrite} 
  then
    if [[ -f ${INDIR2}/${constVar}.nc ]]
    then
      echon "Copy constant variable ${constVar}.nc to output folder"
      [[ -d ${OUTDIR2}/${constVar} ]] || mkdir ${OUTDIR2}/${constVar}
      cp ${INDIR2}/${constVar}.nc ${OUTDIR2}/${constVar}/
    else
      echo "Required constant variable file ${constVar}.nc is not in input folder ${INDIR2}! Skipping this variable..."
    fi
  fi
done


while [[ ${YY} -le ${YYE} ]]      # year loop
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
  while [[ ${MM} -le ${MME} ]] 
  do 
    if [[ ! -d ${INDIR2}/${YY}_${MM} ]] 
    then
      echo "Directory ${INDIR2}/${YY}_${MM} does not exist! Skipping this year..."
      (( YY=YY+1 ))
      continue 2
    fi
    (( MM=MM+1 ))
  done

  #
  if [[ ${LFILE} -ne 2 ]] 
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
      if [[ "${FILEOUT: -1}" == "p" ]] 
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
      


      # determine if current variable is an accumulated or instantaneous quantity
      if [[ ${accu_list} =~ (^|[[:space:]])${varname}($|[[:space:]]) ]]
      then
        LACCU=1
        echon "${varname} is accumulated variable"
      elif [[ ${inst_list} =~ (^|[[:space:]])${varname}($|[[:space:]]) ]]
      then
        LACCU=0
        echon "${varname} is an instantaneous variable"
      elif [[ ${add_list} =~ (^|[[:space:]])${varname}($|[[:space:]]) ]]
      then
        continue
      else
        echo "Error for ${varname}: neither contained in accu_list nor in inst_list! Skipping..."
        continue
      fi
      
      

      FILELIST=""
      MA=${MMA}
      ME=${MME}
      MM=${MA}
      while [[ ${MM} -le ${ME} ]] 
      do 
        if [[ ! -f ${INDIR2}/${YY}_${MM}/${FILEOUT}_ts.nc ]] 
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
      
      if [[ ${LACCU} -eq 1 ]] 
      then
  #   Check dates in files for accumulated variables
  #   if necessary: delete first date apend first date of next year
        if [[ ${TDA} -eq 01 && ${THA} -eq 00 ]]
        then
          echov "Eliminating first time step from tmp1-File"
          ncks -O -h -d time,1, ${FILEIN} ${FILEOUT}_tmp1_${YY}.nc
        elif [[ ${TDA} -eq 01 &&  ${THA} -eq ${DHH} ]]
        then
          echov "Number of timesteps in tmp1-File is OK"
          cp ${FILEIN} ${FILEOUT}_tmp1_${YY}.nc
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
          if [[ ${MP} -gt 12 ]] 
          then
            MP=01
            (( YP=YP+1 ))
          fi
          FILENEXT=${INDIR2}/${YP}_${MP}/${FILEOUT}_ts.nc
          if [[ -f ${FILENEXT} ]] 
          then
            echov "Append first date from next month's file to the end of current month"
            ncks -O -h -d time,0 ${FILENEXT} ${FILEOUT}_tmp2_${YY}.nc
            ncrcat -O -h  ${FILEOUT}_tmp1_${YY}.nc ${FILEOUT}_tmp2_${YY}.nc ${FILEOUT}_tmp3_${YY}.nc
          else
            echo "ERROR: Tried to append first date from next month's file but"
            echo "${FILENEXT} does not exist. Skip year for this variable..."
            continue
          fi
        elif [[ ${TDE} -eq 01 &&  ${THE} -eq 00 ]]
        then
          (( MP=TME ))
          (( YP=TYE ))
          echov "Last timestep in tmp3-File is OK"
          mv ${FILEOUT}_tmp1_${YY}.nc ${FILEOUT}_tmp3_${YY}.nc
        else
          echo "ERROR: END date  ${TDE} ${THE}"
          echo in "${FILEIN} "
          echo "is not correct. Skip year for this variable..."
          continue
        fi
        ENDFILE=${OUTDIR2}/${FILEOUT}/${FILEOUT}_${TYA}${TMA}${TDA}00-${YP}${MP}0100.nc
  #     shift time variable by DHH/2*3600 and transfer time from seconds in days       
        echov "Modifying time and time_bnds values and attributes"
        ncap2 -O -h -s "time_bnds=time_bnds/86400" -s "time=(time-${DTS})/86400" ${FILEOUT}_tmp3_${YY}.nc ${ENDFILE}
        ncatted -O -h -a units,time,o,c,"${REFTIME}" -a units,time_bnds,o,c,"${REFTIME}" ${ENDFILE}
      else
  #   Check dates in files for instantaneous variables
        if [[ ${TDA} -eq 01 && ${THA} -eq 00 ]]
        then
          echov "First date of instantaneous file is OK"
          cp ${FILEIN} ${FILEOUT}_tmp1_${YY}.nc          
        else
          echo "ERROR: Start date " ${TDA} ${THA}
          echo in "${FILEIN} "
          echo "is not correct.  Skip year for this variable..."
          continue       
        fi
        if [[ ${TDE} -ge 28  && ${THE} -eq ${EHH} ]]
        then
          echov "Last date of instantaneous file is OK"
          mv ${FILEOUT}_tmp1_${YY}.nc ${FILEOUT}_tmp3_${YY}.nc
        elif  [[ ${TDE} -eq 01 && ${THE} -eq 00 ]]
        then
          (( NTM=NT-2 )) 
          echov "Last date of instantaneous file is removed"
          ncks -O -h -d time,0,${NTM} ${FILEOUT}_tmp1_${YY}.nc ${FILEOUT}_tmp3_${YY}.nc 
          #change TDE
          VT=($(cdo -s showtimestamp ${FILEOUT}_tmp3_${YY}.nc))
          TDE=$(echo ${VT[-1]} | cut -c9-10)
        else
          echo "ERROR: END date " ${TDE} ${THE}
          echo in "${FILEIN} "
          echo "is not correct.  Skip year for this variable..."
          echo ${EHH}
          continue       
        fi
        ENDFILE=${OUTDIR2}/${FILEOUT}/${FILEOUT}_${TYA}${TMA}${TDA}00-${YY}${ME}${TDE}${EHH}.nc
  #     transfer time from seconds in days and remove time_bnds from instantaneous fields
        echov "Modifying time values and attributes"
        ncap2 -O -h  -s "time=time/86400" ${FILEOUT}_tmp3_${YY}.nc ${ENDFILE}
        ncks -O -C -h -x -v time_bnds ${ENDFILE} ${ENDFILE}
        ncatted -O -h -a units,time,o,c,"${REFTIME}" -a bounds,time,d,, ${ENDFILE}    
      fi


  #   change permission of final file
      chmod ${PERM} ${ENDFILE}
  #
  #   clean temporary files
      rm -f ${FILEOUT}_tmp?_${YY}.nc
      rm ${FILEIN}

    done                    # var name loopende
#
  fi                              #concatenate part



  #
  # create additional fields required by ESGF
  #
  function create_add_vars {
    name1=$1 #first input variable
    name2=$2 #second input variable
    name3=$3 #output variable
    formula=$4 #formula how to create output variable
    standard_name=$5
    if [[ ${formula} == "add" ]]
    then
      formula="${name3}=${name1}+${name2}"
    elif [[ ${formula} == "subs" ]]
    then
      formula="${name3}=${name1}-${name2}"
    elif [[ ${formula} == "add_sqr" ]]
    then
      formula="${name3}=sqrt(${name1}^2+${name2}^2)"
    else
      echo "Formula ${formula} not known! Skipping"
      return
    fi
        
    if [[ ${proc_list} =~ (^|[[:space:]])${name3}($|[[:space:]]) ]] || ${proc_all}
    then
      file1=$(ls ${OUTDIR2}/${name1}/${name1}_${YY}${MMA}0100*.nc) 
      file2=$(ls ${OUTDIR2}/${name2}/${name2}_${YY}${MMA}0100*.nc)
      echov "Input files and formula:"
      echov "$file1"
      echov "$file2"
      echov "$formula"

      if [[ -f ${file1} && -f ${file2} ]] 
      then
        ((c1 = ${#file1}-23 )) 
        ((c2 = ${#file1}-3 ))
        DATE=$(ls ${file1} |cut -c${c1}-${c2})
        file3=${OUTDIR2}/${name3}/${name3}_${DATE}.nc
        if [[ ! -f ${file3} ]] ||  ${overwrite}
        then
          echon "Create ${name3}"
          [[ -d ${OUTDIR2}/${name3} ]] || mkdir  ${OUTDIR2}/${name3} 
          cp ${file1} temp1_${YY}.nc
          ncks -h -a -A -v ${name2} ${file2} temp1_${YY}.nc
          ncap2 -h -O -s ${formula} temp1_${YY}.nc temp1_${YY}.nc 
          ncks -h -a -O -v ${name3},lat,lon,rotated_pole temp1_${YY}.nc ${file3}
          ncatted -h -a long_name,${name3},d,, ${file3}
          ncatted -h -a standard_name,${name3},m,c,${standard_name} ${file3}
          chmod ${PERM} ${file3}
          rm temp1_${YY}.nc
        else
          echov "$(basename ${file3})  already exists. Use option -o to overwrite. Skipping..."
        fi
      else
        echo "Input Files for generating ${name3} are not available"
      fi
    fi
  }

  if [[ ${LFILE} -ne 1 ]] 
  then
    
    echon ""
    echon " Create additional fields for CORDEX"

    # Mean wind spdeed at 10m height: SP_10M
    create_add_vars "U_10M" "V_10M" "SP_10M" "add_sqr" "wind_speed"
    
    # Total downward global radiation at the surface: ASWD_S
    create_add_vars "ASWDIR_S" "ASWDIFD_S" "ASWD_S" "add" "averaged_downward_sw_radiation_sfc" 
    
    # upward solar radiation at TOA: ASOU_T
    create_add_vars "ASOD_T" "ASOB_T" "ASOU_T" "subs" "averaged_solar_upward_radiation_top" 
    
    # Total runoff: RUNOFF_T
    create_add_vars "RUNOFF_S" "RUNOFF_G" "RUNOFF_T" "add" "total_runoff_amount"
    
    # Total convective precipitation: PREC_CON
    create_add_vars "RAIN_CON" "SNOW_CON" "PREC_CON" "add" "convective_precipitation_amount"
    
    # Total snow: TOT_SNOW
    create_add_vars "SNOW_GSP" "SNOW_CON" "TOT_SNOW" "add" "total_snowfall_amount"
    
    # cloud condensed water content TQW
    create_add_vars "TQC" "TQI" "TQW" "add" "atmosphere_cloud_condensed_water_content"  
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
  #while [[ ${YY}${MM} -le ${YYE}${MME} ]]      # year loop
  #do
  #  Remove the input files if you are shure that they are no longer needed:
  #  Files with monthly time series of single variables generated by subchain-script "post.job"
  #
  #  rm -rf ${YY}_${MM}
   # (( MM=MM+1 ))
    #if [[ ${MM} -gt 12 ]] 
    #then
    #  (( YY=YY+1 ))
     # MM=1
    #fi
  #done


