#!/usr/bin/env/python3
import glob
import os


def get_fesfiles(directory):
    """
    Returns the names of all fes files sorted by time and the respective times

    Arguments
    ---------
    directory : base directory of the files

    Returns
    -------
    (files, times) : A tuple of two elements
    files   : a list of all filenames sorted by increasing time
    times   : a list of the respective times of the files
    """
    files = [os.path.basename(f) for f in glob.glob(directory + "fes.b1.iter*")]
    times = [extract_time(f) for f in files]
    files = [i for _, i in sorted(zip(times, files))]
    times = sorted(times)
    return (files, times)


def get_subfolders(basedir):
    """
    Returns all numbered subfolders

    Arguments
    ---------
    basedir : base directory of the search

    Returns
    -------
    folders : a list of all numbered directories (with trailing '/')
    """
    return glob.glob(basedir + os.path.sep + "[0-9]*" + os.path.sep)


def extract_time(x):
    """
    Get time from filename of fes file

    Arguments
    ---------
    x : name of fes file

    Returns
    -------
    time : int
    """
    return int(''.join(i for i in x if i.isdigit())[1:])


def backup_if_exists(name):
    """
    Cascade of backups with format 'bck.$num.name'

    Arguments
    ---------
    name : name of file or directory

    Returns
    -------
    Nothing
    """
    if os.path.exists(name):
        d, f = os.path.split(name)
        backupnum = 0
        while os.path.exists(os.path.join(d, 'bck.'+str(backupnum)+'.'+f)):
            backupnum += 1
        os.rename(name, os.path.join(d, 'bck.'+str(backupnum)+'.'+f))


def prefix_filename(path, prefix):
    """
    Add prefix to filename
    Works with both a single filename and a longer path

    Arguments
    ---------
    path   : filename or full path
    prefix : prefix to add to filename

    Returns
    -------
    prefixed path
    """
    d, f = os.path.split(path)
    f = prefix + f
    return os.path.join(d, f)
