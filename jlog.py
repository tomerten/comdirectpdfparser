# -*- coding: utf-8 -*-

"""
Module comdirectpdfparser.jlog 
=================================================================

A module

"""
import json
import logging


class JSONFormatter(logging.Formatter):
    """Format message as one line of JSON"""

    def format(self, record):
        obj = vars(record)
        obj['message'] = record.getMessage()

        # JSON can't handle exc_info, use default format as string
        if obj['exc_info']:
            obj['exc_info'] = self.formatException(obj['exc_info'])

        # Delete internal fields
        for key in ('msg', 'args'):
            del obj[key]

        return json.dumps(obj)