import threading

from kivy.event import EventDispatcher
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.properties import (
    ObjectProperty,
    StringProperty,
    BooleanProperty,
    NumericProperty,
    ListProperty,
    DictProperty,
    OptionProperty,
)
from kivy.clock import Clock

from wwb_scanner.core import JSONMixin
from wwb_scanner.scanner import Scanner, RtlPowerScanner
from wwb_scanner.scan_objects import Spectrum

try:
    basestring = basestring
except NameError:
    basestring = str


class ScanControls(BoxLayout, JSONMixin):
    gain_dropdown = ObjectProperty(None)
    window_type_dropdown = ObjectProperty(None)
    start_btn = ObjectProperty(None)
    stop_btn = ObjectProperty(None)
    panel_widget = ObjectProperty(None)
    advanced_panel_item = ObjectProperty(None)
    last_tab = ObjectProperty(None)
    scanner_backend = StringProperty('builtin')
    scanning = BooleanProperty(False)
    scan_range = ListProperty([470., 900.])
    idle = BooleanProperty(True)
    gain = NumericProperty(30.)
    sample_rate = NumericProperty(2e6)
    freq_correction = NumericProperty(0)
    sweep_overlap_ratio = NumericProperty(.5)
    sweeps_per_scan = NumericProperty()
    samples_per_sweep = NumericProperty()
    window_size = NumericProperty(allownone=True)
    window_type = OptionProperty('boxcar',
                                 options=Scanner.WINDOW_TYPES + ['None'])
    fft_size = NumericProperty(None, allownone=True)
    rtl_bin_size = NumericProperty(0.025)
    rtl_crop = NumericProperty(50)
    rtl_fir_size = NumericProperty(4)
    serial_number = StringProperty('')
    is_remote = BooleanProperty(False)
    remote_hostname = StringProperty('127.0.0.1')
    remote_port = NumericProperty(1235)
    current_freq = NumericProperty(500.)
    live_spectrum_graph = ObjectProperty(None)
    live_view_visible = BooleanProperty(False)
    smoothing_enabled = BooleanProperty(False)
    smoothing_factor = NumericProperty(80.)
    scaling_enabled = BooleanProperty(False)
    scaling_min_db = NumericProperty(-140.)
    scaling_max_db = NumericProperty(-50.)
    def get_gain(self):
        return self.gain_txt.text
    def __init__(self, **kwargs):
        super(ScanControls, self).__init__(**kwargs)
        if not kwargs.get('__from_json__'):
            self.get_scan_defaults()
        self.gain_dropdown = ScanGainDropDown(scan_controls=self)
        self.window_type_dropdown = WindowTypeDropDown(scan_controls=self)
        self.scan_progress = ScanProgress()
    def on_parent(self, *args, **kwargs):
        self.scan_progress.root_widget = self.parent
    def on_panel_widget(self, *args, **kwargs):
        self.last_tab = self.panel_widget.current_tab
        self.panel_widget.bind(current_tab=self.on_panel_widget_current_tab)
    def on_advanced_panel_item(self, *args):
        panel_item = self.advanced_panel_item
        if panel_item is None:
            return
        if panel_item.content is not None:
            return
        self.on_scanner_backend()
    def on_scanner_backend(self, *args):
        panel_item = self.advanced_panel_item
        if panel_item is None:
            return
        if panel_item.content is not None:
            panel_item.remove_widget(panel_item.content)
        if self.scanner_backend == 'builtin':
            cls = AdvancedOptions
        else:
            cls = RtlPowerAdvancedOptions
        widget = cls()
        panel_item.add_widget(widget)
        widget.scan_controls = self
    def on_panel_widget_current_tab(self, *args, **kwargs):
        current_tab = self.panel_widget.current_tab
        live_view = getattr(self, 'live_view', None)
        if self.last_tab is None or current_tab != live_view:
            self.last_tab = current_tab
        if live_view is not None:
            self.live_view_visible = current_tab == live_view
    def get_scan_defaults(self):
        scanner = Scanner()
        self.sample_rate = scanner.sampling_config.sample_rate
        self.scan_range = scanner.config.scan_range
        self.gain = scanner.device_config.gain
        freq_correction = scanner.device_config.freq_correction
        if freq_correction is None:
            freq_correction = 0
        self.freq_correction = freq_correction
        self.sweep_overlap_ratio = scanner.sampling_config.sweep_overlap_ratio
        self.sweeps_per_scan = scanner.sweeps_per_scan
        self.samples_per_sweep = scanner.samples_per_sweep
        self.window_size = scanner.window_size
        self.window_type = scanner.sampling_config.window_type
        self.fft_size = scanner.sampling_config.get('fft_size')
        self.rtl_bin_size = scanner.sampling_config['rtl_bin_size']
        self.rtl_crop = scanner.sampling_config['rtl_crop']
        self.rtl_fir_size = scanner.sampling_config['rtl_fir_size']
        self.smoothing_enabled = scanner.config.processing.smoothing_enabled
        self.smoothing_factor = scanner.config.processing.smoothing_factor
        self.scaling_enabled = scanner.config.processing.scaling_enabled
        self.scaling_min_db = scanner.config.processing.scaling_min_db
        self.scaling_max_db = scanner.config.processing.scaling_max_db
        if scanner.device_config.serial_number is None:
            self.serial_number = ''
        else:
            self.serial_number = scanner.device_config.serial_number
        self.is_remote = scanner.device_config.is_remote
        self.remote_hostname = scanner.device_config.remote_hostname
        self.remote_port = scanner.device_config.remote_port
    def on_fft_size_input_focus(self, instance):
        if instance.focus:
            return
        if not len(instance.text):
            instance.text = '0'
        self.fft_size = int(instance.text)
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
        keys = ['scan_range', 'gain', 'sweeps_per_scan', 'samples_per_sweep',
                'sweep_overlap_ratio', 'window_size', 'window_type', 'fft_size',
                'rtl_bin_size', 'rtl_crop', 'rtl_fir_size',
                'smoothing_enabled', 'smoothing_factor',
                'scaling_enabled', 'scaling_min_db', 'scaling_max_db']
        d = {key: getattr(self, key) for key in keys}
        if len(self.serial_number):
            d['serial_number'] = self.serial_number
        else:
            d['serial_number'] = None
        return d
    def _deserialize(self, **kwargs):
        keys = ['scan_range', 'gain', 'sweeps_per_scan', 'samples_per_sweep',
                'sweep_overlap_ratio', 'window_size', 'window_type', 'fft_size',
                'rtl_bin_size', 'rtl_crop', 'rtl_fir_size',
                'smoothing_enabled', 'smoothing_factor', 'serial_number',
                'scaling_enabled', 'scaling_min_db', 'scaling_max_db']
        for key in keys:
            if key not in kwargs:
                continue
            val = kwargs.get(key)
            if key == 'serial_number' and val is None:
                val = ''
            setattr(self, key, val)

