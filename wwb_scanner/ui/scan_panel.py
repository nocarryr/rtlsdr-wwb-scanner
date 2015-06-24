import wx

class ScanPanel(wx.Panel):
    def __init__(self, parent):
        super(ScanPanel, self).__init__(parent)
        grid = wx.GridBagSizer(hgap=4, vgap=4)
        self.lblRangeStart = wx.StaticText(self, label='Start Frequency')
        self.spinRangeStart = wx.SpinCtrlDouble(self, value="400.000", initial=400.)
        self.lblRangeEnd = wx.StaticText(self, label='End Frequency')
        self.spinRangeEnd = wx.SpinCtrlDouble(self, value="900.000", initial=900.)
        grid.Add(self.lblRangeStart, pos=(0, 0))
        grid.Add(self.spinRangeStart, pos=(1, 0))
        grid.Add(self.lblRangeEnd, pos=(1, 0))
        grid.Add(self.spinRangeEnd, pos=(1, 1))
        self.SetSizer(grid)
