import threading

from kivy.event import EventDispatcher
from kivy.properties import ObjectProperty, StringProperty
from kivy.clock import Clock
from wwb_scanner.scanner import Scanner


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
        self.scanner = Scanner(scan_range=scan_range, gain=gain)
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
        
