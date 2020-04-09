#!/usr/bin/env python3
"""Parse and use C and numpy style format strings for usage with python"""

import re

class NumberFmt:
    """
    Class to store format of numbers
    """

    def __init__(self, number=None):
        self.flags = ''
        self.specifier = 'f'
        self.width = 14
        self.precision = 9
        if number is not None:
            self.parse(number)


    def parse(self, number):
        """
        Parse format of number string.
        It is not possible to determine all flags from single number, but works for most cases.
        """
        try:
            float(number)
        except ValueError:
            print("String is not a number")

        self.width = len(number)

        # test for signed flag
        leading_spaces = len(number) - len(number.lstrip(' '))
        if number[leading_spaces] == '+': # '-' is ambiguous
            self.flags ='+'

        dot_position = number.find('.')
        if dot_position == -1: # number is an integer
            self.specifier = 'd'
            self.precision = None
            return

        # check for exponential format
        for e in ['e', 'E']:
            e_position = number.find(e)
            if e_position != -1:
                self.specifier = e
                self.precision = e_position - dot_position - 1
                return

        self.specifier = 'f'
        self.precision = len(number) - dot_position - 1
        return


    def get(self):
        """Return format as C style string"""
        if self.precision:
            fmt_str = "%{}{}.{}{}".format(self.flags, self.width, self.precision, self.specifier)
        else:
            fmt_str = "%{}{}{}".format(self.flags, self.width, self.specifier)
        return fmt_str


    def set(self, format_string):
        """Set class variables to the given Cg type string"""
        if format_string[0] != '%':
            raise ValueError("Not a C style number format")
        if not format_string[1].isdigit():
            self.flags = format_string[1]
        self.width = int(''.join(filter(str.isdigit, format_string.split('.')[0])))
        self.precision= int(''.join(filter(str.isdigit, format_string.split('.')[1])))
        self.specifier = format_string[-1]


def get_string_from_file(filename, col):
    """
    Get number string of file from the first non-header line and the given column
    Tested only with plumed files
    """
    with open(filename) as f:
        for line in f:
            if line.startswith('#'):
                continue
            pat = re.compile('\s*[\d+-.]+') # columns with trailing whitespace
            numstring = pat.findall(line)[col]
            return numstring[1::] # remove delimiting whitespace


if __name__ == '__main__':
    numbers = ['21.5624', '1.6345e-05', '+6.276E+02', '3122225', '-2.43123', '  -63214', '  +3.541']
    for num in numbers:
        fmt = NumberFmt(num)
        formatted_num = fmt.get() % (float(num))
        print(num + ': ' + fmt.get() + ' -> ' + formatted_num)
