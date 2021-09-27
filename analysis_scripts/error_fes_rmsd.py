#!/usr/bin/env python3
"""
Calculates error of a FES calculation
Averages pointwise over a set of FES and calculates the standart deviation.
Compares the average values pointwise to a reference FES for the bias.
Combination of both gives the total error.
"""

import argparse
from functools import partial
import os
from multiprocessing import Pool
import numpy as np
from scipy.spatial.distance import pdist
from helpers import misc as hlpmisc
from helpers import plumed_header as plmdheader


def parse_args():
    """Get cli args"""
    parser = argparse.ArgumentParser()
    parser.add_argument('path',
                        help="Path to the folder to be evaluated")
    parser.add_argument('-r', '--ref',
                        help="Path to the reference FES file",
                        required=True)
    parser.add_argument('-kT', '--kT', type=float,
                        help="Value of kT for the FES file (in matching units)",
                        required=True)
    parser.add_argument("-o", "--outfile",
                        help='Name of the file for the error values. Default is "error.txt"',
                        default="error.txt")
    parser.add_argument("-st", "--shift-threshold", type=float, dest='shift_threshold',
                        help="Threshold value of FES (in units of kT) for shifting area. Defaults to 4",
                        default="4.0")
    parser.add_argument("-et", "--error-threshold", type=float, dest='error_threshold',
                        help="Threshold value of FES (in units of kT) for error area. Defaults to 8",
                        default="8.0")
    parser.add_argument('--cv-range', nargs='+', type=float, dest='cv_range',
                        help="CV range to be taken into account. Requires 2 values separated by spaces. \
                              Will be ignored for more than 2 dimensions")
    parser.add_argument("-np", "--numprocs", type=int, default="1",
                        help="Number of parallel processes")
    parser.add_argument("-em", "--error-metric", dest='error_metric', default='rmsd',
                        help="Metric for combining the errors. \
                              Accepts 'absolute' (mean absolute error) and 'rmsd'. Defaults to 'rmsd'")
    args = parser.parse_args()
    if args.cv_range and len(args.cv_range) != 2:
        raise ValueError("--cv-range requires 2 values separated by spaces")
    if args.error_metric not in ['absolute', 'rmsd']:
        raise ValueError("Metric must be 'absolute' or 'rmsd'")
    return args


def calculate_error(filepath, dim, shift_region, error_region, ref, metric='rsmd'):
    """ Calculate error of FES wrt reference

    This shifts the read in FES by the average in the given region and then calculates the
    pointwise distance with a given metric. It returns the average distance in the region of interest.

    Arguments
    ---------
    filepath      : paths to FES to analyze
    dim           : dimensions of FES
    shift_region  : numpy array with booleans for the regions to consider for aligning data
    error_region  : numpy array with booleans for the regions to consider for error calculation
    ref           : numpy array holding the reference values
    metric        : used metric for averaging errors. Accepts either 'absolute' or 'rms'

    Returns
    -------
    error         : float with the average error value in error_region
    """
    fes = np.transpose(np.genfromtxt(filepath))[dim]  # throw away colvar
    # exclude areas with inf in fes
    valid_fes_region = fes < np.inf
    valid_shift_region = np.bitwise_and(shift_region, valid_fes_region)
    valid_error_region = np.bitwise_and(error_region, valid_fes_region)
    refshift = np.average(ref[valid_shift_region])
    fes = fes - np.average(fes[valid_shift_region]) + refshift
    if metric == 'absolute':
        error = np.abs(fes - ref)
        return np.average(error[valid_error_region])
    elif metric == 'rmsd':
        error = (fes - ref)**2
        return np.sqrt(np.average(error[valid_error_region]))
    else:
        raise ValueError("Metric must be 'absolute' or 'rmsd'")


def main():
    args = parse_args()

    # define some constants and empty arrays for storage
    shift_threshold = args.kT * args.shift_threshold
    error_threshold = args.kT * args.error_threshold
    cv_region = True # full range by default
    fmt_times = '%10d'
    fmt_error = '%14.9f'

    # read reference and determine dimensions
    try:
        ref = np.genfromtxt(args.ref).T
    except IOError:
        print("Reference file not found!")
    dim = ref.shape[0] - 1
    colvar = ref[0:dim]
    ref = ref[dim]

    # get folders and files
    folders = hlpmisc.get_subfolders(args.path)
    if len(folders) == 0:
        raise ValueError("No subfolders found at specified path.")
    files, times = hlpmisc.get_fesfiles(folders[0])  # assumes all folders have the same files

    # determine regions of interest and create arrays of booleans
    if args.cv_range and dim==1: # missing implementation for higher dimensions
        if args.cv_range[0] < colvar[0] or args.cv_range[1] > colvar[-1]:
            raise ValueError("Specified CV range is not contained in reference range [{}, {}]"
                             .format(colvar[0], colvar[-1]))
        cv_region = np.bitwise_and(colvar >= args.cv_range[0], colvar <= args.cv_range[1])
    shift_region = np.bitwise_and(ref < shift_threshold, cv_region)
    error_region = np.bitwise_and(ref < error_threshold, cv_region)

    # everything set up, now calculate errors for all files
    filepaths = [os.path.join(d, f) for d in folders for f in files]
    pool = Pool(processes=args.numprocs)
    errors = pool.map(partial(calculate_error, dim=dim, shift_region=shift_region,
                              error_region=error_region, ref=ref, metric=args.error_metric),
                      filepaths)
    errors = np.array(errors).reshape(len(folders),len(files))  # put in matrix form

    # write error for each folder to file
    fields = ["time", "error"]
    fileheader = plmdheader.PlumedHeader(fields)
    fileheader.set_constant("kT", args.kT)
    fileheader.set_constant("shift_threshold", args.shift_threshold)
    fileheader.set_constant("error_threshold", args.error_threshold)
    fileheader.set_constant("error_metric", args.error_metric)
    fmt = [fmt_times] + [fmt_error]
    for i, folder in enumerate(folders):
        errorfile = os.path.join(folder, args.outfile)
        hlpmisc.backup_if_exists(errorfile)
        np.savetxt(errorfile, np.vstack((times, errors[i])).T, header=str(fileheader),
                   comments='', fmt=fmt, delimiter=' ', newline='\n')

    # calculate average and stddev
    avg_error = np.average(errors, axis=0)
    stddev = np.std(errors, axis=0, ddof=1)
    # write to file
    avgfile = os.path.join(args.path, args.outfile)  # in base dir
    hlpmisc.backup_if_exists(avgfile)
    fileheader.fields = ["time", "avg_error", "stddev"]
    fileheader.set_constant('nruns_avg', len(folders))
    fmt.append(fmt_error)
    np.savetxt(avgfile, np.vstack((times, avg_error, stddev)).T, header=str(fileheader),
               comments='', fmt=fmt, delimiter=' ', newline='\n')


if __name__ == '__main__':
    main()
