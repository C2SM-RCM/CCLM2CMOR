#!/bin/bash -l
#SBATCH --account=pr04
#SBATCH --nodes=1
#SBATCH --partition=xfer
#SBATCH --time=4:00:00
#SBATCH --output=/scratch/snx1600/mgoebel/CMOR/logs/shell/delete_%j.out
#SBATCH --error=/scratch/snx1600/mgoebel/CMOR/logs/shell/delete_%j.err
#SBATCH --job-name="delete"


BASEDIR=/scratch/snx1600/mgoebel/CMOR

source ${BASEDIR}/src/settings.sh
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
      startyear=$2
      shift
      ;;
      -e|--end)
      endyear=$2
      args="${args} -e $2"
      shift
      ;;
      *)
      echo "unknown option!"
      ;;
  esac
  shift
done

EXPPATH=${GCM}/${EXP}
INPDIR=${INDIR_BASE1}/${EXPPATH}

while [ ${startyear} -le ${endyear} ]
do
  echo "Deleting ${INPDIR}/${startyear}" #/input
  rm -r  ${INPDIR}/${startyear} #/input
  (( startyear=startyear+1 ))
done


