'''
files.py: utilities for working with files.
'''

import os
from   os import path
import sys
import subprocess
import webbrowser

import holdit


# Main functions.
# .............................................................................

def readable(dest):
    '''Returns True if the given 'dest' is accessible and readable.'''
    return os.access(dest, os.F_OK | os.R_OK)


def writable(dest):
    '''Returns True if the destination is writable.'''
    return os.access(dest, os.F_OK | os.W_OK)


def module_path():
    '''Returns the absolute path to our module installation directory.'''
    # The path returned by module.__path__ is to the directory containing
    # the __init__.py file.
    return path.abspath(holdit.__path__[0])


def holdit_path():
    '''Returns the path to where Holdit is installed.'''
    # The path returned by module.__path__ is to the directory containing
    # the __init__.py file.  What we want here is the path to the installation
    # of the Holdit binary.  I don't know how to get that in a os-independent
    # way, so I'm punting here.
    return path.abspath(path.join(module_path(), '..'))


def desktop_path():
    '''Returns the path to the user's desktop directory.'''
    if sys.platform.startswith('win'):
        return path.join(path.join(os.environ['USERPROFILE']), 'Desktop')
    else:
        return path.join(path.join(path.expanduser('~')), 'Desktop')


def datadir_path():
    '''Returns the path to Holdit's internal data directory.'''
    return path.join(module_path(), 'data')


def rename_existing(file, notifier):
    '''Renames 'file' to 'file.bak'.  Uses a notifier class to provide info
    about what it does.'''

    def rename(f):
        backup = f + '.bak'
        # If we fail, we just give up instead of throwing an exception.
        try:
            os.rename(f, backup)
        except:
            return
        notifier.msg('Renamed existing file "{}" to "{}"'.format(f, backup),
                     'To avoid overwriting the existing file "{}", '.format(f)
                     + 'it has been renamed to "{}"'.format(backup),
                     'info')

    if path.exists(file):
        rename(file)
        return
    full_path = path.join(os.getcwd(), file)
    if path.exists(full_path):
        rename(full_path)
        return


def open_file(file):
    '''Open document with default application in Python.'''
    # Code originally from https://stackoverflow.com/a/435669/743730
    if sys.platform.startswith('darwin'):
        subprocess.call(('open', file))
    elif os.name == 'nt':
        os.startfile(file)
    elif os.name == 'posix':
        subprocess.call(('xdg-open', file))


def open_url(url):
    '''Open the given 'url' in a web browser using the current platform's
    default approach.'''
    webbrowser.open(url)
