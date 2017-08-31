#!/bin/ksh
#SBATCH --account=pr04
#SBATCH --nodes=1
#SBATCH --partition=prepost
#SBATCH --time=00:30:00
#SBATCH --constraint=mc
#SBATCH --output=/scratch/snx1600/mgoebel/CMOR/logs/shell/CMOR_sh_%j.out
#SBATCH --error=/scratch/snx1600/mgoebel/CMOR/logs/shell/CMOR_sh_%j.err
#SBATCH --job-name="CMOR_sh"


#Check if all functions are available
funcs="ncrcat ncks ncap2 ncatted"
for f in $funcs
do
  typ=$(type -p $f)
  if [ -z ${typ} ]  
  then
    echo "Necessary function $f is not available! Load respective module. Exiting..."
    exit
  fi
done

TIME1=$(date +%s)
cd ${SCRATCH}/CMOR/src
source ./settings.sh

#default values
overwrite=false #overwrite output if it exists
n=true #normal printing mode
v=false #verbose printing mode
clean=false #clean  files in WORKDIR  
batch=true #create batch jobs continously always for one year
extract=10 #number of years to extract at once


args=""
concat=false

while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
      -g|--gcm)
      GCM=$2
      args="${args} -g $2"
      shift
      ;;
      -x|--exp)
      EXP=$2
      args="${args} -x $2"
      shift
      ;;
       -s|--start)
      START_DATE=$2
      shift
      ;;
      -e|--end)
      STOP_DATE=$2
      args="${args} -e $2"
      shift
      ;;
      -F|--first_year)
      FIRST=$2
      shift
      ;;
      -E|--extract)
      extract=$2
      shift
      ;;
      --first)
      post_step=1
      args="${args} --first"
      ;;
      --second)
      post_step=2
      args="${args} --second"
      ;;
      -S|--silent)
      n=false
      args="${args} -S"
      ;;
      -V|--verbose)
      v=true
      args="${args} -V"
      ;;
      -O|--overwrite)
      overwrite=true
      args="${args} -O"
      ;;
      --no_batch)
      batch=false
      args="${args} --no_batch"
      ;;
      --clean)
      clean=true
      args="${args} --clean"
      ;;
      *)
      echo "unknown option!"
      ;;
  esac
  shift
done

#log base names
CMOR=${SCRATCH}/CMOR/logs/shell/${GCM}_${EXP}_CMOR_sh
xfer=${SCRATCH}/CMOR/logs/shell/${GCM}_${EXP}_xfer
delete=${SCRATCH}/CMOR/logs/shell/${GCM}_${EXP}_delete


#printing modes

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


EXPPATH=${GCM}/${EXP}
EXPID=${GCM}_${EXP}

#folders
INDIR1=${INDIR_BASE1}/${EXPPATH}
OUTDIR1=${OUTDIR_BASE1}/${EXPPATH}

INDIR2=${INDIR_BASE2}/${EXPPATH}
OUTDIR2=${OUTDIR_BASE2}/${EXPPATH}


#range for second script
YYA=$(echo ${START_DATE} | cut -c1-4) 
YYE=$(echo ${STOP_DATE} | cut -c1-4)

#initialize first year
if [ -z ${FIRST} ]  
then
  FIRST=${YYA}
fi

