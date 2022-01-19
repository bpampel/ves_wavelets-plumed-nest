#!/bin/bash

folders=("chebyshev" "sym10" "metad")
runs=3

for f in ${folders[@]}; do
  custom_input_files=$(ls -d $PWD/$f/*)  # full paths
  for run in $(seq $runs); do
    mkdir "$f/run$run" || exit -1
    mkdir "$f/run$run/input" || exit -1
    inputdir="$f/run$run/input"
    cp $custom_input_files "$inputdir"
    cp shared_input/* "$inputdir"
    mkdir $inputdir/initial_configurations || exit -1
    cp initial_configurations/run$run/* $inputdir/initial_configurations
  done
done
