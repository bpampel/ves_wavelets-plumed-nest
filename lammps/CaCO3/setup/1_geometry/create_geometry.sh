#!/usr/bin/env bash

packmol < packmol.in
vmd -pdb CaCO3.pdb < topo.tcl
