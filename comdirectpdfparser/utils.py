# -*- coding: utf-8 -*-

"""
Module comdirectpdfparser.utils 
=================================================================

A module with utilities for the ComDirect REGEX parser class.

"""
from tika import parser


def readRaw(_file: str) -> dict:
    """Read raw pdf data from file.

    Args:
        _file (str): PDF file to open

    Returns:
        dict: tika dict read from file
    """

    return parser.from_file(_file)


def stringToNumber(s: str) -> float:
    """Rudimentary string to float conversion if the string representation
    contains both comma and dot.

    Pythonic way would be using locale, but this leads to problems on mac,
    keep this method for the time being.

    Args:
        s (str): string to convert to float

    Returns:
        float: float value of the input string
    """

    s = float(s.replace(".", "").replace(",", "."))
    return s
