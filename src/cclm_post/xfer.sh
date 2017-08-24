#!/bin/bash -l
#SBATCH --account=pr04
#SBATCH --nodes=1
#SBATCH --partition=xfer
#SBATCH --time=4:00:00
#SBATCH --output=xfer.out
#SBATCH --error=xfer.err
#SBATCH --job-name="xfer"


set -ex


BASEDIR=/scratch/snx1600/mgoebel/CMOR

source ${BASEDIR}/src/settings.sh

INPDIR=${INPUTPOST}/${EXPPATH}

if [ ! -d ${INPUTPOST}/${EXPPATH} ]
then
  mkdir -p ${INPUTPOST}/${EXPPATH}
fi

startyear=${1}
endyear=${2}



NEXTYEAR=`expr ${startyear} + 1`
set -ex

if [ ${NEXTYEAR} -le ${endyear} ]
then
 sbatch xfer.sh ${NEXTYEAR} ${endyear}
fi

if [ -f ${ARCHDIR}/*${startyear}.tar ]
then
  echo "Extracting archive for year ${startyear}"
  tar -xf ${ARCHDIR}/*${startyear}.tar -C ${INPDIR}
  #cd ${INPDIR}/${startyear}
  #rm -r input

else
  echo "Cannot find .tar file in archive directory! Exiting..."
  exit 1
fi



exit 0
