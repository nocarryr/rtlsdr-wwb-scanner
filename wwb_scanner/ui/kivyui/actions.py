import os

from kivy.garden.filebrowser import FileBrowser

from wwb_scanner.file_handlers import BaseImporter

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
    
class PlotsImport(Action, FileAction):
    name = 'plots.import'
    select_string = 'Import'
    title = 'Import Plot'
    def get_filters(self):
        exts = ['csv', 'sbd2']
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
    filters = ['*.csv', '*.CSV']
    def do_action(self, app):
        self.plot = app.root.plot_container.spectrum_graph.selected
        if self.plot is None:
            app.root.show_message(message='There is not plot to export')
            return
        super(PlotsExport, self).do_action(app)
    def on_browser_success(self, instance):
        filename = instance.filename
        if not len(filename):
            self.app.root.show_message(message='Please enter a filename')
            return
        _fn, ext = os.path.splitext(filename)
        if not len(ext):
            filename = os.path.extsep.join([_fn, 'csv'])
        elif '*.%s' % (ext) not in self.filters:
            self.app.root.show_message(message='Only "csv" files are currently supported')
            return
        filename = os.path.join(instance.path, filename)
        self.dismiss()
        self.plot.spectrum.export_to_file(filename=filename)
        self.app.root.show_message(title='Success', message='File exported to\n%s' % (filename))
        
    
Action.build_from_subclasses()
