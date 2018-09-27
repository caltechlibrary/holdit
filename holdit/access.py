'''
access.py: code to deal with getting user access credentials

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
import queue
import wx
import wx.adv
import textwrap
import webbrowser
import sys

import holdit
from holdit.credentials import password, credentials
from holdit.credentials import keyring_credentials, save_keyring_credentials
from holdit.exceptions import *
from holdit.files import datadir_path, readable

# Note: to turn on debugging, make sure python -O was *not* used to start
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


# Exported classes.
# .............................................................................
# The basic principle of writing the classes (like this one) that get used in
# MainBody is that they should take the information they need, rather than
# putting the info into the controller object (i.e., HolditControlGUI or
# HolditControlCLI).  This is a matter of separation of concerns and
# information hiding.

class AccessHandlerBase():
    ''''Base class for dealing with user access credentials.'''

    def __init__(self, controller, user, pswd):
        '''Initialize internal data with user and password (if given).'''
        self._controller = controller
        self._user = user
        self._pswd = pswd

    @property
    def user(self):
        return self._user

    @property
    def pswd(self):
        return self._pswd


class AccessHandlerCLI(AccessHandlerBase):
    '''Class to use the command line to ask the user for credentials.'''

    def __init__(self, controller, user, pswd, use_keyring, reset_keyring):
        '''Initializes internal data with user and password if available.'''
        super().__init__(controller, user, pswd)
        self._use_keyring = use_keyring
        self._reset = reset_keyring


    def name_and_password(self):
        '''Returns a tuple of user, password.'''
        tmp_user = self._user
        tmp_pswd = self._pswd
        if not all([tmp_user, tmp_pswd]) or self._reset or not self._use_keyring:
            if self._use_keyring and not self._reset:
                if __debug__: log('Getting credentials from keyring')
                tmp_user, tmp_pswd, _, _ = credentials(_KEYRING, "Caltech access login",
                                                       tmp_user, tmp_pswd)
            else:
                if not self._use_keyring:
                    if __debug__: log('Keyring disabled')
                if self._reset:
                    if __debug__: log('Reset invoked')
                tmp_user = input('Caltech access login: ')
                tmp_pswd = password('Password for "{}": '.format(tmp_user))
            if self._use_keyring:
                # Save the credentials if they're different.
                s_user, s_pswd, _, _ = keyring_credentials(_KEYRING)
                if s_user != tmp_user or s_pswd != tmp_pswd:
                    if __debug__: log('Saving credentials to keyring')
                    save_keyring_credentials(_KEYRING, tmp_user, tmp_pswd)
        self._user = tmp_user
        self._pswd = tmp_pswd
        return self._user, self._pswd


class AccessHandlerGUI(AccessHandlerBase):
    '''Class to use a GUI to ask the user for credentials.'''

    def __init__(self, controller, user, pswd):
        '''Initializes internal data with user and password if available.'''
        super().__init__(controller, user, pswd)
        self._parent_frame = controller.frame
        self._queue = queue.Queue()
        self._cancelled = False


    def name_and_password(self):
        '''Returns a tuple of user, password.'''
        self._dialog = LoginDialog(self._parent_frame)
        self._dialog.initialize_values(self._user, self._pswd)
        wx.CallAfter(self._credentials_from_gui, self._queue)
        self._wait()
        self._user, self._pswd, self._cancelled = self._dialog.final_values()
        if self._cancelled:
            raise UserCancelled
        return self._user, self._pswd


    def _credentials_from_gui(self, queue):
        self._dialog.set_queue(queue)
        self._dialog.ShowWindowModal()


    def _wait(self):
        self._queue.get()


# Internal implementation classes for login dialog GUI.
# .............................................................................

