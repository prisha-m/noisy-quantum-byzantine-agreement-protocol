#!/bin/bash
#SBATCH --job-name=t2noisy_sf
#SBATCH --output=/scratch/pmeswani/delftblue_test/noisyt1t2/logs/simsf_%A_%a.out
#SBATCH --error=/scratch/pmeswani/delftblue_test/noisyt1t2/logs/simsf_%A_%a.err
#SBATCH --array=0-5            # 100 chunks of 100 samlpes
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=15
#SBATCH --time=03:00:00      # hh:mm:ss
#SBATCH --mem-per-cpu=3000             
#SBATCH --account=Education-EEMCS-Courses-CSE3000
#SBATCH --partition=compute

module load 2023r1
module load python/3.9.8

# Navigate to your working directory
cd "/scratch/pmeswani/delftblue_test/"

source venv/bin/activate

cd "noisyt1t2"

# Run python with chunk id from SLURM_ARRAY_TASK_ID
srun python3 rs_sf.py $SLURM_ARRAY_TASK_ID
