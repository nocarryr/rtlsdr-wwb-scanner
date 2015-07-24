import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.properties import (
    ObjectProperty, NumericProperty, ListProperty
)
from kivy.garden.filebrowser import FileBrowser

from wwb_scanner.ui.kivyui import plots
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
    def do_action(self, app):
        pass
    
class FileQuit(Action):
    name = 'file.quit'
    def do_action(self, app):
        app.stop()
    
class PlotsImport(Action):
    name = 'plots.import'
    @property
    def last_path(self):
        p = getattr(self, '_last_path', None)
        if p is None:
            p = os.getcwd()
        return p
    def do_action(self, app):
        self.app = app
        browser = FileBrowser(select_string='Import', path=self.last_path)
        browser.bind(on_success=self.on_browser_success)
        browser.bind(on_canceled=self.on_browser_canceled)
        app.root.show_popup(title='Import Plot', content=browser, 
                            size_hint=(.9, .9), auto_dismiss=False)
    def on_browser_success(self, instance):
        filename = instance.selection[0]
        self.app.root.close_popup()
        spectrum = BaseImporter.import_file(filename)
        self.app.root.plot_container.add_plot(spectrum=spectrum, filename=filename)
    def on_browser_canceled(self, instance):
        self.app.root.close_popup()
        
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
        print self.scan_range_widget.scan_range
    
class ScanRangeControls(BoxLayout):
    scan_range_start_txt = ObjectProperty(None)
    scan_range_end_txt = ObjectProperty(None)
    scan_range = ListProperty([470., 900.])
    
class ScanRangeTextInput(TextInput):
    range_index = NumericProperty(-1.)
    value = NumericProperty()
    def __init__(self, **kwargs):
        super(ScanRangeTextInput, self).__init__(**kwargs)
        self.bind(value=self.on_value_changed)
        self.bind(range_index=self.on_range_index_set)
    def on_range_index_set(self, instance, value):
        self.value = self.parent.scan_range[self.range_index]
        self.set_text_from_value()
    def validate_input(self):
        self.value = float(self.text)
    def on_value_changed(self, instance, value):
        self.parent.scan_range[self.range_index] = value
        self.set_text_from_value(value)
    def set_text_from_value(self, value=None):
        if value is None:
            value = self.value
        t = '%07.3f' % (value)
        if self.text != t:
            self.text = t
    
def run():
    MainApp().run()

if __name__ == '__main__':
    run()
