'''
__main__: main command-line interface to Holdit!

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   docxtpl import DocxTemplate
import os
import os.path as path
import plac
import sys

import holdit
from holdit.access import AccessHandlerGUI, AccessHandlerCLI
from holdit.records import records_diff, records_filter
from holdit.tind import records_from_tind
from holdit.google_sheet import records_from_google, update_google, open_google
from holdit.generate import generate_printable_doc
from holdit.messages import color, msg, MessageHandlerGUI, MessageHandlerCLI
from holdit.network import network_available
from holdit.files import readable, open_file, rename_if_exists, desktop_path
from holdit.exceptions import *


# Main program.
# ......................................................................

@plac.annotations(
    pswd       = ('Caltech access user password',                    'option', 'p'),
    user       = ('Caltech access user name',                        'option', 'u'),
    output     = ('write the output to the file "O"',                'option', 'o'),
    template   = ('use file "F" as the TIND record print template',  'option', 't'),
    no_color   = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    no_gui     = ('do not start the GUI interface (default: do)',    'flag',   'G'),
    no_keyring = ('do not use a keyring (default: do)',              'flag',   'K'),
    no_sheet   = ('do not open the spreadsheet (default: open it)',  'flag',   'S'),
    reset      = ('reset keyring stored user name and password',     'flag',   'R'),
    version    = ('print version info and exit',                     'flag',   'V'),
)

def main(user = 'U', pswd = 'P', output='O', template='F',
         no_color=False, no_gui=False, no_keyring=False, no_sheet=False,
         reset=False, version=False):
    '''Generate a printable Word document containing recent hold requests and
also update the relevant Google spreadsheet used for tracking requests.

By default, Holdit! uses a GUI dialog to get the user's Caltech access login
name and password.  If the -G option is given (/G on Windows), it will not
use a GUI dialog, and will instead use the operating system's
keyring/keychain functionality to get a user name and password.  If the
information does not exist from a previous run of Holdit!, it will query the
user interactively for the user name and password, and (unless the -K or /K
argument is given) store them in the user's keyring/keychain so that it does
not have to ask again in the future.  It is also possible to supply the
information directly on the command line using the -u and -p options (or /u
and /p on Windows), but this is discouraged because it is insecure on
multiuser computer systems.

To reset the user name and password (e.g., if a mistake was made the last
time and the wrong credentials were stored in the keyring/keychain system),
use the -R (or /R on Windows) command-line argument to a command.  This
argument will make Holdit! query for the user name and password again even if
an entry already exists in the keyring or keychain.

By default, Holdit! looks for a .docx file named "template.docx" in the
directory where Holdit! is located, and uses that as the template for record
printing.  If given the -t option followed by a file name (/t on Windows), it
will look for the named file instead.  If it is not given an explicit
template file and it cannot find a file "template.docx", Holdit! will use a
built-in default template file.

By default, Holdit! will also open the Google spreadsheet used by the
Circulation staff to track hold requests.  This action is inhibited if given
the -S option (/S on Windows).  The Google spreadsheet is always updated in
any case.

Holdit! will write the output to a file named "holds_print_list.docx" in the
user's Desktop directory, unless the -o option (/o on Windows) is given with
an explicit file path to use instead.

If given the -V option (/V on Windows), this program will print version
information and exit without doing anything else.
'''

    # Our defaults are to do things like color the output, which means the
    # command line flags make more sense as negated values (e.g., "no-color").
    # However, dealing with negated variables in our code is confusing, so:
    use_color   = not no_color
    use_keyring = not no_keyring
    use_gui     = not no_gui
    view_sheet  = not no_sheet

    # We use default values that provide more intuitive help text printed by
    # plac.  Rewrite the values to things we actually use.
    if user == 'U':
        user = None
    if pswd == 'P':
        pswd = None
    if template == 'F':
        template = None
    if output == 'O':
        output = None

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
            accesser = AccessHandlerGUI(user, pswd)
            notifier = MessageHandlerGUI()
        else:
            accesser = AccessHandlerCLI(user, pswd, use_keyring, reset)
            notifier = MessageHandlerCLI(use_color)

        # Try to find the user's template, if any is provided.
        template_path = None
        if template:
            template_path = path.abspath(template)
            if not readable(template_path):
                template_path = None
                msg('File "{}" not not readable -- using default.'.format(template),
                    'warn', colorize)

        # Get the data.
        tind_records = records_from_tind(accesser, notifier)
        google_records = records_from_google(notifier)
        missing_records = records_diff(google_records, tind_records)
        new_records = list(filter(records_filter('all'), missing_records))

        if len(new_records) > 0:
            # Update the spreadsheet with new records.
            update_google(new_records, notifier)
            # Write a printable report.
            if not output:
                output = path.join(desktop_path(), "holds_print_list.docx")
            rename_if_exists(output, notifier)
            result = generate_printable_doc(new_records, template_path)
            result.save(output)
            open_file(output)
        else:
            notifier.note('No new hold requests were found in TIND.')
        # Open the spreadsheet too, if requested.
        if use_gui:
            if notifier.yes_no('Open the tracking spreadsheet?'):
                open_google()
        elif view_sheet:
            open_google()
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
