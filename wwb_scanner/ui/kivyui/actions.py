import os
import datetime

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.treeview import TreeView, TreeViewLabel
from kivy.garden.filebrowser import FileBrowser
from kivy.properties import ObjectProperty, OptionProperty, ListProperty, BooleanProperty

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
    tree = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(ScrolledTree, self).__init__(**kwargs)
        self.bind(minimum_height=self.setter('height'))

class ScrolledTreeNode(TreeViewLabel):
    pass

class PlotsLoadRecent(Action):
    name = 'plots.load_recent'
    sort_field = OptionProperty('Date', options=('id', 'Name', 'Date'))
    sort_ascending = BooleanProperty(True)
    scan_nodes = ListProperty([])
    def do_action(self, app):
        self.app = app
        scan_data = db_store.get_all_scans()
        scroll_view = ScrolledTree()
        tree_view = scroll_view.tree
        self.tree_view = tree_view
        # for eid, scan in scan_data.items():
        #     dt = datetime.datetime.fromtimestamp(scan['timestamp_utc'])
        #     name = str(scan.get('name'))
        #     txt = ' - '.join([name, str(dt)])
        #     scan_node = tree_view.add_node(ScrolledTreeNode(text=txt))
        #     scan_node.eid = eid
        self.populate_nodes()
        load_btn = Button(text='Load')
        cancel_btn = Button(text='Cancel')
        hbox = BoxLayout(orientation='horizontal', size_hint_y=.1)
        hbox.add_widget(load_btn)
        hbox.add_widget(cancel_btn)
        vbox = BoxLayout(orientation='vertical')
        vbox.add_widget(scroll_view)
        vbox.add_widget(hbox)
        cancel_btn.bind(on_release=self.on_cancel)
        load_btn.bind(on_release=self.on_load)
        app.root.show_popup(title='Load Scan', content=vbox, size_hint=(.9, .9))
    def populate_nodes(self):
        for node in self.scan_nodes:
            self.tree_view.remove_node(node)
        self.scan_nodes.clear()
        scan_data = db_store.get_all_scans()
        if self.sort_field == 'id':
            eids = sorted(scan_data.keys())
            if not self.sort_ascending:
                eids = reversed(eids)
            eids = list(eids)
            scans = [scan for scan in eids]
        else:
            d = {}
            for eid, scan in scan_data.items():
                if self.sort_field == 'Name':
                    key = scan.get('name')
                elif self.sort_field == 'Date':
                    key = datetime.datetime.fromtimestamp(scan.get('timestamp_utc'))
                d[key] = (eid, scan)
            keys = sorted(d.keys())
            if not self.sort_ascending:
                keys = reversed(keys)
            eids = []
            scans = []
            for key in keys:
                eid, scan = d[key]
                eids.append(eid)
                scans.append(scan)
        for eid, scan in zip(eids, scans):
            dt = datetime.datetime.fromtimestamp(scan['timestamp_utc'])
            name = str(scan.get('name'))
            txt = ' - '.join([name, str(dt)])
            scan_node = self.tree_view.add_node(ScrolledTreeNode(text=txt))
            scan_node.eid = eid
            self.scan_nodes.append(scan_node)
    def on_cancel(self, *args):
        self.app.root.close_popup()
        self.tree_view = None
    def on_load(self, *args):
        node = self.tree_view.selected_node
        if node is None:
            return
        spectrum = Spectrum.from_dbstore(eid=node.eid)
        self.app.root.plot_container.add_plot(spectrum=spectrum)
        self.on_cancel()

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
