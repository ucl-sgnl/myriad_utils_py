#!/bin/bash -l
#$ -S /bin/bash
#$ -l h_rt=5:00:0
#$ -l mem=512M
#$ -t 1-120
#$ -N srp_trr_job_array
#$ -wd /Users/charlesc/Documents/GitHub/myriad_utils_py/Scratch/noref_GPSIIF_v06/spiralPoints/outputFiles

module unload mkl/10.2.5/035
module unload mpi/qlogic/1.2.7/intel
module unload compilers/intel/11.1/072
module load compilers/gnu/4.1.2
module load mpi/qlogic/1.2.7/gnu

param_file=/Users/charlesc/Documents/GitHub/myriad_utils_py/Scratch/noref_GPSIIF_v06/spiralPoints/paramFiles/params$(printf '%05d' $SGE_TASK_ID).txt
output_file=/Users/charlesc/Documents/GitHub/myriad_utils_py/Scratch/noref_GPSIIF_v06/spiralPoints/outputFiles/output$(printf '%05d' $SGE_TASK_ID).txt

/home/zcesccc/srp_trr_classic/bin/srp_trr_classic $param_file /Users/charlesc/Documents/GitHub/myriad_utils_py/noref_GPSIIF_v06/noref_GPSIIF_v06.txt $output_file
