'''
progress.py: show indication of progresss

Authors
-------

Michael Hucka <mhucka@caltech.edu> -- Caltech Library

Copyright
---------

Copyright (c) 2018 by the California Institute of Technology.  This code is
open-source software released under a 3-clause BSD license.  Please see the
file "LICENSE" for more information.
'''

from   halo import Halo
import sys
import time
import wx
import wx.lib.dialogs

try:
    from termcolor import colored
    if sys.platform.startswith('win'):
        import colorama
        colorama.init()
except:
    pass

import holdit
from holdit.exceptions import *
from holdit.messages import color, msg


# Exported classes.
# .............................................................................
# The basic principle of writing the classes (like this one) that get used in
# MainBody is that they should take the information they need, rather than
# putting the info into the controller object (i.e., HolditControlGUI or
# HolditControlCLI).  This means, for example, that 'use_color' is handed to
# the CLI version of this object, not to the base class or the HolditControl*
# classes, even though use_color is something that may be relevant to more
# than one of the main classes.  This is a matter of separation of concerns
# and information hiding.

class ProgressIndicatorBase():

    def __init__(self, controller):
        '''Initialize internal data with the controller instance.'''
        self._controller = controller


class ProgressIndicatorCLI(ProgressIndicatorBase):

    def __init__(self, controller, use_color):
        super().__init__(controller)
        self._colorize = use_color
        self._spinner = None
        self._current_message = ''


    def start(self, message = None):
        if message is None:
            message = ''
        if self._colorize:
            text = color(message, 'info')
            self._spinner = Halo(spinner='bouncingBall', text = text)
            self._spinner.start()
            self._current_message = message
        else:
            msg(message)


    def update(self, message = None):
        if self._colorize:
            self._spinner.succeed(color(self._current_message, 'info', self._colorize))
            self._spinner.stop()
            self.start(message)
        else:
            msg(message)


    def stop(self, message = None):
        if self._colorize:
            self._spinner.succeed(color(self._current_message, 'info', self._colorize))
            self._spinner.stop()
            self.start(message)
            self._spinner.succeed(color(message, 'info', self._colorize))
            self._spinner.stop()
        else:
            msg(message)


class ProgressIndicatorGUI(ProgressIndicatorBase):

    def start(self, message = None):
        wx.CallAfter(self._controller.write_message, message)


    def update(self, message = None, count = None):
        wx.CallAfter(self._controller.write_message, message)


    def stop(self, message = None):
        wx.CallAfter(self._controller.write_message, message)
