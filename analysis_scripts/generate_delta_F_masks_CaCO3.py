#!/usr/bin/env python3
"""Generate masks for delta F analyis for the CaCO3 system

first argument is the FES file to be matched"""

import argparse
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('fes_file')
fes_file = parser.parse_args().fes_file

cvs = np.genfromtxt(fes_file).T

# case with just bound and "unbound" (or not tightly bound) state
states = []
states.append(np.where(cv[0] < 4, 1, 0))
states.append(np.where((cv[0] > 4) & (cv < 8[0]), 1, 0)) # unbound state(s), cutoff at 8

for i, state in enumerate(states):
    np.savetxt('delta_F_2states_mask' + str(i+1), state, fmt='%1d')


# -----------------------------------------------
# old case with four somewhat arbitrary states: not used in the paper

# bounddist = np.where(cvs[0] < 4, 1, 0)

# states = []
# states.append(np.where((cvs[1] > 6) & (cvs[1] < 7), 1, 0) * bounddist)  # global minimum (monodentate state)
# states.append(np.where(cvs[1] < 6, 1, 0) * bounddist)  # bidentate
# states.append(np.where((cvs[1] > 7) & (cvs[1] < 8), 1, 0) * bounddist)  # other somewhat bound state
# states.append(np.where((cvs[0] > 4) & (cvs[0] < 5) & (cvs[1] > 7) & (cvs[1] < 8), 1, 0)) # solvent-shared ion pair

# for i, state in enumerate(states):
#    np.savetxt('delta_F_4states_mask' + str(i+1), state, fmt='%1d')
