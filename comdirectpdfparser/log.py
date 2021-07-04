# -*- coding: utf-8 -*-

"""
Module comdirectpdfparser.log 
=================================================================

A module

"""
import logging
import logging.config
from os import environ
from pathlib import Path
from threading import Lock

here = Path(__file__).absolute().parent
default_config_file = here / 'log.ini'
env_key = 'NLP_LOG_CONFIG_FILE'

_lock = Lock()
_configured = False


# Disallow using of logging system before it's configured
def _uninitialized(*args, **kwargs):
    raise RuntimeError('logging system not configured')


debug = info = warning = error = fatal = exception = get_logger = _uninitialized


def setup(config_file=None):
    """Setup configuration system from config file (.ini format)"""
    global _configured
    global debug, info, warning, error, fatal, exception, get_logger

    with _lock:
        if _configured:
            return

        if not config_file:
            config_file = environ.get(env_key, default_config_file)

        logging.config.fileConfig(config_file)

        # Set real functions
        debug = logging.debug
        info = logging.info
        warning = logging.warning
        fatal = logging.fatal
        exception = logging.exception
        get_logger = logging.getLogger

        _configured = True

