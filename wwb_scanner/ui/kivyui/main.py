import os

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.popup import Popup
from kivy.app import App
from kivy.properties import (
    ObjectProperty,
    NumericProperty, 
    StringProperty,
)

from wwb_scanner.core import JSONMixin
from wwb_scanner.ui.kivyui import plots
from wwb_scanner.ui.kivyui import scan
from wwb_scanner.ui.kivyui import actions
from wwb_scanner.ui.kivyui.actions import Action

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
    


class RTLSDRScannerApp(App):
    def build(self):
        return RootWidget()
    def on_action_button_release(self, btn):
        btn.parent.parent.dismiss()
        Action.trigger_by_name(btn.action, self)
    
class PlotContainer(FloatLayout, JSONMixin):
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
    
class MessageDialog(BoxLayout):
    message = StringProperty()
    close_text = StringProperty('Close')
    
class StatusBar(BoxLayout):
    message_box = ObjectProperty(None)
    progress_bar = ObjectProperty(None)
    message_text = StringProperty('')
    progress = NumericProperty(0.)
    
def run():
    RTLSDRScannerApp().run()

if __name__ == '__main__':
    run()
