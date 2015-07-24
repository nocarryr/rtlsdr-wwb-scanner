import threading

from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, NumericProperty, StringProperty
from kivy.clock import Clock
from wwb_scanner.scanner import Scanner


class ScanProgress(BoxLayout):
    name = StringProperty()
    scan_controls = ObjectProperty(None)
    progress_bar = ObjectProperty(None)
    cancel_btn = ObjectProperty(None)
    root_widget = ObjectProperty(None)
    progress = NumericProperty(0.)
    def __init__(self, **kwargs):
        super(ScanProgress, self).__init__(**kwargs)
        scan_range = self.scan_controls.scan_range_widget.scan_range
        gain = self.scan_controls.gain_txt.text
        if not gain:
            gain = None
        else:
            gain = float(gain)
        self.name = ' - '.join([str(v) for v in scan_range])
        print scan_range, gain
        self.scanner = Scanner(scan_range=scan_range, gain=gain)
        self.scanner.on_progress = self.on_scanner_progress
        self.scan_thread = ScanThread(scanner=self.scanner, callback=self.on_scanner_finished)
    def on_scanner_progress(self, value):
        Clock.schedule_once(self.update_progress)
    def update_progress(self, *args, **kwargs):
        self.progress = float(self.scanner.progress)
    def run_scan(self):
        Clock.schedule_once(self._run_scan)
    def _run_scan(self, *args, **kwargs):
        self.scan_thread.start()
    def on_scanner_finished(self):
        def do_update(*args, **kwargs):
            self.show_scan()
            self.root_widget.close_popup()
        Clock.schedule_once(do_update)
    def cancel_scan(self, *args, **kwargs):
        if self.scanner._running.is_set():
            self.scanner.stop_scan()
        else:
            self.root_widget.close_popup()
    def show_scan(self):
        spectrum = self.scanner.spectrum
        self.root_widget.plot_container.add_plot(spectrum=spectrum, name=self.name)
    
class ScanThread(threading.Thread):
    def __init__(self, **kwargs):
        super(ScanThread, self).__init__()
        self.scanner = kwargs.get('scanner')
        self.callback = kwargs.get('callback')
    def run(self):
        self.scanner.run_scan()
        self.callback()
        
