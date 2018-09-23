'''
access.py: code to deal with getting user access credentials
'''

import os
import os.path as path
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


# Exported interfaces to different approaches to getting credentials.
# .............................................................................

class AccessHandlerBase():
    def __init__(self, the_user = None, the_pswd = None):
        '''Initialize internal data with user and password if available.'''
        self._user = the_user
        self._pswd = the_pswd

    @property
    def user(self):
        return self._user

    @property
    def pswd(self):
        return self._pswd


class AccessHandlerGUI(AccessHandlerBase):
    '''Use a GUI to ask the user for credentials.'''

    def name_and_password(self):
        '''Returns a tuple of user, password.'''
        tmp_user = self._user
        tmp_pswd = self._pswd

        if __debug__: log('Invoking GUI')
        tmp_user, tmp_pswd, cancel = self._credentials_from_gui(tmp_user, tmp_pswd)
        if cancel:
            if __debug__: log('User initiated quit from within GUI')
            raise UserCancelled

        self._user = tmp_user
        self._pswd = tmp_pswd
        return self._user, self._pswd


    def _credentials_from_gui(self, user, pswd):
        gui = HolditGUI(0)
        gui.initialize_values(user, pswd)
        gui.MainLoop()
        return gui.final_values()


class AccessHandlerCLI(AccessHandlerBase):
    def __init__(self, the_user = None, the_pswd = None, use_keyring = True, reset = False):
        '''Initialize internal data with user and password if available.'''
        super().__init__(the_user, the_pswd)
        self._use_keyring = use_keyring
        self._reset = reset


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


# Internal implementation classes for login GUI.
# .............................................................................

class UserInputValues():
    '''Utility class to store and communicate values from GUI interactions.'''
    user = None
    password = None
    cancel = False


