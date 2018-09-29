'''
control.py: human interface controller for Holdit!
'''

import os
import os.path as path
from queue import Queue
import wx
from   wx.lib.pubsub import pub
import wx.adv
import wx.richtext
import sys
import textwrap
from   threading import Thread
import webbrowser

import holdit
from holdit.files import datadir_path, readable
from holdit.exceptions import *
from holdit.debug import log


# Exported classes.
# .............................................................................

class HolditControlBase():
    '''User interface controller base class.'''

    @property
    def is_gui():
        '''Returns True if the GUI version of the interface is being used.'''
        return None


class HolditControlCLI(HolditControlBase):
    '''User interface controller for Holdit! in command-line interface mode.'''

    def __init__(self):
        super().__init__()


    @property
    def is_gui(self):
        '''Returns True if the GUI version of the interface is being used.'''
        return False


    def start(self, worker):
        self._worker = worker
        if worker:
            worker.start()


    def stop(self):
        sys.exit()


class HolditControlGUI(HolditControlBase):
    '''User interface controller for Holdit! in GUI mode.'''

    def __init__(self):
        super().__init__()
        self._app = wx.App()
        self._frame = HolditMainFrame(None, wx.ID_ANY, "")
        self._app.SetTopWindow(self._frame)
        self._frame.Center()
        self._frame.Show(True)


    @property
    def is_gui(self):
        '''Returns True if the GUI version of the interface is being used.'''
        return True


    def start(self, worker):
        self._worker = worker
        self._worker.start()
        self._app.MainLoop()


    def stop(self):
        wx.CallAfter(self._frame.Destroy)


# Internal implementation classes.
# .............................................................................

class HolditMainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        self._cancel = False
        self._height = 275 if sys.platform.startswith('win') else 250
        self._width  = 450

        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.panel = wx.Panel(self)
        headline = holdit.__name__ + " — generate a list of hold requests"
        self.headline = wx.StaticText(self.panel, wx.ID_ANY, headline, style = wx.ALIGN_CENTER)
        self.headline.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC,
                                      wx.FONTWEIGHT_BOLD, 0, "Arial"))

        # For macos, I figured out how to make the background color of the text
        # box be the same as the rest of the UI elements.  That looks nicer for
        # our purposes (IMHO) than the default (which would be white), but then
        # we need a divider to separate the headline from the text area.
        if not sys.platform.startswith('win'):
            self.divider = wx.StaticLine(self.panel, wx.ID_ANY)
            self.divider.SetMinSize((self._width, 2))

        self.text_area = wx.richtext.RichTextCtrl(self.panel, wx.ID_ANY,
                                                  size = (self._width, 200),
                                                  style = wx.TE_MULTILINE | wx.TE_READONLY)
        # On macos, the color of the text background is set to the same as the
        # rest of the UI panel.  I haven't figured out how to do it on Windows.
        if not sys.platform.startswith('win'):
            gray = wx.SystemSettings.GetColour(wx.SYS_COLOUR_BACKGROUND)
            self.text_area.SetBackgroundColour(gray)

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
        self.Bind(wx.EVT_MENU, self.on_cancel_or_quit, id = self.exitItem.GetId())
        self.Bind(wx.EVT_MENU, self.on_help, id = self.helpItem.GetId())
        self.Bind(wx.EVT_MENU, self.on_about, id = self.aboutItem.GetId())
        self.Bind(wx.EVT_CLOSE, self.on_cancel_or_quit)

        close_id = wx.NewId()
        self.Bind(wx.EVT_MENU, self.on_cancel_or_quit, id = close_id)
        accel_tbl = wx.AcceleratorTable([(wx.ACCEL_CTRL, ord('W'), close_id )])
        self.SetAcceleratorTable(accel_tbl)

        # Now that we created all the elements, set layout and placement.
        self.SetSize((self._width, self._height))
        self.SetTitle(holdit.__name__)
        self.outermost_sizer = wx.BoxSizer(wx.VERTICAL)
        self.outermost_sizer.Add((360, 5), 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add(self.headline, 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add((360, 5), 0, wx.ALIGN_CENTER, 0)
        if not sys.platform.startswith('win'):
            self.outermost_sizer.Add(self.divider, 0, wx.EXPAND | wx.ALIGN_CENTER_VERTICAL, 0)
            self.outermost_sizer.Add((360, 5), 0, wx.ALIGN_CENTER, 0)
        self.outermost_sizer.Add(self.text_area, 0, wx.EXPAND, 0)
        self.outermost_sizer.Add((360, 5), 0, wx.ALIGN_CENTER, 0)
        self.SetSizer(self.outermost_sizer)
        self.Layout()
        self.Centre()

        # Finally, hook in message-passing interface.
        pub.subscribe(self.progress_message, "progress_message")
        pub.subscribe(self.login_dialog, "login_dialog")


    def on_cancel_or_quit(self, event):
        if __debug__: log('HolditControlGUI got Exit/Cancel')
        self._cancel = True
        self.Destroy()
        return True


    def on_escape(self, event):
        if __debug__: log('HolditControlGUI got Escape')
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_ESCAPE:
            self.on_cancel_or_quit(event)
        else:
            event.Skip()
        return True


    def on_about(self, event):
        if __debug__: log('HolditControlGUI opening About window')
        dlg = wx.adv.AboutDialogInfo()
        dlg.SetName(holdit.__name__)
        dlg.SetVersion(holdit.__version__)
        dlg.SetLicense(holdit.__license__)
        dlg.SetDescription('\n'.join(textwrap.wrap(holdit.__description__, 81)))
        dlg.SetWebSite(holdit.__url__)
        dlg.AddDeveloper(holdit.__author__)
        wx.adv.AboutBox(dlg)
        return True


    def on_help(self, event):
        if __debug__: log('HolditControlGUI opening Help window')
        wx.BeginBusyCursor()
        help_file = path.join(datadir_path(), "help.html")
        if readable(help_file):
            webbrowser.open_new("file://" + help_file)
        wx.EndBusyCursor()
        return True


    def progress_message(self, message):
        self.text_area.AppendText(message + ' ...\n')


    def login_dialog(self, results, user, password):
        dialog = LoginDialog(self)
        dialog.initialize_values(results, user, password)
        dialog.ShowWindowModal()


class LoginDialog(wx.Dialog):
    def __init__(self, *args, **kwargs):
        super(LoginDialog, self).__init__(*args, **kwargs)
        self._user = None
        self._password = None
        self._cancel = False
        self._wait_queue = None

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


    def initialize_values(self, wait_queue, user, password):
        self._wait_queue = wait_queue
        self._user = user
        self._password = password
        if self._user:
            self.login.AppendText(self._user)
            self.login.Refresh()
        if self._password:
            self.password.AppendText(self._password)
            self.password.Refresh()


    def return_values(self):
        if __debug__: log('return_values called')
        self._wait_queue.put((self._user, self._password, self._cancel))


    def inputs_nonempty(self):
        user = self.login.GetValue()
        password = self.password.GetValue()
        if user.strip() and password.strip():
            return True
        return False


    def on_ok(self, event):
        '''Stores the current values and destroys the dialog.'''

        if __debug__: log('LoginDialog got OK')
        if self.inputs_nonempty():
            self._cancel = False
            self._user = self.login.GetValue()
            self._password = self.password.GetValue()
            self.return_values()
            # self.Destroy()
            self.return_values()
            self.EndModal(event.EventObject.Id)
        else:
            self.complain_incomplete_values(event)


    def on_cancel_or_quit(self, event):
        if __debug__: log('LoginDialog got Cancel')
        self._cancel = True
        self.return_values()
        # self.Destroy()
        self.return_values()
        self.EndModal(event.EventObject.Id)


    def on_text(self, event):
        if self.login.GetValue() and self.password.GetValue():
            self.ok_button.Enable()
        else:
            self.ok_button.Disable()


    def on_escape(self, event):
        if __debug__: log('LoginDialog got Escape')
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


    def complain_incomplete_values(self, event):
        dialog = wx.MessageDialog(self, caption = "Missing login and/or password",
                                  message = "Incomplete values – do you want to quit?",
                                  style = wx.YES_NO | wx.ICON_WARNING,
                                  pos = wx.DefaultPosition)
        response = dialog.ShowModal()
        dialog.EndModal(wx.OK)
        dialog.Destroy()
        if (response == wx.ID_YES):
            self._cancel = True
            self.return_values()
