#!/bin/bash
# add -l to /bin/bash (or --login) to execute commands from file /etc/profile
#SBATCH --account=pr04
#SBATCH --nodes=1
#SBATCH --partition=xfer
#SBATCH --time=4:00:00
#SBATCH --output=${BASEDIR}/logs/shell/xfer_%j.out
#SBATCH --error=${BASEDIR}/logs/shell/xfer_%j.err
#SBATCH --job-name="xfer_sh"

overwrite_arch=false
args=""
outstream='out01 out02 out03 out04 out05 out06 out07'
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
      -o|--out)
      OUTDIR=$2
      args="${args} -o $2"
      shift
      ;;
      -a|--arch)
      ARCHDIR=$2
      args="${args} -a $2"
      shift
      ;;
      -l|--log)
      xfer=$2
      args="${args} -l $2"
      shift
      ;;
      -S|--src)
      SRCDIR=$2
      args="${args} -S $2"
      shift
      ;;
      --overwrite_arch)
      overwrite_arch=true
      args="${args} --overwrite_arch"
      ;;
      *)
      echo "unknown option!"
      ;;
  esac
  shift
done

if [[ -z $startyear || -z $endyear || -z $OUTDIR || -z $ARCHDIR || -z $xfer || -z $SRCDIR ]]
then
  echo "Please provide all necessary arguments! Exiting..."
  exit
fi

if [ ! -d ${OUTDIR} ]
then
  mkdir -p ${OUTDIR}
fi

#skip already extracted years
(( NEXT_YEAR=startyear + 1 ))
while [ -d ${OUTDIR}/*${NEXT_YEAR} ] && [ ${NEXT_YEAR} -le ${endyear} ]
do
  echo "Input files for year ${NEXT_YEAR} have already been extracted. Skipping..."
  (( NEXT_YEAR=NEXT_YEAR + 1 ))
done

if [ ${NEXT_YEAR} -le ${endyear} ]
then
  sbatch  --job-name=CMOR_sh_${GCM}_${EXP} --error=${xfer}.${NEXT_YEAR}.err --output=${xfer}.${NEXT_YEAR}.out ${SRCDIR}/xfer.sh -s ${NEXT_YEAR} ${args}
fi

if [ ! -d ${OUTDIR}/*${startyear} ] || ${overwrite_arch}
then
  if [ -d ${ARCHDIR}/*${startyear} ] 
  then
    echo "Moving input directory for year ${startyear} to ${OUTDIR} "
    mv ${ARCHDIR}/*${startyear} ${OUTDIR}
  elif [ -f ${ARCHDIR}/*${startyear}.tar ]
  then
    echo "Extracting archive for year ${startyear} to ${OUTDIR}"
    mkdir ${OUTDIR}/${startyear}
    mkdir ${OUTDIR}/${startyear}/output
    for stream in ${outstream}
    do
	mkdir  ${OUTDIR}/${startyear}/output/${stream}
        tar -xf ${ARCHDIR}/*${startyear}.tar -C ${OUTDIR}/${startyear}/output/${stream} --strip-components=3 output/${stream}/${startyear} 
   done
#    tar -xf ${ARCHDIR}/*${startyear}.tar -C ${OUTDIR}  output/out??/${startyear} 
  else
    echo "Cannot find .tar file or extracted archive for year ${startyear} in archive directory ${ARCHDIR}! Skipping year..."
    exit 1
  fi
else
  echo "Input files for year ${startyear} are already at ${OUTDIR}. Skipping..."
fi
