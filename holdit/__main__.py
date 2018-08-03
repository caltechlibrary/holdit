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
import sys

import holdit
from holdit.access import AccessHandlerGUI, AccessHandlerCLI
from holdit.tind import tind_json, tind_records_from_json
from holdit.generate import generate_printable_list
from holdit.messages import color, msg, MessageHandlerGUI, MessageHandlerCLI
from holdit.network import network_available
from holdit.exceptions import *


# Main program.
# ......................................................................

@plac.annotations(
    pswd       = ('Caltech access user password',                    'option', 'p'),
    user       = ('Caltech access user name',                        'option', 'u'),
    no_color   = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    no_gui     = ('do not start the GUI interface (default: do)',    'flag',   'G'),
    no_keyring = ('do not use a keyring (default: do)',              'flag',   'K'),
    reset      = ('reset keyring stored user name and password',     'flag',   'R'),
    version    = ('print version info and exit',                     'flag',   'V'),
)

def main(user = 'U', pswd = 'P', no_color=False, no_gui=False, no_keyring=False,
         reset=False, version=False):
    '''Generate a list of current hold requests.

By default, Holdit uses a GUI dialog to get the user's Caltech access login
name and password.  If the -G option is given (/G on Windows), it will not
use a GUI dialog, and will instead use the operating system's
keyring/keychain functionality to get a user name and password.  If the
information does not exist from a previous run of Holdit, it will query the
user interactively for the user name and password, and (unless the -K or /K
argument is given) store them in the user's keyring/keychain so that it does
not have to ask again in the future.  It is also possible to supply the
information directly on the command line using the -u and -p options (or /u
and /p on Windows), but this is discouraged because it is insecure on
multiuser computer systems.

To reset the user name and password (e.g., if a mistake was made the last
time and the wrong credentials were stored in the keyring/keychain system),
add the -R (or /R on Windows) command-line argument to a command.  This
argument will make Holdit query for the user name and password again even if
an entry already exists in the keyring or keychain.

If given the -V option (/V on Windows), this program will print version
information and exit without doing anything else.
'''

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "no-color").
    # However, dealing with negated variables in our code is confusing, so:
    use_color   = not no_color
    use_keyring = not no_keyring
    use_gui     = not no_gui

    # We use default values that provide more intuitive help text printed by
    # plac.  Rewrite the values to things we actually use.
    if user == 'U':
        user = None
    if pswd == 'P':
        pswd = None

    # Process the version argument first, because it causes an early exit.
    if version:
        print('{} version {}'.format(holdit.__title__, holdit.__version__))
        print('Author: {}'.format(holdit.__author__))
        print('URL: {}'.format(holdit.__url__))
        print('License: {}'.format(holdit.__license__))
        sys.exit()

    # Perform general sanity checks.
    if not network_available():
        raise SystemExit(color('No network', 'error', use_color))
    if use_gui and no_keyring:
        msg('Warning: keyring flag ignored when using GUI', 'warn', use_color)
    if use_gui and reset:
        msg('Warning: reset flag ignored when using GUI', 'warn', use_color)

    # If the user left the gui option as default (meaning, use gui), we may
    # still have to resort to non-gui operation if the command line contained
    # options that implicate non-gui actions.
    try:
        if use_gui:
            credentials_handler = AccessHandlerGUI(user, pswd)
            message_handler = MessageHandlerGUI()
        else:
            credentials_handler = AccessHandlerCLI(user, pswd, use_keyring, reset)
            message_handler = MessageHandlerCLI(use_color)
        data = tind_json(credentials_handler, message_handler)
        records = tind_records_from_json(data)
        generate_printable_list(records)
    except (KeyboardInterrupt, UserCancelled):
        if no_gui:
            msg('Quitting.', 'warn', use_color)
        sys.exit()
    if no_gui:
        msg('Done.', 'info', use_color)


# On windows, we want the command-line args to use slash intead of hyphen.

if sys.platform.startswith('win'):
    main.prefix_chars = '/'


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
