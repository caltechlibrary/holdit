'''
__main__: main command-line interface to Holdit.

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

import os
import os.path as path
import plac
import requests
import sys
try:
    from termcolor import colored
except ImportError:
    pass

import holdit
from holdit.gui import credentials_from_gui
from holdit.messages import color, msg
from holdit.generate import generate_hold_list
from holdit.credentials import password, credentials
from holdit.credentials import keyring_credentials, save_keyring_credentials

# NOTE: to turn on debugging, make sure python -O was *not* used to start
# python, then set the logging level to DEBUG *before* loading this module.
# Conversely, to optimize out all the debugging code, use python -O or -OO
# and everything inside "if __debug__" blocks will be entirely compiled out.
if __debug__:
    import logging
    logging.basicConfig(level = logging.INFO)
    logger = logging.getLogger('holdit')
    def log(s, *other_args): logger.debug('holdit: ' + s.format(*other_args))


# Global constants.
# .............................................................................

_KEYRING = "org.caltechlibrary.holdit"
'''
The name of the keyring used to store Caltech access credentials, if any.
'''


# Main program.
# ......................................................................

@plac.annotations(
    pswd       = ('Caltech access user password',                    'option', 'p'),
    user       = ('Caltech access user name',                        'option', 'u'),
    no_color   = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    no_gui     = ('do not start the GUI interface (default: do)',    'flag',   'G'),
    reset      = ('reset stored user name and password',             'flag',   'R'),
    version    = ('print version info and exit',                     'flag',   'V'),
    no_keyring = ('do not use a keyring (default: do)',              'flag',   'X'),
)

def main(user = 'U', pswd = 'P', no_color=False, no_gui=False,
         reset=False, no_keyring=False, version=False):
    '''Generate a list of current hold requests.'''

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "nocolor").
    # Dealing with negated variables is confusing, so turn them around here.
    colorize = 'termcolor' in sys.modules and not no_color
    use_keyring = not no_keyring
    use_gui = not no_gui

    # Some user interactions change depending on the current platform.
    on_windows = sys.platform.startswith('win')

    # We use default values that provide more intuitive help text printed by
    # plac.  Rewrite the values to things we actually use.
    if user == 'U':
        user = None
    if pswd == 'P':
        pswd = None
    if on_windows:
        get_help = '(Hint: use /h to get help.)'
    else:
        get_help = '(Hint: use -h to get help.)'

    # Process the version argument first, because it causes an early exit.
    if version:
        print('{} version {}'.format(holdit.__title__, holdit.__version__))
        print('Author: {}'.format(holdit.__author__))
        print('URL: {}'.format(holdit.__url__))
        print('License: {}'.format(holdit.__license__))
        sys.exit()

    # General sanity checks.
    if not network_available():
        raise SystemExit(color('No network', 'error', colorize))

    # If the user left the gui option as default (meaning, use gui), we may
    # still have to resort to non-gui operation if the command line contained
    # options that implicate non-gui actions.
    try:
        if use_gui and not any([user, pswd, reset, no_keyring]):
            if __debug__: log('Invoking GUI')
            user, pswd, cancel = credentials_from_gui()
            if cancel:
                if __debug__: log('User initiated quit from within GUI')
                sys.exit()
        elif not all([user, pswd]) or reset or no_keyring:
            user, pswd = credentials_from_keyring(user, pswd, use_keyring, reset)
        generate_hold_list(user, pswd)
    except KeyboardInterrupt:
        if no_gui:
            msg('Quitting.', 'warn', colorize)
        sys.exit()

# If this is windows, we want the command-line args to use slash intead
# of hyphen.

if sys.platform.startswith('win'):
    main.prefix_chars = '/'


# Miscellaneous utilities.
# ......................................................................

def network_available():
    '''Return True if it appears we have a network connection, False if not.'''
    try:
        r = requests.get("https://www.caltech.edu")
        return True
    except requests.ConnectionError:
        if __debug__: log('Could not connect to https://www.caltech.edu')
        return False


def credentials_from_keyring(user, pswd, use_keyring, reset):
    if not user or not pswd or reset:
        if use_keyring and not reset:
            if __debug__: log('Getting credentials from keyring')
            user, pswd, _, _ = credentials(_KEYRING, "Caltech access login", user, pswd)
        else:
            if use_keyring:
                if __debug__: log('Keyring disabled')
            if reset:
                if __debug__: log('Reset invoked')
            user = input('Caltech access login: ')
            pswd = password('Password for "{}": '.format(user))
    if use_keyring:
        # Save the credentials if they're different from what's currently saved.
        s_user, s_pswd, _, _ = keyring_credentials(_KEYRING)
        if s_user != user or s_pswd != pswd:
            if __debug__: log('Saving credentials to keyring')
            save_keyring_credentials(_KEYRING, user, pswd)
    return user, pswd


# Main entry point.
# ......................................................................
# The following allows users to invoke this using "python3 -m holdit".

if __name__ == '__main__':
    plac.call(main)


# For Emacs users
# ......................................................................
# Local Variables:
# mode: python
# python-indent-offset: 4
# End:
