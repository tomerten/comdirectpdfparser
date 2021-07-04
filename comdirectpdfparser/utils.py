# -*- coding: utf-8 -*-

"""
Module comdirectpdfparser.utils 
=================================================================

A module with utilities for the ComDirect REGEX parser class.

"""
from tika import parser


def readRaw(_file):
    """
    Read raw pdf data from file.

    Arguments :
    -----------
    str	: _file
        PDF file to open.

	Returns:
	--------
	dict
		tika dict read from file
    """

    return parser.from_file(_file)

def stringToNumber(s):
    """
    Rudimentary string to float conversion
    if the string representation contains both 
    comma and dot.
    
    Pythonic way would be using locale, but
    leads to problems on mac, keep this
    method for the time being.

    Parameters:
    -----------
    s: str
        string to convert to float
    """
    s = float(s.replace('.','').replace(',','.'))
    return s