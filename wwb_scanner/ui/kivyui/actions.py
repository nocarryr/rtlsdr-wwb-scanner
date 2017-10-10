import os
import datetime

from kivy.clock import Clock
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.treeview import TreeView, TreeViewNode
from kivy.uix.behaviors import ButtonBehavior
from kivy.garden.filebrowser import FileBrowser
from kivy.properties import (
    ObjectProperty,
    DictProperty,
    NumericProperty,
    StringProperty,
    ColorProperty,
    ListProperty,
    BooleanProperty,
    AliasProperty,
    OptionProperty,
)

from wwb_scanner.utils.color import Color
from wwb_scanner.utils.dbstore import db_store
from wwb_scanner.file_handlers import BaseImporter
from wwb_scanner.scan_objects import Spectrum

class Action(object):
    _instances = {}
    def __init__(self, **kwargs):
        if not hasattr(self, 'name'):
            self.name = kwargs.get('name')
        self.callback = kwargs.get('callback')
        Action._instances[self.name] = self
    @classmethod
    def build_from_subclasses(cls):
        for _cls in Action.__subclasses__():
            _cls()
    @classmethod
    def trigger_by_name(cls, name, app):
        action = Action._instances.get(name)
        return action(app)
    def __call__(self, app):
        cb = self.callback
        if cb is not None:
            return cb(action=self, app=app)
        return self.do_action(app)

class FileQuit(Action):
    name = 'file.quit'
    def do_action(self, app):
        app.stop()

class FileAction(object):
    @property
    def last_path(self):
        return self.get_last_path()
    def get_last_path(self):
        p = getattr(self, '_last_path', None)
        if p is None:
            p = os.getcwd()
        return p
    def get_select_string(self):
        return getattr(self, 'select_string', '')
    def get_title(self):
        return getattr(self, 'title', '')
    def get_filters(self):
        return getattr(self, 'filters', [])
    def build_browser(self, **kwargs):
        kwargs.setdefault('select_string', self.get_select_string())
        kwargs.setdefault('path', self.last_path)
        kwargs.setdefault('filters', self.get_filters())
        return FileBrowser(**kwargs)
    def do_action(self, app):
        self.app = app
        title = self.get_title()
        browser = self.build_browser()
        browser.bind(on_success=self.on_browser_success)
        browser.bind(on_canceled=self.on_browser_canceled)
        app.root.show_popup(title=title, content=browser,
                            size_hint=(.9, .9), auto_dismiss=False)
    def dismiss(self):
        self.app.root.close_popup()
    def on_browser_success(self, instance):
        self.dismiss()
    def on_browser_canceled(self, instance):
        self.dismiss()

class FileSaveAs(Action, FileAction):
    name = 'file.save_as'
    select_string = 'Save As'
    title = 'Save Session As'
    filters = ['*.json', '*.JSON']
    def on_browser_success(self, instance):
        filename = instance.filename
        if not len(filename):
            self.app.root.show_message(message='Please enter a filename')
            return
        _fn, ext = os.path.splitext(filename)
        if not len(ext):
            filename = os.path.extsep.join([_fn, 'json'])
        #elif '*.%s' % (ext) not in self.filters:
        #    self.app.root.show_message(message='Only "json" files are currently supported')
        #    return
        filename = os.path.join(instance.path, filename)
        self.dismiss()
        s = self.app.root.to_json(indent=2)
        with open(filename, 'w') as f:
            f.write(s)
        self.app.root.current_filename = filename
        self.app.root.show_message(title='Success', message='File saved as\n%s' % (filename))

class FileSave(Action):
    name = 'file.save'
    def do_action(self, app):
        filename = app.root.current_filename
        if not filename:
            Action.trigger_by_name('file.save_as', app)
            return
        s = app.root.to_json(indent=2)
        with open(filename, 'w') as f:
            f.write(s)
        app.root.status_bar.message_text = 'File saved'

class FileOpen(Action, FileAction):
    name = 'file.open'
    select_string = 'Open'
    title = 'Open Session'
    filters = ['*.json', '*.JSON']
    def on_browser_success(self, instance):
        filename = os.path.join(instance.path, instance.filename)
        with open(filename, 'r') as f:
            s = f.read()
        self.dismiss()
        self.app.root.instance_from_json(s)
        self.app.root.current_filename = filename

class ScrolledTree(BoxLayout):
    app = ObjectProperty(None)
    tree = ObjectProperty(None)
    sort_header = ObjectProperty(None)
    __events__ = ['on_cancel', 'on_load']
    def on_cancel(self, *args):
        self.app.root.close_popup()
    def on_load(self, *args):
        node = self.tree.selected_node
        if node is None:
            return
        spectrum = Spectrum.from_dbstore(eid=node.eid)
        self.app.root.plot_container.add_plot(spectrum=spectrum)
        self.app.root.close_popup()
    def on_sort_header(self, *args):
        self.sort_header.bind(active_cell=self.on_sort_cell, descending=self.on_sort_descending)
    def on_sort_cell(self, instance, cell):
        if cell is None:
            self.tree.root.sort_property_name = '__index__'
        else:
            self.tree.root.sort_property_name = cell.sort_property
    def on_sort_descending(self, instance, value):
        self.tree.root.descending = value

