#!/bin/bash -l
# Standard output and error:
#SBATCH -o ./tjob.out.%j
#SBATCH -e ./tjob.err.%j
# Initial working directory:
#SBATCH -D .
# Job Name:
#SBATCH -J CaCO3_ves
# Queue (Partition):
#SBATCH --partition=general
# Number of nodes and tasks per node:
#SBATCH --nodes=25
#SBATCH --ntasks-per-node=32
#
#SBATCH --mail-type=end
#SBATCH --mail-user=pampel@mpip-mainz.mpg.de
#
# Wall clock limit:
#SBATCH --time=24:00:00

EXE=/u/bpampel/executables/lmp_mpi
WALKERS=25

STARTDIR=`pwd`

# timestamp and random seed for unique dir name
TMPNAME=`date -Iseconds`-$RANDOM
TMPDIR=/ptmp/bpampel/$TMPNAME
mkdir -p $TMPDIR
cd $TMPDIR

# move needed files here
rsync -az ${STARTDIR}/input/* ./
echo 'Copied files to '`pwd`

# change seeds using python random
SEEDS=`python3 -c "import random; print(*random.sample(range(10000000,99999999),${WALKERS}))"`
sed -i 's/seed\ world.*/seed\ world\ '"$SEEDS"'/' 'start.lmp'

# run job
srun $EXE -partition ${WALKERS}x32 -in start.lmp -screen none
echo 'Job finished, now syncing files'

# copy output files to userspace and clean up
rsync -az ${TMPDIR} ${STARTDIR}
#rm -r $TMPDIR
