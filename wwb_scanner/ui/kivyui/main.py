from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.app import App
from kivy.properties import (
    ObjectProperty, NumericProperty, ListProperty
)


class RootWidget(BoxLayout):
    plot_container = ObjectProperty(None)
    scan_controls = ObjectProperty(None)
    


class MainApp(App):
    def build(self):
        return RootWidget()
    
class PlotContainer(BoxLayout):
    pass
    
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
    

if '__main__' == __name__:
    MainApp().run()
