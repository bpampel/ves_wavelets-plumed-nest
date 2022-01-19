#!/usr/bin/env bash

# set all variables
basedir=1d-double_well
shared_input_dir=shared_input
num_iter=20
simulation_exe='plumed ves_md_linearexpansion'
multisim_exe=$(pwd)/run_multisim.sh
pot_ref_file="$basedir/pot_ref.data"

# uncomment the simulation you want to do
name=sym8
#name='legendre'
#name='gaussians'
#name='splines'

# somewhat crude test with the --help switch but otherwise the needed ves module has to be specified manually
$simulation_exe --help > /dev/null 2>&1 || { echo "Error: Executable $simulation_exe could not be called successfully."; exit 1; }


# copy files
fulldir=$basedir/$name
mkdir "$fulldir" || exit 1
cp -R "$basedir/$shared_input_dir/." "$fulldir"
cp "$basedir/plumed_$name.dat" "$fulldir/plumed.dat"

# run simulations
"$multisim_exe" "$simulation_exe" "$fulldir" "$num_iter"
