
GCM=HadGEM2-ES
EXP=RCP85

DirBase=/project/pr04/mgoebel/CMOR
Const=${DirBase}/work/cclm_work/${GCM}/${EXP}/cclm_const.nc
DirOut=${DirBase}/work/input_CMORlight/${GCM}/${EXP}

function timeseries {  # building a time series for a given quantity
cd @{INPDIR}/@{CURRDIR}/$2
@{NCO_BINDIR}/ncrcat -h -O -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v $1 lffd@{CURRENT_DATE}*[!cpz].nc @{OUTDIR}/@{YYYY_MM}/$1_ts.nc
@{NCO_BINDIR}/ncks -h -A -d rlon,${NBOUNDCUT},${IESPONGE} -d rlat,${NBOUNDCUT},${JESPONGE} -v lon,lat,rotated_pole @{INPDIR}/@{CURRDIR}/$2/lffd@{CURRENT_DATE}0100.nc @{OUTDIR}/@{YYYY_MM}/$1_ts.nc
}