class AdvancedOptionsBase(BoxLayout):
    scan_controls = ObjectProperty(None)
    option_widgets = DictProperty()
    unbound_option_widgets = ListProperty()
    window_type = StringProperty(allownone=True)
    window_type_dropdown_trigger = ObjectProperty(None, allownone=True)
    def on_scan_controls(self, *args):
        if self.scan_controls is None:
            return
        self.window_type = self.scan_controls.window_type
        self.scan_controls.bind(window_type=self.setter('window_type'))
        for widget in self.unbound_option_widgets[:]:
            self.bind_option_widget(widget)
    def add_widget(self, widget, index=0):
        super(AdvancedOptionsBase, self).add_widget(widget, index)
        if isinstance(widget, BaseOption):
            self.bind_option_widget(widget)
    def bind_option_widget(self, widget):
        prop_name = getattr(widget, 'prop_name', None)
        if not prop_name:
            self.unbound_option_widgets.append(widget)
            widget.bind(prop_name=self.on_widget_prop_name)
        elif self.scan_controls is None:
            if widget not in self.unbound_option_widgets:
                self.unbound_option_widgets.append(widget)
        elif prop_name not in self.option_widgets:
            widget.value = getattr(self.scan_controls, prop_name)
            widget.bind(value=self.scan_controls.setter(prop_name))
            self.scan_controls.bind(**{prop_name:widget.setter('value')})
            self.option_widgets[prop_name] = widget
            if widget in self.unbound_option_widgets:
                self.unbound_option_widgets.remove(widget)
    def on_widget_prop_name(self, widget, prop_name):
        if not prop_name:
            return
        self.bind_option_widget(widget)
        widget.unbind(prop_name=self.on_widget_prop_name)
    def on_window_type_dropdown_trigger(self, instance, value):
        if not value:
            return
        self.scan_controls.window_type_dropdown.open(value)

class AdvancedOptions(AdvancedOptionsBase):
    pass

class RtlPowerAdvancedOptions(AdvancedOptionsBase):
    pass

class BaseOption(BoxLayout):
    label_text = StringProperty()
    allownone = BooleanProperty(False)
    prop_name = StringProperty()

class NumericOption(BaseOption):
    value = NumericProperty(allownone=True)
    is_float = BooleanProperty(False)

class TextOption(BaseOption):
    value = StringProperty(allownone=True)

class BoolOption(BaseOption):
    value = BooleanProperty(False)

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

class WindowTypeDropDown(DropDown):
    scan_controls = ObjectProperty(None)
    def on_scan_controls(self, *args):
        if self.scan_controls is None:
            return
        prop = self.scan_controls.property('window_type')
        for win_type in prop.options:
            btn = WindowTypeDropDownBtn(text=win_type)
            self.add_widget(btn)

class WindowTypeDropDownBtn(Button):
    pass