#if only years given: process from January to December
if [ ${#START_DATE} -eq 4 ]
then
  START_DATE="${START_DATE}01"
  (( STOP_DATE=STOP_DATE+1 ))
  STOP_DATE="${STOP_DATE}01"
else
  START_DATE= $(echo ${START_DATE} | cut -c1-6) 
  STOP_DATE=$(echo ${STOP_DATE} | cut -c1-6) 
fi

#if no archives have been extracted in the beginning:
if [ ! -d ${INDIR1}/*${YYA} ] && [ ${post_step} -ne 2 ]
then
    (( endex=YYA+extract-1 ))
    #limit to extraction to end year
    if [ ${endex} -gt ${YYE} ]
    then
      endex=${YYE}
    fi
    echon "Extracting years ${YYA} to ${endex} \n\n"
    sbatch --job-name=CMOR_sh --error=${xfer}.${YYA}.err --output=${xfer}.${YYA}.out ${SRCDIR}/xfer.sh -s ${YYA} -e ${endex} -g ${GCM} -x ${EXP}
    #abort running job and restart it after extraction is done
    sbatch --dependency=singleton --job-name=CMOR_sh --error=${CMOR}.${YYA}.err --output=${CMOR}.${YYA}.out master_post.sh ${args} -s ${YYA} -F ${FIRST} 
    exit
fi

(( NEXTYEAR=YYA+1 ))

#for batch processing: process only one year per job
if [ ${NEXTYEAR} -le ${YYE} ] && ${batch}  
then
  #Extract archived years every 10 years
  (( d=YYA-FIRST ))
  (( mod=d%extract ))
  if [ $mod -eq 0 ] && [ ${post_step} -ne 2 ]
  then
    (( startex=YYA+extract ))
    (( endex=YYA+2*extract-1 ))
    #limit to extraction to end year
    if [ ${endex} -gt ${YYE} ]
    then
      endex=${YYE}
    fi
    if [ ${startex} -le ${YYE} ]
    then
      echon "Extracting years from ${startex} to  ${endex} \n\n"
      sbatch  --job-name=CMOR_sh --error=${xfer}.${startex}.err --output=${xfer}.${startex}.out ${SRCDIR}/xfer.sh -s ${startex} -e ${endex} -g ${GCM} -x ${EXP}
       #Submit job for the following year when all other jobs (to wait for extraction) are finished
      sbatch --dependency=singleton --job-name=CMOR_sh --error=${CMOR}.${NEXTYEAR}.err --output=${CMOR}.${NEXTYEAR}.out master_post.sh ${args} -s ${NEXTYEAR} -F ${FIRST} 
    else
      #Submit job for the following year without waiting
      sbatch --job-name=CMOR_sh --error=${CMOR}.${NEXTYEAR}.err --output=${CMOR}.${NEXTYEAR}.out master_post.sh ${args} -s ${NEXTYEAR} -F ${FIRST} 
    fi
  else
    #Submit job for the following year without waiting
    sbatch --job-name=CMOR_sh --error=${CMOR}.${NEXTYEAR}.err --output=${CMOR}.${NEXTYEAR}.out master_post.sh ${args} -s ${NEXTYEAR} -F ${FIRST} 
  fi
  
  #at end concatenate all log files
  if [ ${YYA} -eq ${YYE} ]
  then
    concat=true
  fi
  
  #Set stop years to start years to process only one year per job
  YYE=${YYA}
  ((STOP_DATE=START_DATE+100 )) #increase by one year (months are also in there)
  
fi


if  [ ${post_step} -ne 2 ]
then
  CURRENT_DATE=${START_DATE}
  echo "###################################################### \n First  processing step \n######################################################"
 # echo "Path to input data: " ${ARCHDIR}
  echo "Start: " ${START_DATE}
  echo "Stop: " ${STOP_DATE}
  source ${SRCDIR}/first.sh

fi


if [ ${post_step} -ne 1 ]
then
  echo ""
  echo "###################################################### \n Second processing step \n######################################################"
  echo "Start: " ${YYA}
  echo "Stop: " ${YYE}
  source ${SRCDIR}/second.sh
fi

if ${clean}
then
  rm -r ${WORKDIR}
fi

echo "######################################################"
TIME2=$(date +%s)
SEC_TOTAL=$(python -c "print(${TIME2}-${TIME1})")
echo "total time for postprocessing: ${SEC_TOTAL} s"


if [ ${post_step} -ne 2 ]
then
  #Delete input data
  echo "deleting input data"
  sbatch --job-name=delete --error=${delete}.${YYA}.err --output=${delete}.${YYA}.out ${SRCDIR}/delete.sh -s ${YYA} -e ${YYE} -g ${GCM} -x ${EXP}  
fi

#at end concatenate all log files
if ${concat}
then
  year=${FIRST}
  while [ year -le ${YYE} ]
  do
    echo "CMOR STEP 1 \n GCM: ${GCM} \n Experiment: ${GCM} \n Years: ${FIRST} - ${YYE} ######################################################" >> ${CMOR}.log
    cat ${xfer}.${year}.out >> ${CMOR}.log
    cat ${CMOR}.${year}.out >> ${CMOR}.log
    echo "######################################################\n\n"
    (( year=year+1 ))
  done 
fi
