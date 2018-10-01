'''
debug.py: debugging aids for Holdit!

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import holdit


# Logger configuration.
# .............................................................................

if __debug__:
    import logging
    holdit_logger = logging.getLogger('holdit')
    formatter     = logging.Formatter('%(name)s: %(message)s')
    handler       = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    holdit_logger.addHandler(handler)


# Exported functions.
# .............................................................................

def set_debug(enabled):
    '''Turns on debug logging if 'enabled' is True; turns it off otherwise.'''
    if __debug__:
        from logging import DEBUG, WARNING
        logging.getLogger('holdit').setLevel(DEBUG if enabled else WARNING)


def log(s, *other_args):
    '''Logs a debug message. 's' can contain format directive, and the
    remaining arguments are the arguments to the format string.'''
    if __debug__:
        logging.getLogger('holdit').debug(s.format(*other_args))
