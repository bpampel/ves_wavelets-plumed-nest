#!/usr/bin/env python3
"""Parse and create headers of plumed data files"""

class PlumedHeader:
    """
    Stores plumed file header in list
    Can parse and create similar headers for usage in python tools
    """

    def __init__(self, header=None):
        self.data = []
        self.set(header)

    def __getitem__(self, index):
        return self.data[index]

    def __setitem__(self, index, line):
        self.data[index] = line

    def __delitem__(self, index):
        del self.data[index]

    def __repr__(self):
        """
        Returns header as string with newlines to be printed to file
        Can be used directly as header argument to numpys savetxt
        """
        return '\n'.join(self.data)


    def parse_file(self, filename):
        """
        Saves header of a plumed file as list of lines
        The header is assumed to be the first lines of the file that start with #!
        """
        header = []
        with open(filename) as f:
            for line in f:
                if line.startswith('#!'):
                    header.append(line.rstrip('\n'))
                else:
                    self.data = header
                    return


    def add_line(self, line, pos=-1):
        """
        Insert header line at given position (line number starting with 0)
        Defaults to -1 (append)
        This will prepend #! at the start of the line automatically
        """
        headerline = '#! ' + line
        if pos == -1:
            self.data.append(headerline)
        else:
            self.data.insert(pos, headerline)

    def del_lines(self, pos):
        """
        Delete header lines at given positions
        Requires a list of integers.
        Line numbers are starting with 0
        """
        for i in sorted(pos, reverse=True):
            del self.data[i]


    def set(self, header):
        """
        Set header to given list of strings
        Will overwrite existing header
        """
        if header is None:
            header = []
        self.data = header


    def search_lines(self, string):
        """
        Get all lines containing string
        Returns list of tuples (linenumber, line)
        """
        return [(i, line) for i, line in enumerate(self.data) if string in line]
