#!/bin/ksh
#SBATCH --account=pr04
#SBATCH --nodes=1
##SBATCH --partition=prepost
#SBATCH --time=4:00:00
#SBATCH --constraint=gpu
#SBATCH --output=/scratch/snx1600/mgoebel/CMOR/logs/CMOR_py_%j.out
#SBATCH --error=/scratch/snx1600/mgoebel/CMOR/logs/CMOR_py_%j.err
#SBATCH --job-name="CMOR_py"

cores=3
script_folder="${SCRATCH}/CMOR/src/CMORlight"
python_script="${script_folder}/cmorlight2.py"

#necessary for derotation
export IGNORE_ATT_COORDINATES=1

multi=false # run several jobs simultaneously
args=""
while [[ $# -gt 0 ]]
do
  key="$1"
  case $key in
       -s|--start)
      START=$2
      shift
      ;;
      -e|--end)
      STOP=$2
      shift
      ;;
      -m|--multi)
      multi=true
      ;;
      *)
      args="$args $1"
      ;;
  esac
  shift
done



# Python script runs $cores years at once -> create one job out of $cores years
(( START_NEW=START+cores ))

if [ -z ${START} ]  
then
  echo "Please provide start year for processing with -s YYYY. Exiting..."
  exit
fi

if [ -z ${STOP} ]  
then
  echo "Please provide end year for processing with -e YYYY. Exiting..."
  exit
fi

if [ ${START_NEW} -le ${STOP} ] && $multi
then
  sbatch master_cmor.sh ${args} -m -s ${START_NEW} -e ${STOP}
  (( STOP=START+cores-1 )) #STOP year for this batch
fi

cd ${script_folder}
echo "Starting Python script for years ${START} to ${STOP}..."
python ${python_script} ${args} -s ${START} -e ${STOP}
echo "finished"



