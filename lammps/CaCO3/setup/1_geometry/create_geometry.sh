#!/usr/bin/env bash

# create geometry from structures via packmol and vmd
# outputs data.CaCO3 file

packmol < packmol.in
vmd -pdb CaCO3.pdb < topo.tcl
