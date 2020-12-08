#!/bin/bash
###############################################################################
# batch settings for MISTRAL at DKRZ, Hamburg
#  setting here are for shared Partition with a maximum of 36 CPUS 
###############################################################################
#SBATCH --job-name CMOR_@{VAR}_@{START}-@{STOP}
#SBATCH --nodes=@{NODES}
#SBATCH --partition=@{PARTITION}
#SBATCH --ntasks-per-node=@{CPUS}
##SBATCH --cpus-per-task=@{CPUS}
#SBATCH --mem-per-cpu=@{MEM}
#SBATCH --output @{JOBDIR}/CMOR_@{VAR}_@{START}-@{STOP}.out
#SBATCH --error @{JOBDIR}/CMOR_@{VAR}_@{START}-@{STOP}.err
#SBATCH --time=@{WALLTIME}
#SBATCH --account=@{ACCOUNT}

# Set Environment variables ###################################################
export IGNORE_ATT_COORDINATES=1 # grid for derotation is rlat/rlon

ulimit -s 102400

# Run the program #############################################################
echo "Start CMOR program for years @{START} to @{STOP}."
#time srun -l --propagate=STACK --cpu_bind=verbose,cores --distribution=block:cyclic @{PYTHON} @{CMORPROG} @{ARGS} -s @{START} -e @{STOP}
time  @{PYTHON} @{CMORPROG} @{ARGS} -s @{START} -e @{STOP}
echo "CMOR program finished."
