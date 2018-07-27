'''
access.py: code to deal with getting user access credentials
'''

import wx

from holdit.credentials import password, credentials
from holdit.credentials import keyring_credentials, save_keyring_credentials
from holdit.exceptions import *

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

class AccessHandlerGUI():
    '''Use a GUI to ask the user for credentials.'''
    user = None
    pswd = None


    def __init__(self, user = None, pswd = None):
        '''Initialize internal data with user and password if available.'''
        self.user = user
        self.pswd = pswd


    def name_and_password(self):
        '''Returns a tuple of user, password.'''
        user = self.user
        pswd = self.pswd
        if not all([user, pswd]):
            if __debug__: log('Invoking GUI')
            user, pswd, cancel = self._credentials_from_gui(user, pswd)
            if cancel:
                if __debug__: log('User initiated quit from within GUI')
                raise UserCancel
        return user, pswd


    def _credentials_from_gui(self, user, pswd):
        gui = HolditGUI(0)
        gui.init_values(user, pswd)
        gui.MainLoop()
        return gui.final_values()


class AccessHandlerCLI():
    user = None
    pswd = None
    reset = False
    use_keyring = False


    def __init__(self, user = None, pswd = None, use_keyring = True, reset = False):
        '''Initialize internal data with user and password if available.'''
        self.user = user
        self.pswd = pswd
        self.use_gui = use_gui
        self.use_keyring = use_keyring
        self.reset = reset


    def name_and_password(self):
        '''Returns a tuple of user, password.'''
        user = self.user
        pswd = self.pswd
        if not all([user, pswd]) or self.reset or self.no_keyring:
            if self.use_keyring and not self.reset:
                if __debug__: log('Getting credentials from keyring')
                user, pswd, _, _ = credentials(_KEYRING, "Caltech access login",
                                               user, pswd)
            else:
                if not self.use_keyring:
                    if __debug__: log('Keyring disabled')
                if self.reset:
                    if __debug__: log('Reset invoked')
                user = input('Caltech access login: ')
                pswd = password('Password for "{}": '.format(user))
            if self.use_keyring:
                # Save the credentials if they're different.
                s_user, s_pswd, _, _ = keyring_credentials(_KEYRING)
                if s_user != user or s_pswd != pswd:
                    if __debug__: log('Saving credentials to keyring')
                    save_keyring_credentials(_KEYRING, user, pswd)
        return user, pswd


# Internal implementation classes for login GUI.
# .............................................................................

class UserInputValues():
    '''Utility class to store and communicate values from GUI interactions.'''
    user = None
    password = None
    cancel = False


class HolditGUI(wx.App):
    '''Top level class for creating and interacting with the login GUI.'''
    values = UserInputValues()


    def OnInit(self):
        self.setsizeframe = MainFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.setsizeframe)
        self.setsizeframe.Show()
        return True


    def init_values(self, user, password):
        self.values.user = user
        self.values.password = password
        self.setsizeframe.init_values(self.values)


    def final_values(self):
        return self.values.user, self.values.password, self.values.cancel


class MainFrame(wx.Frame):
    values = None

    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self)
        self.SetSize((355, 175))
        self.title = wx.StaticText(panel, wx.ID_ANY, "Holdit: generate a list of hold requests", style = wx.ALIGN_CENTER)
        self.top_line = wx.StaticLine(panel, wx.ID_ANY)
        self.login_label = wx.StaticText(panel, wx.ID_ANY, "Caltech TIND login:", style = wx.ALIGN_RIGHT)
        self.login = wx.TextCtrl(panel, wx.ID_ANY, '', style = wx.TE_PROCESS_ENTER)
        self.login.Bind(wx.EVT_KEY_DOWN, self.on_enter_or_tab)
        self.password_label = wx.StaticText(panel, wx.ID_ANY, "Caltech TIND password:", style = wx.ALIGN_RIGHT)
        self.password = wx.TextCtrl(panel, wx.ID_ANY, '', style = wx.TE_PROCESS_ENTER)
        self.password.Bind(wx.EVT_KEY_DOWN, self.on_enter_or_tab)
        self.bottom_line = wx.StaticLine(panel, wx.ID_ANY)
        self.cancel_button = wx.Button(panel, wx.ID_ANY, "Cancel")
        self.cancel_button.Bind(wx.EVT_KEY_DOWN, self.on_escape)
        self.ok_button = wx.Button(panel, wx.ID_ANY, "OK")
        self.ok_button.Bind(wx.EVT_KEY_DOWN, self.on_ok_enter_key)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel_button)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        self.Bind(wx.EVT_CLOSE, self.on_cancel)

        close_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.on_cancel, id = close_id)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('W'), close_id )])
        self.SetAcceleratorTable(accel_tbl)


    def __set_properties(self):
        self.SetTitle("Holdit")
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


    def init_values(self, values):
        self.values = values
        if self.values.user:
            self.login.AppendText(self.values.user)
            self.login.Refresh()
        if self.values.password:
            self.password.AppendText(self.values.password)
            self.password.Refresh()


    def on_ok(self, event):
        self.values.cancel = False
        self.values.user = self.login.GetValue()
        self.values.password = self.password.GetValue()
        if self.values_valid():
            self.Destroy()
        else:
            self.complain_incomplete_values()


    def on_cancel(self, event):
        dialog = wx.MessageDialog(self, caption = "Quit?",
                                  message = "Are you sure you want to quit?",
                                  style = wx.YES_NO | wx.ICON_WARNING,
                                  pos = wx.DefaultPosition)
        response = dialog.ShowModal()
        if (response == wx.ID_YES):
            self.values.cancel = True
            self.Destroy()
        else:
            event.StopPropagation()


    def on_escape(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.on_cancel(event)
        else:
            event.Skip()


    def on_ok_enter_key(self, event):
        keycode = event.GetKeyCode()
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER, wx.WXK_SPACE]:
            self.on_ok(event)
        elif keycode == wx.WXK_ESCAPE:
            self.on_cancel(event)
        else:
            event.EventObject.Navigate()


    def on_enter_or_tab(self, event):
        keycode = event.GetKeyCode()
        if keycode in [wx.WXK_RETURN, wx.WXK_NUMPAD_ENTER]:
            # If focus is on the login line, move to password.
            # If focus is not, then it's on password, so we move to the button.
            if wx.Window.FindFocus() is self.login:
                event.EventObject.Navigate()
            else:
                self.ok_button.SetFocus()
        elif keycode == wx.WXK_TAB:
            event.EventObject.Navigate()
        elif keycode == wx.WXK_ESCAPE:
            self.on_cancel(event)
        else:
            event.Skip()


    def values_valid(self):
        if not self.values.user.strip() or not self.values.password.strip():
            return False
        return True


    def complain_incomplete_values(self):
        dialog = wx.MessageDialog(self, caption = "Missing login and/or password",
                                  message = "Incomplete values – do you want to quit?",
                                  style = wx.YES_NO | wx.ICON_WARNING,
                                  pos = wx.DefaultPosition)
        response = dialog.ShowModal()
        if (response == wx.ID_YES):
            self.values.cancel = True
            self.Destroy()
