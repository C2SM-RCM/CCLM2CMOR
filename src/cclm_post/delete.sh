#!/bin/bash -l
#SBATCH --account=pr04
#SBATCH --nodes=1
#SBATCH --partition=xfer
#SBATCH --time=4:00:00
#SBATCH --output=delete.out
#SBATCH --error=delete.err
#SBATCH --job-name="xfer"


BASEDIR=/scratch/snx1600/mgoebel/CMOR

source ${BASEDIR}/src/settings.sh

INPDIR=${INPUTPOST}/${EXPPATH}


startyear=${1}
endyear=${2}

year=${startyear}


#~ if [ ${NEXTYEAR} -le ${endyear} ]
#~ then
 #~ sbatch xfer.sh ${NEXTYEAR} ${endyear}
#~ fi
while [ ${year} -le ${endyear} ]
do
  echo "Deleting ${INPDIR}/${year}" #/input
  rm -r  ${INPDIR}/${year} #/input
  (( year=year+1 ))
done


exit 0
