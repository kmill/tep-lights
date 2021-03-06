#!/usr/bin/env python
# -*- coding: utf-8 -*-
# generated by wxGlade 0.6.3 on Fri Apr 16 03:13:32 2010

import wx
import threading

from cydmx import dmxwidget

# begin wxGlade: extracode
# end wxGlade

global_data = {
    'strobeEnable': False,
    'strobeDuty': 1,
    'hueAdj': 0.5,
    'brightnessAdj': 0.5,
}

class Strober(dmxwidget.Widget):

    def draw(self, panel):
        if global_data['strobeEnable']:
            panel.setall_rgb(0, 0, 0)
            for i in range(global_data['strobeDuty']):
                panel.outputAndWait(30)
        b = global_data['brightnessAdj']
        panel.setall_hbs(global_data['hueAdj'], b, 0)
        panel.outputAndWait(30)

class StrobeControlWin(wx.Frame):
    def __init__(self, *args, **kwds):
        # begin wxGlade: StrobeControlWin.__init__
        kwds["style"] = wx.ICONIZE|wx.MINIMIZE|wx.CLOSE_BOX|wx.MINIMIZE_BOX|wx.SYSTEM_MENU
        wx.Frame.__init__(self, *args, **kwds)
        self.label_4 = wx.StaticText(self, -1, "Strobe Control:")
        self.panel_1 = wx.Panel(self, -1)
        self.slider_4 = wx.Slider(self, -1, 1000, 0, 1000)
        self.checkbox_1 = wx.CheckBox(self, -1, "Enable Strobe")
        self.panel_2 = wx.Panel(self, -1)
        self.label_2 = wx.StaticText(self, -1, "Color Adjust:")
        self.slider_2 = wx.Slider(self, -1, 500, 0, 1000)
        self.label_3 = wx.StaticText(self, -1, "Brightness Adjust:")
        self.slider_3 = wx.Slider(self, -1, 500, 0, 1000)

        self.__set_properties()
        self.__do_layout()

        self.Bind(wx.EVT_COMMAND_SCROLL, self.freqAdj, self.slider_4)
        self.Bind(wx.EVT_CHECKBOX, self.enableStrobe, self.checkbox_1)
        self.Bind(wx.EVT_COMMAND_SCROLL, self.hueAdj, self.slider_2)
        self.Bind(wx.EVT_COMMAND_SCROLL, self.adjBrightness, self.slider_3)
        # end wxGlade

    def __set_properties(self):
        # begin wxGlade: StrobeControlWin.__set_properties
        self.SetTitle("Visualization Adjuster")
        self.SetSize((443, 408))
        self.label_4.SetFont(wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_2.SetFont(wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        self.label_3.SetFont(wx.Font(13, wx.DEFAULT, wx.NORMAL, wx.BOLD, 0, ""))
        # end wxGlade

    def __do_layout(self):
        # begin wxGlade: StrobeControlWin.__do_layout
        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1 = wx.GridSizer(3, 2, 0, 0)
        sizer_2 = wx.BoxSizer(wx.VERTICAL)
        grid_sizer_1.Add(self.label_4, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_2.Add(self.panel_1, 1, 0, 0)
        sizer_2.Add(self.slider_4, 7, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE, 0)
        sizer_2.Add(self.checkbox_1, 0, wx.EXPAND, 0)
        sizer_2.Add(self.panel_2, 1, wx.EXPAND, 0)
        grid_sizer_1.Add(sizer_2, 8, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 3)
        grid_sizer_1.Add(self.label_2, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.slider_2, 0, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.label_3, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        grid_sizer_1.Add(self.slider_3, 0, wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0)
        sizer_1.Add(grid_sizer_1, 2, wx.LEFT|wx.RIGHT|wx.EXPAND, 1)
        self.SetSizer(sizer_1)
        self.Layout()
        self.Centre()
        # end wxGlade

    def freqAdj(self, event): # wxGlade: StrobeControlWin.<event_handler>
        global_data['strobeDuty'] = min(max(int(-0.028 * self.slider_4.Value + 29), 1), 29)
        event.Skip()

    def hueAdj(self, event): # wxGlade: StrobeControlWin.<event_handler>
        global_data['hueAdj'] = (self.slider_2.Value) / 1000.0
        event.Skip()

    def adjBrightness(self, event): # wxGlade: StrobeControlWin.<event_handler>
        global_data['brightnessAdj'] = self.slider_3.Value / 1000.0
        event.Skip()

    def enableStrobe(self, event): # wxGlade: StrobeControlWin.<event_handler>
        global_data['strobeEnable'] = self.checkbox_1.Value
        event.Skip()

# end of class StrobeControlWin

class RunPanel(threading.Thread):
    def __init__(self, *args, **kwargs):
        super(RunPanel, self).__init__(*args, **kwargs)
        self.setDaemon(True)

    def run(self):
        dmxwidget.WidgetServer().run([Strober])


class StrobeConfig(wx.App):
    def OnInit(self):
        wx.InitAllImageHandlers()
        frame_1 = StrobeControlWin(None, -1, "")
        self.SetTopWindow(frame_1)
        frame_1.Show()
        return 1

# end of class StrobeConfig

if __name__ == "__main__":
    t = RunPanel()
    t.start()
    StrobeControl = StrobeConfig(0)
    StrobeControl.MainLoop()
