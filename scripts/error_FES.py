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
from helpers import misc as hlpmisc
from helpers import number_format as nfmt
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
    parser.add_argument("--avgdir",
                        help='Name of the directory for the average file. Default is "avg"',
                        default="avg")
    parser.add_argument("--errorfile",
                        help='Name of the file for the error values. Default is "error.txt"',
                        default="error.txt")
    parser.add_argument("-st", "--shifting_threshold", type=float,
                        help="Threshold value of FES (in units of kT) for shifting area. Defaults to 4",
                        default="4.0")
    parser.add_argument("-et", "--error_threshold", type=float,
                        help="Threshold value of FES (in units of kT) for error area. Defaults to 8",
                        default="8.0")
    parser.add_argument('--cv-range', nargs='+', type=float,
                        help='CV range to be taken into account. Requires 2 values separated by spaces. \
                              Will be ignored for more than 2 dimensions')
    parser.add_argument("-np", "--numprocs", type=int, default="1",
                        help="Number of parallel processes")
    args = parser.parse_args()
    if args.cv_range and len(args.cv_range) != 2:
        raise ValueError("--cv-range requires 2 values separated by spaces")
    return args


def calculate_error(filenames, avgdir, colvar, shift_region, error_region, ref, refshift):
    """
    Function doing the actual work.

    Arguments
    ---------
    filenames     : list with paths of all filenames to analyze
    avgdir        : directory to save averaged fes
    colvar        : numpy array holding the colvar values
    shift_region  : numpy array with booleans for the regions to consider for aligning data
    error_region  : numpy array with booleans for the regions to consider for error calculation
    ref           : numpy array holding the reference values
    ref_shift_avg : average value of ref in shift region

    Returns
    -------
    [avgstddev, avgbias, avgerror] : list of three floats
    avgstddev     : average standard deviation in error region
    avgbias       : average bias in error region
    avgerror      : combination of both error measures
    """
    dim, num_datapoints = colvar.shape
    data = np.empty([len(folders), num_datapoints], dtype=float)

    # loop over all folders
    for j, filename in enumerate(filenames):
        data[j] = np.transpose(np.genfromtxt(filename))[dim] # throw away colvar

    # all data is read, calculate error measures
    avgdata = np.average(data, axis=0)
    stddev = np.std(data, axis=0, ddof=1, dtype=np.float64)
    avgstddev = np.average(np.extract(error_region, stddev))

    avgshift = np.average(np.extract(shift_region, avgdata))
    avgdata = avgdata - avgshift + refshift

    # calculate bias
    bias = np.absolute(avgdata - ref)
    avgbias = np.average(np.extract(error_region, bias))

    # add to recieve total error
    error = np.sqrt(stddev**2 + bias**2)
    avgerror = np.average(np.extract(error_region, error))

    # copy header from one infile and add fields
    fileheader = plmdheader.PlumedHeader()
    fileheader.parse_file(filenames[0])
    fileheader[0] += ' stddev bias error'
    fileheader.add_line('SET nruns_avg {}'.format(len(filenames)))
    fileheader.add_line('SET error_threshold {}'.format(error_threshold))

    # parse number format from FES file
    fmt_str = nfmt.get_string_from_file(filenames[0], dim)
    fmt = nfmt.NumberFmt(fmt_str)

    # write data of current time to file
    outfile = os.path.join(avgdir, os.path.basename(filenames[0]))
    outdata = np.transpose(np.vstack((colvar, avgdata, stddev, bias, error)))
    if dim == 1:
        np.savetxt(outfile, np.asmatrix(outdata), header=str(fileheader),
                   comments='', fmt=fmt.get(), delimiter=' ', newline='\n')
    if dim == 2:
        # find out number of bins per direction from header
        nbins = []
        for line in fileheader.search_lines('nbins'):
            nbins.append(int(line[1].split(' ')[-1]))
        write_sliced_to_file(outdata, nbins, outfile, fileheader, fmt.get())

    return [avgstddev, avgbias, avgerror]


def write_sliced_to_file(data, nbins, filename, header, fmts):
    """
    Writes 2d data to file including a newline after every row

    Arguments
    ---------
    data          : numpy array contaning positions and data information
    nbins         : list with bin numbers per direction
    filename      : path to write to
    header        : plumed_header to write to file
    fmts          : single format or list of formats for the data columns

    Returns
    -------
    Nothing
    """
    data = data.reshape(*nbins, len(data[0])) # split into rows
    with open(filename, 'w') as outfile:
        outfile.write(str(header) + '\n')
        for row in data[:-1]:
            np.savetxt(outfile, row, comments='', fmt=fmts,
                       delimiter=' ', newline='\n')
            outfile.write('\n')
        np.savetxt(outfile, data[-1], comments='', fmt=fmts,
                   delimiter=' ', newline='\n')


if __name__ == '__main__':
    args = parse_args()

    # define some constants and empty arrays for storage
    shift_threshold = args.kT * args.shifting_threshold
    shift_threshold = args.kT * args.shifting_threshold
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
    files, times = hlpmisc.get_fesfiles(folders[0]) # assumes all folders have the same files

    # determine regions of interest and create arrays of booleans
    if args.cv_range and dim==1: # missing implementation for higher dimensions
        if args.cv_range[0] < colvar[0] or args.cv_range[1] > colvar[-1]:
            raise ValueError("Specified CV range is not contained in reference range [{}, {}]"
                             .format(colvar[0], colvar[-1]))
        cv_region = np.array([colvar >= args.cv_range[0]]) & np.array([colvar <= args.cv_range[1]])
    shift_region = np.array([ref < shift_threshold]) & cv_region
    error_region = np.array([ref < error_threshold]) & cv_region
    refshift = np.average(np.extract(shift_region, ref))

    hlpmisc.backup_if_exists(args.avgdir)
    os.mkdir(args.avgdir)

    # everything set up, now do the analysis for each time seperately
    filenames = [[os.path.join(d, f) for d in folders] for f in files]
    pool = Pool(processes=args.numprocs)
    avgvalues = pool.map(partial(calculate_error, avgdir=args.avgdir, colvar=colvar,
                                 shift_region=shift_region, error_region=error_region,
                                 ref=ref, refshift=refshift),
                         filenames)

    # write averaged values to file
    hlpmisc.backup_if_exists(args.errorfile)
    errordata = np.column_stack((times, avgvalues))
    errorheader = plmdheader.PlumedHeader()
    errorheader.add_line("FIELDS time stddev bias total_error")
    errorheader.add_line("SET kT {}".format(args.kT))
    errorheader.add_line("SET error_threshold {}".format(args.error_threshold))
    fmt = [fmt_times] + 3*[fmt_error]
    np.savetxt(args.errorfile, np.asmatrix(errordata), header=str(errorheader),
               comments='', fmt=fmt, delimiter=' ', newline='\n')
