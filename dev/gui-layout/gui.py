#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# generated by wxGlade 0.9.0pre on Wed Jul 25 12:42:08 2018
#

import wx

# begin wxGlade: dependencies
# end wxGlade

# begin wxGlade: extracode
# end wxGlade


class MainFrame(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: MainFrame.__init__
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        self.SetSize((355, 175))
        self.title = wx.StaticText(self, wx.ID_ANY, "Holdit: generate a list of hold requests", style=wx.ALIGN_CENTER)
        self.top_line = wx.StaticLine(self, wx.ID_ANY)
        self.login_label = wx.StaticText(self, wx.ID_ANY, "Caltech TIND login:", style=wx.ALIGN_RIGHT)
        self.login = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_DONTWRAP)
        self.password_label = wx.StaticText(self, wx.ID_ANY, "Caltech TIND password:", style=wx.ALIGN_RIGHT)
        self.password = wx.TextCtrl(self, wx.ID_ANY, "", style=wx.TE_DONTWRAP | wx.TE_PASSWORD)
        self.bottom_line = wx.StaticLine(self, wx.ID_ANY)
        self.cancel_button = wx.Button(self, wx.ID_ANY, "Cancel")
        self.ok_button = wx.Button(self, wx.ID_ANY, "OK")

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_BUTTON, self.on_cancel, self.cancel_button)
        self.Bind(wx.EVT_BUTTON, self.on_ok, self.ok_button)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: MainFrame.__set_properties
        self.SetTitle("Holdit")
        self.title.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_ITALIC, wx.FONTWEIGHT_BOLD, 0, "Arial"))
        self.top_line.SetMinSize((360, 2))
        self.login_label.SetToolTip("The account name to use to log in to caltech.tind.io. This should be a Caltech access login name.")
        self.login.SetMinSize((195, 22))
        self.password_label.SetToolTip("The account password to use to log in to caltech.tind.io. This should be a Caltech access password.")
        self.password.SetMinSize((195, 22))
        self.ok_button.SetFocus()
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: MainFrame.__do_layout
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
        # end wxGlade

    def on_cancel(self, event):  # wxGlade: MainFrame.<event_handler>
        print("Event handler 'on_cancel' not implemented!")
        event.Skip()

    def on_ok(self, event):  # wxGlade: MainFrame.<event_handler>
        print("Event handler 'on_ok' not implemented!")
        event.Skip()

# end of class MainFrame

class HolditApp(wx.App):
    def OnInit(self):
        self.setsizeframe = MainFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.setsizeframe)
        self.setsizeframe.Show()
        return True

# end of class HolditApp

if __name__ == "__main__":
    Holdit = HolditApp(0)
    Holdit.MainLoop()