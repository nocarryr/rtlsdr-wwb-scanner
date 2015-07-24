import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.properties import (
    ObjectProperty, NumericProperty, ListProperty, StringProperty
)
from kivy.garden.filebrowser import FileBrowser

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

class RootWidget(BoxLayout):
    plot_container = ObjectProperty(None)
    scan_controls = ObjectProperty(None)
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
        
    


class MainApp(App):
    def build(self):
        return RootWidget()
    def on_action_button_release(self, btn):
        btn.parent.parent.dismiss()
        Action.trigger_by_name(btn.action, self)
    
class PlotContainer(BoxLayout):
    spectrum_graph = ObjectProperty(None)
    def add_plot(self, **kwargs):
        fn = kwargs.get('filename')
        if fn is not None:
            kwargs.setdefault('name', os.path.basename(fn))
        plot = self.spectrum_graph.add_plot(**kwargs)
        self.tool_panel.add_plot(plot)
    
class ScanControls(BoxLayout):
    scan_range_widget = ObjectProperty(None)
    gain_txt = ObjectProperty(None)
    start_btn = ObjectProperty(None)
    def on_scan_button_release(self):
        self.scan_progress = ScanProgress(scan_controls=self)
        self.parent.show_popup(title='Scanning', content=self.scan_progress, 
                               size_hint=(.5, .8), auto_dismiss=False)
        self.scan_progress.run_scan()
    
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
    
def run():
    MainApp().run()

if __name__ == '__main__':
    run()
