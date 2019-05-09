'''
__main__: main command-line interface to Hold It!

Hold It! generates a printable Word document containing recent hold requests and
also update the relevant Google spreadsheet used for tracking requests.

By default, Hold It! uses a GUI dialog to get the user's Caltech access login
name and password.  If the -G option is given (/G on Windows), it will not
use a GUI dialog, and will instead use the operating system's
keyring/keychain functionality to get a user name and password.  If the
information does not exist from a previous run of Hold It!, it will query the
user interactively for the user name and password, and (unless the -K or /K
argument is given) store them in the user's keyring/keychain so that it does
not have to ask again in the future.  It is also possible to supply the
information directly on the command line using the -u and -p options (or /u
and /p on Windows), but this is discouraged because it is insecure on
multiuser computer systems.

To reset the user name and password (e.g., if a mistake was made the last
time and the wrong credentials were stored in the keyring/keychain system),
use the -R (or /R on Windows) command-line argument to a command.  This
argument will make Hold It! query for the user name and password again even if
an entry already exists in the keyring or keychain.

By default, Hold It! looks for a .docx file named "template.docx" in the
directory where Hold It! is located, and uses that as the template for record
printing.  If given the -t option followed by a file name (/t on Windows), it
will look for the named file instead.  If it is not given an explicit
template file and it cannot find a file "template.docx", Hold It! will use a
built-in default template file.

By default, Hold It! will also open the Google spreadsheet used by the
Circulation staff to track hold requests.  This action is inhibited if given
the -S option (/S on Windows).  The Google spreadsheet is always updated in
any case.

Hold It! will write the output to a file named "holds_print_list.docx" in the
user's Desktop directory, unless the -o option (/o on Windows) is given with
an explicit file path to use instead.

If given the -V option (/V on Windows), this program will print version
information and exit without doing anything else.

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
import time
from   threading import Thread
import traceback

import holdit
from holdit.control import HoldItControlGUI, HoldItControlCLI
from holdit.access import AccessHandlerGUI, AccessHandlerCLI
from holdit.progress import ProgressIndicatorGUI, ProgressIndicatorCLI
from holdit.messages import MessageHandlerGUI, MessageHandlerCLI
from holdit.config import Config
from holdit.records import records_diff, records_filter
from holdit.tind import records_from_tind
from holdit.google_sheet import records_from_google, update_google, open_google
from holdit.generate import printable_doc
from holdit.network import network_available
from holdit.files import readable, writable, open_file, rename_existing, file_in_use
from holdit.files import desktop_path, module_path, holdit_path, delete_existing
from holdit.exceptions import *
from holdit.debug import set_debug, log


# Main program.
# ......................................................................

@plac.annotations(
    pswd       = ('Caltech access user password',                    'option', 'p'),
    user       = ('Caltech access user name',                        'option', 'u'),
    output     = ('write the output to the file "O"',                'option', 'o'),
    template   = ('use file "F" as the TIND record print template',  'option', 't'),
    debug      = ('turn on debugging (console only)',                'flag',   'D'),
    no_color   = ('do not color-code terminal output (default: do)', 'flag',   'C'),
    no_gui     = ('do not start the GUI interface (default: do)',    'flag',   'G'),
    no_keyring = ('do not use a keyring (default: do)',              'flag',   'K'),
    no_sheet   = ('do not open the spreadsheet (default: open it)',  'flag',   'S'),
    reset      = ('reset keyring-stored user name and password',     'flag',   'R'),
    version    = ('print version info and exit',                     'flag',   'V'),
)

def main(user = 'U', pswd = 'P', output='O', template='F',
         no_color=False, no_gui=False, no_keyring=False, no_sheet=False,
         reset=False, debug=False, version=False):
    '''Generates a printable Word document containing recent hold requests and
also update the relevant Google spreadsheet used for tracking requests.

By default, Hold It! uses a GUI dialog to get the user's Caltech access login
name and password.  If the -G option is given (/G on Windows), it will not
use a GUI dialog, and will instead use the operating system's
keyring/keychain functionality to get a user name and password.  If the
information does not exist from a previous run of Hold It!, it will query the
user interactively for the user name and password, and (unless the -K or /K
argument is given) store them in the user's keyring/keychain so that it does
not have to ask again in the future.  It is also possible to supply the
information directly on the command line using the -u and -p options (or /u
and /p on Windows), but this is discouraged because it is insecure on
multiuser computer systems.

To reset the user name and password (e.g., if a mistake was made the last
time and the wrong credentials were stored in the keyring/keychain system),
use the -R (or /R on Windows) command-line argument to a command.  This
argument will make Hold It! query for the user name and password again even if
an entry already exists in the keyring or keychain.

By default, Hold It! looks for a .docx file named "template.docx" in the
directory where Hold It! is located, and uses that as the template for record
printing.  If given the -t option followed by a file name (/t on Windows), it
will look for the named file instead.  If it is not given an explicit
template file and it cannot find a file "template.docx", Hold It! will use a
built-in default template file.

By default, Hold It! will also open the Google spreadsheet used by the
Circulation staff to track hold requests.  This action is inhibited if given
the -S option (/S on Windows).  The Google spreadsheet is always updated in
any case.

