#!/bin/ksh

source ./settings.sh

overwrite=false #overwrite output if it exists
n=true #normal printing mode
v=false #verbose printing mode
clean=false #clean  files in WORKDIR  
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
      -i|--input)
      EXPPATH=$2
      shift
      ;;
       -s1|--start1)
      START_DATE=$2
      shift
      ;;
      -e1|--end1)
      STOP_DATE=$2
      shift
      ;;
      -s2|--start2)
      YYA=$2
      shift
      ;;
      -e2|--end2)
      YYE=$2
      shift
      ;;
      --first)
      post_step=1
      ;;
      --second)
      post_step=2
      ;;
      -S|--silent)
      n=false
      ;;
      -V|--verbose)
      v=true
      ;;
      -O|--overwrite)
      overwrite=true
      ;;
      --clean)
      clean=true
      ;;
      *)
      echo "unknown option!"
      ;;
  esac
  shift
done

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
  echo "Path to input data: " ${INPATH}
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
