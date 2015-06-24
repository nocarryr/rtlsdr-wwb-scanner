import wx

from wwb_scanner.ui.menubar import MENUS

class MainWindow(wx.Frame):
    def __init__(self, title='RTL-SDR WWB Scanner'):
        super(MainWindow, self).__init__(None, title=title)
        for cls in MENUS:
            cls(mainwindow=self)
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
