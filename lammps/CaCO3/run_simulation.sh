#!/usr/bin/env bash

exe=lmp_mpi
walkers=25
inputdir="sym10"
outdir="$HOME/data/CaCO3/${inputdir}_$(date -Iminutes)" # adjust to system

mkdir $outdir | exit -1

# copy input files to tmp directory
tmpdir=$(mktemp -d) | exit 1 # adjust to system
cp shared_input/* $tmpdir/
cp $inputdir/* $tmpdir/
echo "Copied files to $tmpdir"

# change seeds using python random
cd $tmpdir
seeds=`python3 -c "import random; print(*random.sample(range(10000000,99999999),${walkers}))"`
sed -i 's/seed\ world.*/seed\ world\ '"$seeds"'/' 'start.lmp'

# run job
echo 'Starting simulation'
srun $exe -partition ${walkers}x32 -in start.lmp -screen none
echo 'Simulation finished, moving files'

# copy output files to userspace and clean up
mv * $outdir/
rmdir $tmpdir
echo 'All finished'
