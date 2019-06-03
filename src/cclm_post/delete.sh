#!/bin/bash
# add -l to /bin/bash (or --login) to execute commands from file /etc/profile
#SBATCH --account=pr04
#SBATCH --nodes=1
#SBATCH --partition=xfer
#SBATCH --time=4:00:00
#SBATCH --output=${BASEDIR}/logs/delete_%j.out
#SBATCH --error=${BASEDIR}/logs/delete_%j.err
#SBATCH --job-name="delete"


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
      startyear=$2
      shift
      ;;
      -e|--end)
      endyear=$2
      shift
      ;;
      -I|--input)
      INPDIR=$2
      shift
      ;;
      *)
      echo "unknown option!"
      ;;
  esac
  shift
done

while [ ${startyear} -le ${endyear} ]
do
  if [ -d ${INPDIR}/${startyear} ]
  then
    echo "Deleting ${INPDIR}/${startyear}" 
    rm -r  ${INPDIR}/${startyear} 
  fi  
  (( startyear=startyear+1 ))
done