class SortableNode(TreeViewNode):
    tree_view = ObjectProperty(None, allownone=True)
    sort_property_name = StringProperty('__index__')
    sort_property_uids = DictProperty()
    descending = BooleanProperty(False)
    def __init__(self, **kwargs):
        self._trigger_sort = None
        super(SortableNode, self).__init__(**kwargs)
        trigger = Clock.create_trigger(self._sort_children, 0)
        trigger()
        self._trigger_sort = trigger
    def on_nodes(self, *args):
        need_sort = False
        keys = set()
        for node in self.nodes:
            key = hash(node)
            keys.add(key)
            if key not in self.sort_property_uids:
                need_sort = True
                self._bind_child_prop(node)
        to_remove = keys - set(self.sort_property_uids.keys())
        for key in to_remove:
            uid, prop, node = self.sort_property_uids[key]
            self._unbind_child_prop(node)
        if need_sort and self._trigger_sort is not None:
            self._trigger_sort()
    def on_sort_property_name(self, instance, prop):
        if self._trigger_sort is None:
            return
        for node in self.nodes:
            self._unbind_child_prop(node)
            self._bind_child_prop(node)
        self._trigger_sort()
    def on_descending(self, instance, value):
        if self._trigger_sort is None:
            return
        self._trigger_sort()
    def _bind_child_prop(self, node):
        prop = self.sort_property_name
        if prop == '__index__':
            return
        key = hash(node)
        if key in self.sort_property_uids:
            return
        uid = node.fbind(prop, self.on_child_sort_property_value, property_name=prop)
        self.sort_property_uids[key] = (uid, prop, node)
    def _unbind_child_prop(self, node):
        key = hash(node)
        val = self.sort_property_uids.get(key)
        if val is None:
            return
        del self.sort_property_uids[key]
        uid, prop, node = val
        node.unbind_uid(prop, uid)
    def on_child_sort_property_value(self, instance, value, **kwargs):
        prop = kwargs.get('property_name')
        if prop != self.sort_property_name:
            return
        self._trigger_sort()
    def _sort_children(self, *args, **kwargs):
        tv = self.tree_view
        if tv is None:
            return
        prop = self.sort_property_name
        if prop == '__index__':
            return
        def iter_vals():
            vals = {getattr(n, prop) for n in self.nodes}
            if self.descending:
                it = reversed(sorted(vals))
            else:
                it = sorted(vals)
            for v in it:
                yield v
        def iter_nodes():
            yielded = set()
            nodes = set(self.nodes)
            for v in iter_vals():
                for n in nodes.copy():
                    if getattr(n, prop) != v:
                        continue
                    yield n
                    nodes.discard(n)

        nodes = [n for n in iter_nodes()]
        self.nodes = nodes
        tv._trigger_layout()

class SortableTreeViewLabel(Label, SortableNode):
    pass

class SortableTreeView(TreeView):
    def add_node(self, node, parent=None):
        if getattr(self, '_root', None) is None:
            node = SortableTreeViewLabel(text='Root', is_open=True, level=0)
            for key, value in self.root_options.items():
                setattr(node, key, value)
        node.tree_view = self
        super(SortableTreeView, self).add_node(node, parent)
        parent = node.parent_node
        if parent is not None:
            parent._bind_child_prop(node)
            parent._trigger_sort()
        return node
    def remove_node(self, node):
        node.tree_view = None
        super(SortableTreeView, self).remove_node(node)

class ScrolledTreeView(SortableTreeView):
    def __init__(self, **kwargs):
        kwargs['root_options'] = {'sort_property_name':'datetime'}
        super(ScrolledTreeView, self).__init__(**kwargs)
        self.bind(minimum_height=self.setter('height'))
        scan_data = db_store.get_all_scans()
        for eid, scan in scan_data.items():
            scan_node = self.add_node(ScrolledTreeNode(eid=eid, scan_data=scan))

class SortHeader(BoxLayout):
    cells = ListProperty()
    active_cell = ObjectProperty(None, allownone=True)
    descending = BooleanProperty(False)
    def add_widget(self, widget, index=0):
        super(SortHeader, self).add_widget(widget, index)
        if isinstance(widget, SortHeaderCell):
            self.cells.append(widget)
            widget.bind(
                selected=self.on_cell_selected,
                descending=self.on_cell_descending,
            )
    def on_active_cell(self, instance, cell):
        for w in self.cells:
            if w is cell:
                continue
            w.selected = False
        self.descending = cell.descending
    def on_cell_selected(self, instance, value):
        if not value:
            return
        self.active_cell = instance
    def on_cell_descending(self, instance, value):
        if not instance.selected:
            return
        self.descending = value

