from collections import OrderedDict

import wx

class Menubar(object):
    def __init__(self, **kwargs):
        self.mainwindow = kwargs.get('mainwindow')
        self.mainwindow.menubar = self
        self._menubar = wx.MenuBar()
        self.mainwindow.SetMenuBar(self._menubar)
        self.menus = OrderedDict()
    def add_menu(self, menu):
        self.menus[menu.name] = menu
        self._menubar.Append(menu._menu, menu.label)
        
class Menu(object):
    def __init__(self, **kwargs):
        self.mainwindow = kwargs.get('mainwindow')
        if not hasattr(self.mainwindow, 'menubar'):
            self.menubar = Menubar(mainwindow=self.mainwindow)
        else:
            self.menubar = self.mainwindow.menubar
        if not hasattr(self, 'name'):
            self.name = kwargs.get('name', self.__class__.__name__)
        if not hasattr(self, 'label'):
            self.label = self.name
        self._menu = wx.Menu()
        self.menu_item_data = OrderedDict()
        self.menu_items = OrderedDict()
        self.build_items(**kwargs)
        self.add_to_menubar()
    def build_items(self, **kwargs):
        pass
    def add_to_menubar(self):
        self.menubar.add_menu(self)
    def on_activate(self, **kwargs):
        kwargs['menu'] = self
        self.mainwindow.on_menuitem_activate(**kwargs)
        
class MenuItem(object):
    def __init__(self, item_id, label, text, **kwargs):
        self.id = item_id
        self.label = label
        self.text = text
        self.menu = kwargs.get('menu')
        self._menuitem = self.menu._menu.Append(self.id, self.label, self.text)
        self.menu.mainwindow.Bind(wx.EVT_MENU, self.on_activate, self._menuitem)
    def on_activate(self, e):
        self.menu.on_activate(menuitem=self, event=e)
        
class FileMenu(Menu):
    name = 'File'
    label = '&File'
    def build_items(self, **kwargs):
        items = self.menu_items
        items['exit'] = MenuItem(wx.ID_EXIT, 'E&xit', ' Exit', menu=self)
    
MENUS = [FileMenu]
