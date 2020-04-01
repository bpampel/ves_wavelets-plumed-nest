#!/usr/bin/env bash
###
### Run multiple simulations with different seeds

# Variables from arguments
exe=$1
directory=$2
num_iter=$3 # number of independent runs

ves_md_input='input'


cd $directory || exit 1
inputfiles=$(ls)

for i in $(seq 1 $num_iter); do
  mkdir $i || exit 1
  cp $inputfiles $i
  cd $i
  seed=$(python -c "import random; print(random.randint(10000000,99999999))")
  sed -i 's/random_seed.*/random_seed\ '"$seed"'/' "$ves_md_input"
  $exe input > logfile
  cd ../
done