Hold It! will write the output to a file named "holds_print_list.docx" in the
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

    # Configure debug logging if it's turned on.
    if debug:
        set_debug(True)

    # Switch between different ways of getting information from/to the user.
    if use_gui:
        controller = HoldItControlGUI()
        accesser   = AccessHandlerGUI(user, pswd)
        notifier   = MessageHandlerGUI()
        tracer     = ProgressIndicatorGUI()
    else:
        controller = HoldItControlCLI()
        accesser   = AccessHandlerCLI(user, pswd, use_keyring, reset)
        notifier   = MessageHandlerCLI(use_color)
        tracer     = ProgressIndicatorCLI(use_color)

    # Start the worker thread.
    if __debug__: log('Starting main body thread')
    controller.start(MainBody(template, output, view_sheet, debug,
                              controller, tracer, accesser, notifier))


class MainBody(Thread):
    '''Main body of Hold It! implemented as a Python thread.'''

    def __init__(self, template, output, view_sheet, debug,
                 controller, tracer, accesser, notifier):
        '''Initializes main thread object but does not start the thread.'''
        Thread.__init__(self, name = "MainBody")
        self._template   = template
        self._output     = output
        self._view_sheet = view_sheet
        self._debug      = debug
        self._controller = controller
        self._tracer     = tracer
        self._accesser   = accesser
        self._notifier   = notifier
        if controller.is_gui:
            # Only make this a daemon thread when using the GUI; for CLI, it
            # must not be a daemon thread or else Hold It! exits immediately.
            self.daemon = True


    def run(self):
        # Set shortcut variables for better code readability below.
        template   = self._template
        output     = self._output
        view_sheet = self._view_sheet
        debug      = self._debug
        controller = self._controller
        accesser   = self._accesser
        notifier   = self._notifier
        tracer     = self._tracer

        # Preliminary sanity checks.  Do this here because we need the notifier
        # object to be initialized based on whether we're using GUI or CLI.
        tracer.start('Performing initial checks')
        if not network_available():
            notifier.fatal('No network connection.')

        # Let's do this thing.
        try:
            config = Config(path.join(module_path(), "holdit.ini"))

            # The default template is expected to be inside the Hold It module.
            # If the user supplies a template, we use it instead.
            tracer.update('Getting output template')
            template_file = config.get('holdit', 'template')
            template_file = path.abspath(path.join(module_path(), template_file))
            if template:
                temp = path.abspath(template)
                if readable(temp):
                    if __debug__: log('Using user-supplied template "{}"'.format(temp))
                    template_file = temp
                else:
                    notifier.warn('File "{}" not readable -- using default.'.format(template))
            else:
                # Check for "template.docx" in the Hold It installation dir.
                temp = path.abspath(path.join(holdit_path(), "template.docx"))
                if readable(temp):
                    if __debug__: log('Using template found at "{}"'.format(temp))
                    template_file = temp

            # Sanity check against possible screwups in creating the Hold It! app.
            # Do them here so that we can fail early if we know we can't finish.
            if not readable(template_file):
                notifier.fatal('Template doc file "{}" not readable.'.format(template_file))
                sys.exit()
            if not writable(desktop_path()):
                notifier.fatal('Output folder "{}" not writable.'.format(desktop_path()))
                sys.exit()

            # Get the data.
            spreadsheet_id = config.get('holdit', 'spreadsheet_id')
            tracer.update('Connecting to TIND')
            tind_records = records_from_tind(accesser, notifier, tracer)
            tracer.update('Connecting to Google')
            google_records = records_from_google(spreadsheet_id, accesser.user, notifier)
            missing_records = records_diff(google_records, tind_records)
            new_records = list(filter(records_filter('all'), missing_records))
            if __debug__: log('diff + filter => {} records'.format(len(new_records)))

            if len(new_records) > 0:
                # Update the spreadsheet with new records.
                tracer.update('Updating Google spreadsheet')
                update_google(spreadsheet_id, new_records, accesser.user, notifier)
                # Write a printable report.
                tracer.update('Generating printable document')
                if not output:
                    output = path.join(desktop_path(), "holds_print_list.docx")
                if path.exists(output):
                    rename_existing(output)
                if file_in_use(output):
                    details = '{} appears to be open in another program'.format(output)
                    notifier.warn('Cannot write Word doc -- is it still open?', details)
                else:
                    result = printable_doc(new_records, template_file)
                    result.save(output)
                    tracer.update('Opening Word document for printing')
                    open_file(output)
            else:
                tracer.update('No new hold requests were found in TIND.')
            # Open the spreadsheet too, if requested.
            if isinstance(notifier, MessageHandlerGUI):
                if notifier.yes_no('Open the tracking spreadsheet?'):
                    open_google(spreadsheet_id)
            elif view_sheet:
                open_google(spreadsheet_id)
        except (KeyboardInterrupt, UserCancelled) as err:
            tracer.stop('Quitting.')
            controller.stop()
        except ServiceFailure:
            tracer.stop('Stopping due to a problem connecting to services')
            controller.stop()
        except Exception as err:
            if debug:
                import pdb; pdb.set_trace()
            tracer.stop('Stopping due to error')
            notifier.fatal(holdit.__title__ + ' encountered an error',
                           str(err) + '\n' + traceback.format_exc())
            controller.stop()
        else:
            tracer.stop('Done')
            controller.stop()


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
