import threading

from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.textinput import TextInput
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.properties import (
    ObjectProperty, 
    StringProperty, 
    BooleanProperty, 
    NumericProperty, 
    ListProperty, 
    AliasProperty, 
)
from kivy.clock import Clock

from wwb_scanner.core import JSONMixin
from wwb_scanner.scanner import Scanner


class ScanControls(BoxLayout, JSONMixin):
    scan_range_widget = ObjectProperty(None)
    gain_dropdown = ObjectProperty(None)
    start_btn = ObjectProperty(None)
    stop_btn = ObjectProperty(None)
    scanning = BooleanProperty(False)
    idle = BooleanProperty(True)
    gain = NumericProperty(30.)
    samples_per_scan = NumericProperty()
    window_size = NumericProperty()
    def get_scan_range(self):
        return self.scan_range_widget.scan_range
    def set_scan_range(self, value):
        self.scan_range_widget.scan_range = value
    scan_range = AliasProperty(get_scan_range, set_scan_range)
    def get_gain(self):
        return self.gain_txt.text
    def __init__(self, **kwargs):
        super(ScanControls, self).__init__(**kwargs)
        self.get_scan_defaults()
        self.gain_dropdown = ScanGainDropDown(scan_controls=self)
        self.scan_progress = ScanProgress()
    def on_parent(self, *args, **kwargs):
        self.scan_progress.root_widget = self.parent
    def get_scan_defaults(self):
        scanner = Scanner()
        self.samples_per_scan = scanner.samples_per_scan
        self.window_size = scanner.window_size
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
    scan_controls = ObjectProperty(None)
    range_index = NumericProperty(-1.)
    value = NumericProperty()
    def __init__(self, **kwargs):
        super(ScanRangeTextInput, self).__init__(**kwargs)
    def on_scan_controls(self, *args):
        if self.scan_controls is None:
            return
        if self.range_index < 0:
            return
        self.value = self.scan_controls.scan_range[self.range_index]
        self.set_text_from_value()
    def on_range_index(self, instance, value):
        if self.scan_controls is None:
            return
        self.value = self.scan_controls.scan_range[self.range_index]
        self.set_text_from_value()
    def on_value(self, instance, value):
        self.scan_controls.scan_range[self.range_index] = value
        self.set_text_from_value(value)
    def on_focus(self, instance, value):
        if value:
            return
        self.value = float(self.text)
    def set_text_from_value(self, value=None):
        if value is None:
            value = self.value
        t = '%07.3f' % (value)
        if self.text != t:
            self.text = t

class ScanGainDropDown(DropDown):
    scan_controls = ObjectProperty(None)
    gains = ListProperty()
    gain_buttons = ListProperty()
    def on_scan_controls(self, *args, **kwargs):
        if self.scan_controls is None:
            return
        self.get_gains()
    def get_gains(self, *args, **kwargs):
        scanner = Scanner()
        gains = scanner.gains
        if gains is None:
            self.gains.append(0.)
            return
        self.gains = gains
        self.scan_controls.gain = scanner.gain
    def on_gains(self, *args, **kwargs):
        scan_controls = self.scan_controls
        for i, gain in enumerate(self.gains):
            try:
                btn = self.gain_buttons[i]
            except IndexError:
                btn = None
            if btn is not None:
                if btn.gain == gain:
                    continue
                old_gain = btn.gain
                btn.gain = gain
                if scan_controls is not None and scan_controls.gain == old_gain:
                    scan_controls.gain = gain
            else:
                btn = ScanGainDropDownBtn(gain=gain)
                self.add_widget(btn)

class ScanGainDropDownBtn(Button):
    gain = NumericProperty()

class ScanProgress(EventDispatcher):
    name = StringProperty()
    scan_controls = ObjectProperty(None)
    status_bar = ObjectProperty(None)
    root_widget = ObjectProperty(None)
    plot = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(ScanProgress, self).__init__(**kwargs)
        self.scanner = None
        self.scan_thread = None
    def on_root_widget(self, *args, **kwargs):
        self.get_widgets()
    def get_widgets(self):
        r = self.root_widget
        if r is None:
            return
        if self.scan_controls is None:
            self.scan_controls = r.scan_controls
        if self.status_bar is None:
            self.status_bar = r.status_bar
    def build_scanner(self):
        self.get_widgets()
        scan_range = self.scan_controls.scan_range
        graph_widget = self.root_widget.plot_container.spectrum_graph
        graph_widget.auto_scale_x = False
        graph_widget.x_min = scan_range[0]
        graph_widget.x_max = scan_range[1]
        gain = self.scan_controls.gain
        self.name = ' - '.join([str(v) for v in scan_range])
        self.status_bar.progress = 0.
        self.status_bar.message_text = 'Scanning %s' % (self.name)
        self.scanner = Scanner(scan_range=scan_range, gain=gain, 
                               samples_per_scan=self.scan_controls.samples_per_scan, 
                               window_size=self.scan_controls.window_size)
        self.scanner.on_progress = self.on_scanner_progress
        self.scan_thread = ScanThread(scanner=self.scanner, callback=self.on_scanner_finished)
        self.run_scan()
    def on_scanner_progress(self, value):
        Clock.schedule_once(self.update_progress)
    def update_progress(self, *args, **kwargs):
        progress = float(self.scanner.progress)
        self.status_bar.progress = progress
        if int(progress * 100) % 2 == 0:
            self.show_scan()
    def run_scan(self):
        Clock.schedule_once(self._run_scan)
    def _run_scan(self, *args, **kwargs):
        self.scan_thread.start()
    def on_scanner_finished(self):
        def do_update(*args, **kwargs):
            self.show_scan()
            self.cleanup()
        Clock.schedule_once(do_update)
    def cancel_scan(self, *args, **kwargs):
        if self.scanner._running.is_set():
            self.scanner.stop_scan()
    def cleanup(self):
        if self.scanner is not None:
            self.scanner = None
        if self.scan_thread is not None:
            self.scan_thread = None
        self.scan_controls.scanning = False
        self.scan_controls.idle = True
    def show_scan(self):
        if self.scanner is None:
            return
        spectrum = self.scanner.spectrum
        if self.plot is None:
            plot_container = self.root_widget.plot_container
            self.plot = plot_container.add_plot(spectrum=spectrum, name=self.name)
        else:
            self.plot.update_data()
        
    
class ScanThread(threading.Thread):
    def __init__(self, **kwargs):
        super(ScanThread, self).__init__()
        self.scanner = kwargs.get('scanner')
        self.callback = kwargs.get('callback')
    def run(self):
        self.scanner.run_scan()
        self.callback()
        
