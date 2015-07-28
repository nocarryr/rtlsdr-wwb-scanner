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

from wwb_scanner.core import JSONMixin
from wwb_scanner.ui.kivyui import plots
from wwb_scanner.ui.kivyui.actions import Action
from wwb_scanner.ui.kivyui.scan import ScanProgress

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