class LoginDialog(wx.Dialog):
    def __init__(self, parent_frame):
        super(LoginDialog, self).__init__(parent_frame)
        self._user = None
        self._password = None
        self._cancel = False

        panel = wx.Panel(self)
        if sys.platform.startswith('win'):
            self.SetSize((330, 175))
        else:
            self.SetSize((330, 155))
        self.explanation = wx.StaticText(panel, wx.ID_ANY,
                                         'Holdit! needs your Caltech Access credentials',
                                         style = wx.ALIGN_CENTER)
        self.top_line = wx.StaticLine(panel, wx.ID_ANY)
        self.login_label = wx.StaticText(panel, wx.ID_ANY, "Caltech login: ", style = wx.ALIGN_RIGHT)
        self.login = wx.TextCtrl(panel, wx.ID_ANY, '', style = wx.TE_PROCESS_ENTER)
        self.login.Bind(wx.EVT_KEY_DOWN, self.on_enter_or_tab)
        self.login.Bind(wx.EVT_TEXT, self.on_text)
        self.password_label = wx.StaticText(panel, wx.ID_ANY, "Caltech password: ", style = wx.ALIGN_RIGHT)
        self.password = wx.TextCtrl(panel, wx.ID_ANY, '', style = wx.TE_PASSWORD)
        self.password.Bind(wx.EVT_KEY_DOWN, self.on_enter_or_tab)
        self.password.Bind(wx.EVT_TEXT, self.on_text)
        self.bottom_line = wx.StaticLine(panel, wx.ID_ANY)
        self.cancel_button = wx.Button(panel, wx.ID_ANY, "Cancel")
        self.cancel_button.Bind(wx.EVT_KEY_DOWN, self.on_escape)
        self.ok_button = wx.Button(panel, wx.ID_ANY, "OK")
        self.ok_button.Bind(wx.EVT_KEY_DOWN, self.on_ok_enter_key)
        self.ok_button.SetDefault()
        self.ok_button.Disable()

        # Put everything together and bind some keystrokes to events.
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.on_cancel_or_quit, self.cancel_button)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        self.Bind(wx.EVT_CLOSE, self.on_cancel_or_quit)

        close_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.on_cancel_or_quit, id = close_id)
        accel_tbl = wx.AcceleratorTable([
            (wx.ACCEL_CTRL, ord('W'), close_id ),
            (wx.ACCEL_CMD, ord('.'), close_id ),
        ])
        self.SetAcceleratorTable(accel_tbl)


    def __set_properties(self):
        self.SetTitle(holdit.__name__)
        self.login_label.SetToolTip("The account name to use to log in to caltech.tind.io. This should be a Caltech access login name.")
        self.login.SetMinSize((195, 22))
        self.password_label.SetToolTip("The account password to use to log in to caltech.tind.io. This should be a Caltech access password.")
        self.password.SetMinSize((195, 22))
        self.ok_button.SetFocus()


    def __do_layout(self):
        self.outermost_sizer = wx.BoxSizer(wx.VERTICAL)
        self.button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.login_sizer = wx.FlexGridSizer(2, 2, 5, 0)
        self.outermost_sizer.Add((360, 5), 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add(self.explanation, 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add((360, 5), 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add(self.top_line, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0)
        self.outermost_sizer.Add((360, 8), 0, wx.ALIGN_CENTER, 0)
        self.login_sizer.Add(self.login_label, 0, wx.ALIGN_RIGHT, 0)
        self.login_sizer.Add(self.login, 0, wx.EXPAND, 0)
        self.login_sizer.Add(self.password_label, 0, wx.ALIGN_RIGHT, 0)
        self.login_sizer.Add(self.password, 0, wx.EXPAND, 0)
        self.outermost_sizer.Add(self.login_sizer, 1, wx.ALIGN_CENTER | wx.FIXED_MINSIZE, 5)
        self.outermost_sizer.Add((360, 5), 0, 0, 0)
        self.outermost_sizer.Add(self.bottom_line, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0)
        self.outermost_sizer.Add((360, 5), 0, 0, 0)
        self.button_sizer.Add((0, 0), 0, 0, 0)
        self.button_sizer.Add(self.cancel_button, 0, wx.ALIGN_CENTER, 0)
        self.button_sizer.Add((10, 20), 0, 0, 0)
        self.button_sizer.Add(self.ok_button, 0, wx.ALIGN_CENTER, 0)
        self.button_sizer.Add((10, 20), 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add(self.button_sizer, 1, wx.ALIGN_RIGHT, 0)
        self.outermost_sizer.Add((360, 5), 0, wx.ALIGN_CENTER, 0)
        self.SetSizer(self.outermost_sizer)
        self.Layout()
        self.Centre()


    def initialize_values(self, user, password):
        self._user = user
        self._password = password
        if self._user:
            self.login.AppendText(self._user)
            self.login.Refresh()
        if self._password:
            self.password.AppendText(self._password)
            self.password.Refresh()


    def final_values(self):
        return self._user, self._password, self._cancel


    def inputs_nonempty(self):
        user = self.login.GetValue()
        password = self.password.GetValue()
        if user.strip() and password.strip():
            return True
        return False


    def on_ok(self, event):
        '''Stores the current values and destroys the dialog.'''

        if self.inputs_nonempty():
            self._cancel = False
            self._user = self.login.GetValue()
            self._password = self.password.GetValue()
            self.Destroy()
            self.queue.put(True)
        else:
            self.complain_incomplete_values()


    def on_cancel_or_quit(self, event):
        self._cancel = True
        self.Destroy()
        self.queue.put(True)


    def on_text(self, event):
        if self.login.GetValue() and self.password.GetValue():
            self.ok_button.Enable()
        else:
            self.ok_button.Disable()


    def on_escape(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.on_cancel_or_quit(event)
        else:
            event.Skip()


    def on_ok_enter_key(self, event):
        keycode = event.GetKeyCode()
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE]:
            self.on_ok(event)
        elif keycode == wx.WXK_ESCAPE:
            self.on_cancel_or_quit(event)
        else:
            event.EventObject.Navigate()


    def on_enter_or_tab(self, event):
        keycode = event.GetKeyCode()
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            # If the ok button is enabled, we interpret return/enter as "done".
            if self.ok_button.IsEnabled():
                self.on_ok(event)
            # If focus is on the login line, move to password.
            if wx.Window.FindFocus() is self.login:
                event.EventObject.Navigate()
        elif keycode == wx.WXK_TAB:
            event.EventObject.Navigate()
        elif keycode == wx.WXK_ESCAPE:
            self.on_cancel_or_quit(event)
        else:
            event.Skip()


    def complain_incomplete_values(self):
        dialog = wx.MessageDialog(self, caption = "Missing login and/or password",
                                  message = "Incomplete values – do you want to quit?",
                                  style = wx.YES_NO | wx.ICON_WARNING,
                                  pos = wx.DefaultPosition)
        response = dialog.ShowModal()
        if (response == wx.ID_YES):
            self._cancel = True
            self.Destroy()


    def set_queue(self, queue):
        self.queue = queue
