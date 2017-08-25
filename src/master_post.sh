#!/bin/ksh
#SBATCH --account=pr04
#SBATCH --nodes=1
##SBATCH --partition=prepost
#SBATCH --time=04:00:00
#SBATCH --constraint=gpu
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

(( NEXT_YEAR=YYA+1 ))


echo "GCM:" ${GCM}
echo "Experiment:" ${GCM}
echo "######################################################"
 
#for batch processing: process only one year per job
if [ ${NEXT_YEAR} -le ${YYE} ] && ${batch}  
then


  #Extract archived years every 10 years
  (( d=YYA-FIRST ))
  (( mod=d%10 ))
  if [ $mod -eq 0 ]
  then
    (( startex=YYA+10 ))
    (( endex=YYA+19 ))
    echon "Extracting years ${startex} to  ${endex} \n\n"
    sbatch  ${SRCDIR}/xfer.sh -s ${startex} -e ${endex} -g ${GCM} -x ${EXP}
    #Submit job for the following year after all other jobs (including extraction) are finished
    sbatch --dependency=singleton master_post.sh ${args} -s ${NEXT_YEAR} -F ${FIRST} 
  else
    sbatch master_post.sh ${args} -s ${NEXT_YEAR} -F ${FIRST} 
  fi


  #Set stop years to start years to process only one year per job
  YYE=${YYA}
  ((STOP_DATE=START_DATE+100 )) #increase by one year (months are also in there)

fi




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

#Delete input data
echo "deleting input data"
sbatch  ${SRCDIR}/delete.sh -s ${YYA} -e ${YYE} -g ${GCM} -x ${EXP}
