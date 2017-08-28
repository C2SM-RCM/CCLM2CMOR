#!/bin/bash -l
#SBATCH --account=pr04
#SBATCH --nodes=1
#SBATCH --partition=xfer
#SBATCH --time=4:00:00
#SBATCH --output=/scratch/snx1600/mgoebel/CMOR/logs/shell/xfer_%j.out
#SBATCH --error=/scratch/snx1600/mgoebel/CMOR/logs/shell/xfer_%j.err
#SBATCH --job-name="xfer_sh"


BASEDIR=${SCRATCH}/CMOR

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
xfer=${SCRATCH}/CMOR/logs/shell/${GCM}_${EXP}_xfer

if [ ! -d ${INPDIR} ]
then
  mkdir -p ${INPDIR}
fi

#skip already extracted years
(( NEXTYEAR=startyear + 1 ))
while [ -d ${INPDIR}/*${NEXTYEAR} ] && [ ${NEXTYEAR} -le ${endyear} ]
do
  echo "Input files for year ${NEXTYEAR} have already been extracted. Skipping..."
  (( NEXTYEAR=NEXTYEAR + 1 ))
done


if [ ${NEXTYEAR} -le ${endyear} ]
then
  sbatch  --job-name=CMOR_sh --error=${xfer}.${NEXTYEAR}.err --output=${xfer}.${NEXTYEAR}.out ${SRCDIR}/xfer.sh -s ${NEXTYEAR} ${args}
fi


if [ ! -d ${INPDIR}/*${startyear} ]
then
  if [ -f ${ARCHDIR}/*${startyear}.tar ] 
  then
    echo "Extracting archive for year ${startyear}"
    tar -xf ${ARCHDIR}/*${startyear}.tar -C ${INPDIR}
    rm -r ${INPDIR}/${startyear}/input

  else
    echo "Cannot find .tar file for year ${startyear} in archive directory! Exiting..."
    exit 1
  fi
else
  echo "Input files for year ${startyear} have already been extracted. Skipping..."
fi


