#!/bin/bash
###############################################################################
# batch settings for MISTRAL at DKRZ, Hamburg
#  setting here are for shared Partition with a maximum of 36 CPUS 
###############################################################################
#SBATCH --job-name CHUNK_@{VAR}_@{START_PERIOD}-@{STOP_PERIOD}
#SBATCH --nodes=@{NODES}
#SBATCH --partition=@{PARTITION}
###SBATCH --cpus-per-task=1
#SBATCH --ntasks-per-node=@{CPUS}
#SBATCH --mem-per-cpu=@{MEM_CHUNK}
#SBATCH --output @{JOBDIR}/CHUNK_@{VAR}_@{START_PERIOD}-@{STOP_PERIOD}.out
#SBATCH --error @{JOBDIR}/CHUNK_@{VAR}_@{START_PERIOD}-@{STOP_PERIOD}.err
#SBATCH --time=@{WALLTIME_CHUNK}
#SBATCH --account=@{ACCOUNT}

# Set Environment variables ###################################################
export IGNORE_ATT_COORDINATES=1 # grid for derotation is rlat/rlon

ulimit -s 102400

# Run the program #############################################################
echo "Start CHUNK program for years @{START_PERIOD} to @{STOP_PERIOD}."
time srun -l --propagate=STACK --cpu_bind=verbose,cores --distribution=block:cyclic @{PYTHON} @{CMORPROG} @{ARGS_CHUNK} -s @{START_PERIOD} -e @{STOP_PERIOD}
echo "CHUNK program finished."