class SortHeaderCell(ButtonBehavior, BoxLayout):
    text = StringProperty()
    sort_property = StringProperty()
    selected = BooleanProperty(False)
    descending = BooleanProperty(False)
    icon_name = StringProperty('fa-sort')
    _inactive_icon_name = 'fa-sort'
    _active_icon_names = {True: 'fa-sort-desc', False: 'fa-sort-asc'}
    #_inactive_icon_name = u'\u21c5'
    #_active_icon_names = {True:u'\u25b2', False:u'\u25bc'}
    direction = OptionProperty('None', options=['up', 'down', 'None'])
    def on_release(self, *args):
        if self.selected:
            self.descending = not self.descending
        else:
            self.selected = True
    def on_selected(self, instance, value):
        if not value:
            self.descending = False
            self.direction = 'None'
            self.icon_name = self._inactive_icon_name
        else:
            if self.descending:
                self.direction = 'down'
            else:
                self.direction = 'up'
            self.icon_name = self._active_icon_names.get(self.descending)
    def on_descending(self, instance, value):
        if self.selected:
            if value:
                self.direction = 'down'
            else:
                self.direction = 'up'
            self.icon_name = self._active_icon_names.get(value)


class ScrolledTreeNode(BoxLayout, SortableNode):
    eid = NumericProperty()
    name = StringProperty()
    datetime = ObjectProperty()
    scan_color = ColorProperty([0,0,0,0])
    scan_data = DictProperty()
    def __init__(self, **kwargs):
        super(ScrolledTreeNode, self).__init__(**kwargs)
        self.name = str(self.scan_data.get('name'))
        self.datetime = datetime.datetime.fromtimestamp(self.scan_data['timestamp_utc'])
        c = Color(**self.scan_data['color'])
        self.scan_color = c.to_list()

class SquareTexture(Widget):
    def get_rect_size(self):
        w, h = self.size
        if h < w:
            size = [h, h]
        else:
            size = [w, w]
        return size
    def set_rect_size(self, value):
        pass
    rect_size = AliasProperty(get_rect_size, set_rect_size, bind=['size'])
    def get_rect_pos(self):
        w, h = self.rect_size
        x = self.center_x - w/2.
        y = self.center_y - h/2.
        return [x, y]
    def set_rect_pos(self, value):
        pass
    rect_pos = AliasProperty(get_rect_pos, set_rect_pos, bind=['pos', 'rect_size'])

class ColorBox(SquareTexture):
    scan_color = ColorProperty([0,0,0,0])


class PlotsLoadRecent(Action):
    name = 'plots.load_recent'
    def do_action(self, app):
        self.app = app
        scroll_view = ScrolledTree()
        app.root.show_popup(title='Load Scan', content=scroll_view, size_hint=(.9, .9))

class PlotsImport(Action, FileAction):
    name = 'plots.import'
    select_string = 'Import'
    title = 'Import Plot'
    def get_filters(self):
        exts = ['csv', 'sdb2']
        filters = ['.'.join(['*', ext]) for ext in exts]
        filters.extend(['.'.join(['*', ext.upper()]) for ext in exts])
        return filters
    def on_browser_success(self, instance):
        filename = instance.selection[0]
        self.dismiss()
        spectrum = BaseImporter.import_file(filename)
        self.app.root.plot_container.add_plot(spectrum=spectrum, filename=filename)

class PlotsExport(Action, FileAction):
    name = 'plots.export'
    select_string = 'Export'
    title = 'Export Selected Plot'
    def get_filters(self):
        exts = ['csv', 'sdb2']
        filters = ['.'.join(['*', ext]) for ext in exts]
        filters.extend(['.'.join(['*', ext.upper()]) for ext in exts])
        return filters
    def do_action(self, app):
        self.plot = app.root.plot_container.spectrum_graph.selected
        if self.plot is None:
            app.root.show_message(message='There is not plot to export')
            return
        super(PlotsExport, self).do_action(app)
    def on_browser_success(self, instance):
        filters = self.get_filters()
        filename = instance.filename
        if not len(filename):
            self.app.root.show_message(message='Please enter a filename')
            return
        _fn, ext = os.path.splitext(filename)
        if not len(ext):
            filename = os.path.extsep.join([_fn, 'csv'])
        elif '*.%s' % (ext.lstrip('.')) not in filters:
            self.app.root.show_message(
                message='Only "csv" and "sdb2" files are currently supported',
            )
            return
        filename = os.path.join(instance.path, filename)
        self.dismiss()
        self.plot.spectrum.export_to_file(filename=filename)
        self.app.root.show_message(title='Success', message='File exported to\n%s' % (filename))


Action.build_from_subclasses()
