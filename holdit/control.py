'''
control.py: human interface controller for Holdit!
'''

import os
import os.path as path
import queue
import wx
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
        self._app = wx.App(0)
        self._frame = HolditMainFrame(None, wx.ID_ANY, "")
        self._app.SetTopWindow(self._frame)
        self._frame.Center()
        self._frame.Show(True)


    @property
    def is_gui(self):
        '''Returns True if the GUI version of the interface is being used.'''
        return True


    @property
    def frame(self):
        '''Returns the main application wxPython frame.'''
        return self._frame


    def start(self, worker):
        self._worker = worker
        # The thread needs to be started after starting the wxPython main loop.
        wx.CallAfter(self._worker.start)
        self._app.MainLoop()


    def stop(self):
        wx.CallAfter(self._frame.Destroy)


    def write_message(self, message):
        self._frame.write_message(message)


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

        # Finally, deal with layout.
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


    def write_message(self, message):
        self.text_area.AppendText(message + ' ...\n')
