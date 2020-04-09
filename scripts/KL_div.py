#!/usr/bin/env python3
"""
Calculates Kullback-Leibler divergence of a set of FES files with respect to some reference
"""

import argparse
from functools import partial
import os
from multiprocessing import Pool
import numpy as np
from helpers import misc as hlpmisc


def parse_args():
    """Get cli args"""
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                        help="Path to the folder to be evaluated")
    parser.add_argument('-r', '--ref',
                        help="Path to the reference FES file",
                        required=True)
    parser.add_argument('-k', '--kT', type=float,
                        help="Value of kT for the FES files (in matching units)",
                        required=True)
    parser.add_argument('-d', '--dim', type=int, default=1,
                        help="Dimension of the FES files, defaults to 1")
    parser.add_argument('-o', '--outfile', default="kl_div",
                        help="Name of the output file(s), defaults to \"kl_div\"")
    parser.add_argument("-a", "--average", action='store_true',
                        help="Also calculate average over runs.")
    parser.add_argument('-i', '--invert', action='store_true',
                        help="Use the reference probabilities as Q(x) instead of P(x)")
    parser.add_argument("-np", "--numprocs", type=int, default="1",
                        help="Number of parallel processes")
    args = parser.parse_args()
    return args


def fes_to_prob(fes, kT):
    """Returns normalized probability distribution from free energy surface"""
    prob = np.exp(- fes / float(kT))
    return normalize_distribution(prob)


def normalize_distribution(x):
    """Normalize a probability distribution"""
    norm = 1 / np.sum(x)
    return x * norm


def kl_div(p, q):
    """
    Calculates the Kullback-Leibler divergence of two probability distributions

    Arguments
    ---------
    p : numpy array containing the data / reference probabilities
    q : numpy array containing the model probabilities

    Returns
    -------
    kl_div : a double containing the KL divergence
    """
    x = np.where((p > 0) & (q > 0), p * np.log(p/q), 0) # filter out log(0)

    return np.sum(x)


def kl_div_to_ref(filename, ref, kT, dim, inv):
    """
    Calculates the Kullback-Leibler divergence of a FES file to a reference

    Arguments
    ---------
    filename : path to the fes file
    ref      : numpy array holding the reference probabilities
    kT       : energy in units of kT

    Returns
    -------
    kl_div : a double containing the KL divergence
    """

    fes = np.genfromtxt(filename).T[dim]
    if fes.shape != ref.shape:
        raise ValueError("Number of elements of reference and file " + filename + " does not match")
    prob = fes_to_prob(fes, kT)

    if inv:
        return kl_div(prob, ref)
    else:
        return kl_div(ref, prob)


if __name__ == '__main__':
    args = parse_args()

    # read reference fes file
    try:
        ref = np.genfromtxt(args.ref).T
    except IOError:
        print("Reference file not found!")
    if ref.shape[0] != args.dim + 1: # dim colvar columns + data colum
        raise ValueError("Specified dimension and dimension of reference file do not match.")
    ref = fes_to_prob(ref[args.dim], args.kT) # overwrite ref with the probabilities

    # get subfolders and filenames
    folders = hlpmisc.get_subfolders(args.path)
    if not folders:
        print("There are no subfolders of the form '[0-9]*' at the specified path.")
        if args.average:
            raise ValueError("Averaging not possible. Are you sure about the -a option?")
        else:
            print("Using only the FES files of the base directory.")
            folders = [args.path]

    files, times = hlpmisc.get_fesfiles(folders[0]) # assumes all folders have the same files

    allfilenames = [os.path.join(folder, f) for folder in folders for f in files]

    pool = Pool(processes=args.numprocs)

    kl = pool.map(partial(kl_div_to_ref, kT=args.kT, ref=ref, dim=args.dim, inv=args.invert), allfilenames)
    kl = np.array(kl).reshape(len(folders),len(files)) # put in matrix form

    fileheader =     "#! FIELDS time kl_div"
    fileheader += ("\n#! SET kT " + str(args.kT))

    for i, folder in enumerate(folders):
        outfile = os.path.join(folder, args.outfile)
        hlpmisc.backup_if_exists(outfile)
        np.savetxt(outfile, np.vstack((times, kl[i])).T, header=fileheader,
                   delimiter=' ', newline='\n')

    avgheader =     "#! FIELDS time kl_div stddev"
    avgheader += ("\n#! SET kT " + str(args.kT))

    if args.average:
        avgfile = os.path.join(os.path.dirname(os.path.dirname(folders[0])), args.outfile) # in base dir
        hlpmisc.backup_if_exists(avgfile)
        avg_kl = np.average(kl, axis=0)
        stddev = np.std(kl, axis=0, ddof=1)
        np.savetxt(avgfile, np.vstack((times, avg_kl, stddev)).T, header=avgheader,
                   delimiter=' ', newline='\n')