class ScanProgress(EventDispatcher):
    name = StringProperty()
    scan_controls = ObjectProperty(None)
    status_bar = ObjectProperty(None)
    root_widget = ObjectProperty(None)
    plot = ObjectProperty(None, allownone=True)
    current_spectrum = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(ScanProgress, self).__init__(**kwargs)
        self.cancelled = False
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
        scan_controls = self.scan_controls
        scan_range = self.scan_controls.scan_range
        graph_widget = self.root_widget.plot_container.spectrum_graph
        graph_widget.auto_scale_x = False
        graph_widget.x_min = scan_range[0]
        graph_widget.x_max = scan_range[1]
        self.name = ' - '.join([str(v) for v in scan_range])
        self.status_bar.progress = 0.
        self.status_bar.message_text = 'Scanning %s' % (self.name)
        keys = {
            'config':[
                'scan_range',
            ],
            'device':[
                'serial_number',
                'gain',
                'freq_correction',
                'is_remote',
                'remote_hostname',
                'remote_port',
            ],
            'sampling':[
                'sample_rate',
                'sweep_overlap_ratio',
                'sweeps_per_scan',
                'samples_per_sweep',
                'window_size',
                'window_type',
                'fft_size',
                'rtl_bin_size',
                'rtl_crop',
                'rtl_fir_size',
            ],
            'processing':[
                'smoothing_enabled',
                'smoothing_factor',
                'scaling_enabled',
                'scaling_min_db',
                'scaling_max_db',
            ],
        }
        scan_config = {}
        for conf_name, conf_keys in keys.items():
            for key in conf_keys:
                val = getattr(scan_controls, key)
                if key == 'window_type' and val == 'None':
                    val = None
                elif key == 'window_size' and not val:
                    val = None
                elif key == 'fft_size' and not val:
                    val = None
                elif key == 'serial_number' and not len(val):
                    val = None
                if isinstance(val, basestring):
                    val = str(val)
                if conf_name == 'config':
                    scan_config[key] = val
                else:
                    if conf_name not in scan_config:
                        scan_config[conf_name] = {}
                    scan_config[conf_name][key] = val
        if self.scan_controls.scanner_backend == 'builtin':
            cls = Scanner
        else:
            cls = RtlPowerScanner
        self.scanner = cls(config=scan_config)
        self.scanner.on_progress = self.on_scanner_progress
        self.scanner.on_sweep_processed = self.on_sweep_processed
        self.scan_thread = ScanThread(scanner=self.scanner, callback=self.on_scanner_finished)
        self.run_scan()
    def smooth_scan(self, *args):
        spectrum = self.scanner.spectrum
        N = int(spectrum.sample_data.size * self.scan_controls.smoothing_factor / 100.)
        spectrum.smooth(N)
        spectrum.interpolate()
    def scale_scan(self, *args):
        spectrum = self.scanner.spectrum
        spectrum.scale(self.scan_controls.scaling_min_db, self.scan_controls.scaling_max_db)
    def on_scanner_progress(self, value):
        Clock.schedule_once(self.update_progress)
    def on_sweep_processed(self, **kwargs):
        freqs = kwargs.get('frequencies')
        powers = kwargs.get('powers')
        fc = kwargs.get('sample_set').center_frequency / 1e6
        fc = float(fc)
        spectrum = self.current_spectrum
        new_spectrum = False
        if spectrum is None or fc != self.scan_controls.current_freq:
            spectrum = Spectrum()
            new_spectrum = True
        try:
            self.scan_controls.current_freq = fc
        except:
            print(type(fc), repr(fc))
            self.cancel_scan()
            raise
        spectrum.add_sample_set(frequency=freqs, iq=powers, center_frequency=fc)
        if new_spectrum:
            self.current_spectrum = spectrum
        elif self.scan_controls.live_view_visible:
            sg = self.scan_controls.live_spectrum_graph
            plot = sg.spectrum_plot_container.children[0]
            plot.update_data()
    def on_current_spectrum(self, *args):
        if self.current_spectrum is None:
            return
        sg = self.scan_controls.live_spectrum_graph
        sg.spectrum_plot_container.clear_widgets()
        sg.add_plot(spectrum=self.current_spectrum)
    def update_progress(self, *args, **kwargs):
        if self.scanner is None:
            return
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
        if not self.cancelled:
            if self.scan_controls.smoothing_enabled:
                self.smooth_scan()
            if self.scan_controls.scaling_enabled:
                self.scale_scan()
        Clock.schedule_once(do_update)
    def cancel_scan(self, *args, **kwargs):
        self.cancelled = True
        if self.scanner._running.is_set():
            self.scanner.stop_scan()
    def cleanup(self):
        if self.scanner is not None:
            self.scanner = None
        if self.scan_thread is not None:
            self.scan_thread = None
        self.plot = None
        self.scan_controls.scanning = False
        self.scan_controls.idle = True
    def show_scan(self):
        if self.scanner is None:
            return
        spectrum = self.scanner.spectrum
        if not len(spectrum.samples):
            return
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
