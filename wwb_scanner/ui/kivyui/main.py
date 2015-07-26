import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.properties import (
    ObjectProperty,
    NumericProperty, 
    ListProperty, 
    StringProperty,
    BooleanProperty, 
    AliasProperty, 
)
from kivy.garden.filebrowser import FileBrowser

from wwb_scanner.core import JSONMixin
from wwb_scanner.ui.kivyui import plots
from wwb_scanner.ui.kivyui.scan import ScanProgress
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

class RootWidget(BoxLayout, JSONMixin):
    plot_container = ObjectProperty(None)
    scan_controls = ObjectProperty(None)
    status_bar = ObjectProperty(None)
    current_filename = StringProperty()
    def show_popup(self, **kwargs):
        self.close_popup()
        self._popup_content = kwargs.get('content')
        self._popup = Popup(**kwargs)
        self._popup.open()
        return self._popup
    def close_popup(self):
        if getattr(self, '_popup', None) is None:
            return
        self._popup.dismiss()
        self._popup = None
        self._popup_content = None
    def show_message(self, **kwargs):
        self.close_message()
        content = MessageDialog(**kwargs)
        self._message_popup = Popup(content=content, title=kwargs.get('title', ''), 
                                    size_hint=[.6, .6], auto_dismiss=False)
        self._message_popup.open()
    def close_message(self):
        if getattr(self, '_message_popup', None) is None:
            return
        self._message_popup.dismiss()
        self._message_popup = None
    def _serialize(self):
        attrs = ['plot_container', 'scan_controls']
        d = {attr:getattr(self, attr)._serialize() for attr in attrs}
        return d
    def _deserialize(self, **kwargs):
        for key, data in kwargs.items():
            obj = getattr(self, key)
            obj.instance_from_json(data)
    


class MainApp(App):
    def build(self):
        return RootWidget()
    def on_action_button_release(self, btn):
        btn.parent.parent.dismiss()
        Action.trigger_by_name(btn.action, self)
    
class PlotContainer(BoxLayout, JSONMixin):
    spectrum_graph = ObjectProperty(None)
    def add_plot(self, **kwargs):
        fn = kwargs.get('filename')
        if fn is not None:
            kwargs.setdefault('name', os.path.basename(fn))
        plot = self.spectrum_graph.add_plot(**kwargs)
        self.tool_panel.add_plot(plot)
        return plot
    def _serialize(self):
        d = {'spectrum_graph':self.spectrum_graph._serialize()}
        return d
    def _deserialize(self, **kwargs):
        data = kwargs.get('spectrum_graph')
        self.spectrum_graph.instance_from_json(data)
    
class ScanControls(BoxLayout, JSONMixin):
    scan_range_widget = ObjectProperty(None)
    gain_txt = ObjectProperty(None)
    start_btn = ObjectProperty(None)
    stop_btn = ObjectProperty(None)
    scanning = BooleanProperty(False)
    idle = BooleanProperty(True)
    gain = NumericProperty(30.)
    def get_scan_range(self):
        return self.scan_range_widget.scan_range
    def set_scan_range(self, value):
        self.scan_range_widget.scan_range = value
    scan_range = AliasProperty(get_scan_range, set_scan_range)
    def get_gain(self):
        return self.gain_txt.text
    def __init__(self, **kwargs):
        super(ScanControls, self).__init__(**kwargs)
        self.scan_progress = ScanProgress()
    def on_parent(self, *args, **kwargs):
        self.scan_progress.root_widget = self.parent
    def on_idle(self, instance, value):
        self.stop_btn.disabled = value
    def on_scan_button_release(self):
        self.scanning = True
        self.idle = False
        self.scan_progress.build_scanner()
    def on_stop_button_release(self):
        self.scan_progress.cancel_scan()
        self.idle = True
    def _serialize(self):
        d = dict(
            scan_range=self.scan_range, 
            gain=self.gain, 
        )
        return d
    def _deserialize(self, **kwargs):
        scan_range = kwargs.get('scan_range')
        gain = kwargs.get('gain')
        self.scan_range = scan_range
        self.gain = float(gain)
    
class ScanRangeControls(BoxLayout):
    scan_range_start_txt = ObjectProperty(None)
    scan_range_end_txt = ObjectProperty(None)
    scan_range = ListProperty([470., 900.])
    
class ScanRangeTextInput(TextInput):
    range_index = NumericProperty(-1.)
    value = NumericProperty()
    def __init__(self, **kwargs):
        super(ScanRangeTextInput, self).__init__(**kwargs)
        #self.bind(value=self.on_value_changed)
        self.bind(range_index=self.on_range_index_set)
    def on_range_index_set(self, instance, value):
        self.value = self.parent.scan_range[self.range_index]
        self.set_text_from_value()
    def validate_input(self):
        self.value = float(self.text)
    def on_value(self, instance, value):
        print instance, value
        self.parent.scan_range[self.range_index] = value
        self.set_text_from_value(value)
    def set_text_from_value(self, value=None):
        if value is None:
            value = self.value
        t = '%07.3f' % (value)
        if self.text != t:
            self.text = t
    
class MessageDialog(BoxLayout):
    message = StringProperty()
    close_text = StringProperty('Close')
    
class StatusBar(BoxLayout):
    message_box = ObjectProperty(None)
    progress_bar = ObjectProperty(None)
    message_text = StringProperty('')
    progress = NumericProperty(0.)
    
def run():
    MainApp().run()

if __name__ == '__main__':
    run()
