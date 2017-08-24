#!/bin/ksh
#SBATCH --account=pr04
#SBATCH --nodes=1
##SBATCH --partition=prepost
#SBATCH --time=4:00:00
#SBATCH --constraint=gpu
#SBATCH --output=/scratch/snx1600/mgoebel/CMOR/logs/shell/CMOR_sh_%j.out
#SBATCH --error=/scratch/snx1600/mgoebel/CMOR/logs/shell/CMOR_sh_%j.err
#SBATCH --job-name="CMOR_sh"

DATE1=$(date +%s)
cd /scratch/snx1600/mgoebel/CMOR/src
source ./settings.sh

overwrite=false #overwrite output if it exists
n=true #normal printing mode
v=false #verbose printing mode
clean=false #clean  files in WORKDIR  
batch=false
args=""
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
      -i|--input)
      EXPPATH=$2
      args="${args} -i $2"
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
      --batch)
      batch=true
      args="${args} --batch"
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


#range for first and second script equal
YYA=$(echo ${START_DATE} | cut -c1-4) 
YYE=$(echo ${STOP_DATE} | cut -c1-4)

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

(( NEXT_YEAR=YYA+1 ))

#for batch processing: process only one year per job
if [ ${NEXT_YEAR} -le ${YYE} ] && ${batch}  
then
  #Submit job for the following year  
  sbatch master_post.sh ${args} -s ${NEXT_YEAR}

  #Set stop years to start years to process only one year per job
  YYE=${YYA}
  ((STOP_DATE=START_DATE+100 )) #increase by one year (months are also in there)

fi
EXPPATH=${GCM}/${EXP}
EXPID=${GCM}_${EXP}

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


echo "GCM:" ${GCM}
echo "Experiment:" ${GCM}
echo "######################################################"

if  [ ${post_step} -ne 2 ]
then
  CURRENT_DATE=${START_DATE}
  echo "First processing step \n######################################################"
 # echo "Path to input data: " ${ARCHDIR}
  echo "Start: " ${START_DATE}
  echo "Stop: " ${STOP_DATE}
  source ${SRCDIR}/first.sh

fi


if [ ${post_step} -ne 1 ]
then
  echo ""
  echo "######################################################"
  echo "Second processing step \n######################################################"
  echo "Start: " ${YYA}
  echo "Stop: " ${YYE}
  source ${SRCDIR}/second.sh

fi

if ${clean}
then
  rm -r ${WORKDIR}
fi

echo "######################################################"
DATE2=$(date +%s)
SEC_TOTAL=$(python -c "print(${DATE2}-${DATE1})")
echo "total time for postprocessing: ${SEC_TOTAL} s"

