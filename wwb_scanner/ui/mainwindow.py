import wx

from wwb_scanner.ui.menubar import MENUS
from wwb_scanner.ui.graph_panel import GraphPanel
from wwb_scanner.ui.scan_panel import ScanPanel


class MainWindow(wx.Frame):
    def __init__(self, title='RTL-SDR WWB Scanner'):
        super(MainWindow, self).__init__(None, title=title)
        for cls in MENUS:
            cls(mainwindow=self)
        self.graph_panel = GraphPanel(self)
        self.scan_panel = ScanPanel(self)
        vbox = self.main_widget = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(self.graph_panel, 0, wx.EXPAND)
        vbox.Add(self.scan_panel)
        self.SetSizerAndFit(vbox)
        self.Show(True)
    def on_menuitem_activate(self, **kwargs):
        menuitem = kwargs.get('menuitem')
        if menuitem.id == wx.ID_EXIT:
            self.Close(True)
        
def main():
    app = wx.App(False)
    mainwin = MainWindow()
    app.MainLoop()
    
if __name__ == '__main__':
    main()
