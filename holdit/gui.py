'''
gui.py: GUI for Holdit
'''

import wx

class Values():
    user = None
    password = None
    cancel = False


class MainFrame(wx.Frame):
    values = None

    def __init__(self, *args, **kwds):
        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE | wx.TAB_TRAVERSAL
        wx.Frame.__init__(self, *args, **kwds)
        panel = wx.Panel(self)
        self.SetSize((355, 175))
        self.title = wx.StaticText(panel, wx.ID_ANY, "Holdit: generate a list of hold requests", style=wx.ALIGN_CENTER)
        self.top_line = wx.StaticLine(panel, wx.ID_ANY)
        self.login_label = wx.StaticText(panel, wx.ID_ANY, "Caltech TIND login:", style=wx.ALIGN_RIGHT)
        self.login = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_DONTWRAP)
        self.password_label = wx.StaticText(panel, wx.ID_ANY, "Caltech TIND password:", style=wx.ALIGN_RIGHT)
        self.password = wx.TextCtrl(panel, wx.ID_ANY, "", style=wx.TE_DONTWRAP | wx.TE_PASSWORD)
        self.bottom_line = wx.StaticLine(panel, wx.ID_ANY)
        self.cancel_button = wx.Button(panel, wx.ID_ANY, "Cancel")
        self.ok_button = wx.Button(panel, wx.ID_ANY, "OK")

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


class HolditApp(wx.App):
    values = Values()

    def OnInit(self):
        self.setsizeframe = MainFrame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.setsizeframe)
        self.setsizeframe.init_values(self.values)
        self.setsizeframe.Show()
        return True

    def final_values(self):
        return self.values.user, self.values.password, self.values.cancel

# end of class HolditApp

def credentials_from_gui():
    gui = HolditApp(0)
    gui.MainLoop()
    return gui.final_values()