class HolditGUI(wx.App):
    '''Top level class for creating and interacting with the login GUI.'''

    def __init__(self, parent):
        super().__init__(parent)
        self.values = UserInputValues()


    def OnInit(self):
        self.setsizeframe = MainFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.setsizeframe)
        self.setsizeframe.Show()
        return True


    def initialize_values(self, user, password):
        self.values.user = user
        self.values.password = password
        self.setsizeframe.initialize_values(self.values)


    def final_values(self):
        return self.values.user, self.values.password, self.values.cancel


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self.values = None

        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self)
        if sys.platform.startswith('win'):
            self.SetSize((425, 200))
        else:
            self.SetSize((355, 175))
        self.title = wx.StaticText(panel, wx.ID_ANY,
                                   holdit.__name__ + " — generate a list of hold requests",
                                   style = wx.ALIGN_CENTER)
        self.top_line = wx.StaticLine(panel, wx.ID_ANY)
        self.login_label = wx.StaticText(panel, wx.ID_ANY, "Caltech TIND login: ", style = wx.ALIGN_RIGHT)
        self.login = wx.TextCtrl(panel, wx.ID_ANY, '', style = wx.TE_PROCESS_ENTER)
        self.login.Bind(wx.EVT_KEY_DOWN, self.on_enter_or_tab)
        self.login.Bind(wx.EVT_TEXT, self.on_text)
        self.password_label = wx.StaticText(panel, wx.ID_ANY, "Caltech TIND password: ", style = wx.ALIGN_RIGHT)
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

        # Create a simple menu bar.
        self.menuBar = wx.MenuBar(0)

        # Add a "File" menu with a quit item.
        self.fileMenu = wx.Menu()
        self.exitItem = wx.MenuItem(self.fileMenu, wx.ID_EXIT, "&Exit",
                                    wx.EmptyString, wx.ITEM_NORMAL)
        self.fileMenu.Append(self.exitItem)
        if sys.platform.startswith('win'):
            # Only need to add a File menu on Windows.  On Macs, wxPython
            # automatically puts the wx.ID_EXIT item under the app menu.
            self.menuBar.Append(self.fileMenu, "&File")

        # Add a "help" menu bar item.
        self.helpMenu = wx.Menu()
        self.helpItem = wx.MenuItem(self.helpMenu, wx.ID_HELP, "&Help",
                                    wx.EmptyString, wx.ITEM_NORMAL)
        self.helpMenu.Append(self.helpItem)
        self.helpMenu.AppendSeparator()
        self.aboutItem = wx.MenuItem(self.helpMenu, wx.ID_ABOUT,
                                     "&About " + holdit.__name__,
                                     wx.EmptyString, wx.ITEM_NORMAL)
        self.helpMenu.Append(self.aboutItem)
        self.menuBar.Append(self.helpMenu, "Help")

        # Put everything together and bind some keystrokes to events.
        self.SetMenuBar(self.menuBar)
        self.__set_properties()
        self.__do_layout()
        self.Bind(wx.EVT_BUTTON, self.on_cancel_or_quit, self.cancel_button)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        self.Bind(wx.EVT_MENU, self.on_cancel_or_quit, id = self.exitItem.GetId())
        self.Bind(wx.EVT_MENU, self.on_help, id = self.helpItem.GetId())
        self.Bind(wx.EVT_MENU, self.on_about, id = self.aboutItem.GetId())
        self.Bind(wx.EVT_CLOSE, self.on_cancel_or_quit)

        close_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.on_cancel_or_quit, id = close_id)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('W'), close_id )])
        self.SetAcceleratorTable(accel_tbl)


    def __set_properties(self):
        self.SetTitle(holdit.__name__)
        self.title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, "Arial"))
        self.top_line.SetMinSize((360, 2))
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
        self.outermost_sizer.Add(self.title, 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add((360, 8), 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add(self.top_line, 0, wx.EXPAND, 0)
        self.outermost_sizer.Add((360, 8), 0, wx.ALIGN_CENTER, 0)
        self.login_sizer.Add(self.login_label, 0, wx.ALIGN_RIGHT, 0)
        self.login_sizer.Add(self.login, 0, wx.EXPAND, 0)
        self.login_sizer.Add(self.password_label, 0, wx.ALIGN_RIGHT, 0)
        self.login_sizer.Add(self.password, 0, wx.EXPAND, 0)
        self.outermost_sizer.Add(self.login_sizer, 1, wx.ALIGN_CENTER | wx.FIXED_MINSIZE, 5)
        self.outermost_sizer.Add((360, 5), 0, 0, 0)
        self.outermost_sizer.Add(self.bottom_line, 0, wx.EXPAND, 0)
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


    def initialize_values(self, values):
        self.values = values
        if values.user:
            self.login.AppendText(values.user)
            self.login.Refresh()
        if values.password:
            self.password.AppendText(values.password)
            self.password.Refresh()


    def inputs_nonempty(self):
        user = self.login.GetValue()
        password = self.password.GetValue()
        if user.strip() and password.strip():
            return True
        return False


    def on_ok(self, event):
        '''Stores the current values and destroys the dialog.'''

        if self.inputs_nonempty():
            self.values.cancel = False
            self.values.user = self.login.GetValue()
            self.values.password = self.password.GetValue()
            self.Destroy()
        else:
            self.complain_incomplete_values()


    def on_cancel_or_quit(self, event):
        self.values.cancel = True
        self.Destroy()


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
            self.values.cancel = True
            self.Destroy()


    def on_about(self, event):
        dlg = wx.adv.AboutDialogInfo()
        dlg.SetName(holdit.__name__)
        dlg.SetVersion(holdit.__version__)
        dlg.SetLicense(holdit.__license__)
        dlg.SetDescription('\n'.join(textwrap.wrap(holdit.__description__, 81)))
        dlg.SetWebSite(holdit.__url__)
        dlg.AddDeveloper(u"Michael Hucka (California Institute of Technology)")
        wx.adv.AboutBox(dlg)


    def on_help(self, event):
        wx.BeginBusyCursor()
        help_file = path.join(datadir_path(), "help.html")
        if readable(help_file):
            webbrowser.open_new("file://" + help_file)
        wx.EndBusyCursor()
