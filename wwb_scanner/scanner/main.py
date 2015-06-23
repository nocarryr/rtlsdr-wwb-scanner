import threading
import json

from rtlsdr import RtlSdr

from wwb_scanner.scanner import sample_processing
from wwb_scanner.scan_objects import Spectrum
from wwb_scanner.ui import plots
from wwb_scanner.file_handlers import CSVExporter

SCANNER_DEFAULTS = dict(
    scan_range=[400., 900.], 
    step_size=.025, 
    sample_rate=2e6,  
    save_raw_values=False
)

def mhz_to_hz(mhz):
    return mhz * 1000000.0
def hz_to_mhz(hz):
    return hz / 1000000.0
    
class StopScanner(Exception):
    pass
    
class Scanner(object):
    '''
        params:
            scan_range: (list) frequency range to scan (in MHz)
            step_size:  increment (in MHz) to return scan values
    '''
    def __init__(self, **kwargs):
        self._current_freq = None
        self._progress = 0.
        for key, val in SCANNER_DEFAULTS.items():
            if key in kwargs:
                val = kwargs.get(key)
            setattr(self, key, val)
        if 'spectrum' in kwargs:
            self.spectrum = Spectrum.from_json(kwargs['spectrum'])
        else:
            self.spectrum = Spectrum(step_size=self.step_size)
        self.sdr = RtlSdr()
        self.sdr.sample_rate = self.sample_rate
        samples_per_scan = kwargs.get('samples_per_scan')
        if samples_per_scan is None:
            samples_per_scan = sample_processing.calc_num_samples(self.sample_rate)
        sample_segment_length = kwargs.get('sample_segment_length')
        if sample_segment_length is None:
            sample_segment_length = int(self.sample_rate / mhz_to_hz(self.step_size))
        self.samples_per_scan = samples_per_scan
        self.sample_segment_length = sample_segment_length
        if self.save_raw_values:
            self.raw_values = {}
            if 'raw_values' in kwargs:
                for key, val in kwargs['raw_values'].items():
                    self.raw_values[key] = sample_processing.SampleSet.from_json(self, val)
    @classmethod
    def from_json(cls, data):
        if isinstance(data, basestring):
            data = json.loads(data)
        return cls(**data)
    def to_json(self, **kwargs):
        d = self._serialize()
        return json.dumps(d, **kwargs)
    @property
    def current_freq(self):
        return self._current_freq
    @current_freq.setter
    def current_freq(self, value):
        self._current_freq = value
        self.on_current_freq(value)
    def on_current_freq(self, value):
        print 'scanning %s' % (value)
    @property
    def progress(self):
        return self._progress
    @progress.setter
    def progress(self, value):
        value = round(value, 1)
        if value == self._progress:
            return
        self._progress = value
        self.on_progress(value)
    def on_progress(self, value):
        print '%s%%' % (int(value * 100))
    def calc_next_center_freq(self, sample_set):
        f = sample_set.frequencies
        return f.max() + (f.max() - f.min())
    def run_scan(self):
        freq, end_freq = self.scan_range
        step_size = self.step_size
        num_steps = (end_freq - freq) / step_size
        print 'num_steps=%s' % (num_steps)
        step = 0
        while freq < end_freq:
            self.current_freq = freq
            sample_set = self.scan_freq(mhz_to_hz(freq))
            if sample_set is False:
                break
            freq = self.calc_next_center_freq(sample_set)
            step += 1
            self.progress = step / num_steps
    def scan_freq(self, freq):
        spectrum = self.spectrum
        sample_set = sample_processing.SampleSet(self, freq)
        if self.save_raw_values:
            self.raw_values[freq] = sample_set
        freqs = sample_set.frequencies
        powers = sample_set.powers
        print 'adding %s samples to spectrum: range=%s - %s' % (len(freqs), min(freqs), max(freqs))
        for f, p in zip(freqs, powers):
            spectrum.add_sample(frequency=f, magnitude=p)
        return sample_set
    def _serialize(self):
        keys = ['samples_per_scan', 'sample_segment_length']
        keys.extend(SCANNER_DEFAULTS.keys())
        d = {k: getattr(self, k) for k in keys}
        if self.save_raw_values:
            raw_values = self.raw_values
            d['raw_values'] = {k: raw_values[k]._serialize() for k in raw_values.keys()}
        d['spectrum'] = self.spectrum._serialize()
        return d
        
        
        
class ThreadedScanner(threading.Thread, Scanner):
    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        Scanner.__init__(self, **kwargs)
        self.plot = kwargs.get('plot')
        self.run_once = kwargs.get('run_once', True)
        self.scan_wait_timeout = kwargs.get('scan_wait_timeout', 5.)
        self.scanning = threading.Event()
        self.waiting = threading.Event()
        self.stopping = threading.Event()
        self.stopped = threading.Event()
        self.need_update = threading.Event()
        self.need_update_lock = threading.Lock()
    def on_current_freq(self, value):
        if self.plot is not None:
            self.plot.update_plot()
        with self.need_update_lock:
            self.need_update.set()
    def run(self):
        scanning = self.scanning
        waiting = self.waiting
        stopping = self.stopping
        stopped = self.stopped
        scan_wait_timeout = self.scan_wait_timeout
        run_once = self.run_once
        run_scan = self.run_scan
        while True:
            if stopping.is_set():
                break
            scanning.set()
            run_scan()
            scanning.clear()
            if run_once:
                break
            waiting.wait(scan_wait_timeout)
        stopped.set()
    def scan_freq(self, freq):
        if self.stopping.is_set():
            return False
        return super(ThreadedScanner, self).scan_freq(freq)
    def stop(self):
        self.stopping.set()
        self.waiting.set()
        self.stopped.wait()
        
def scan_and_plot(**kwargs):
    scanner = ThreadedScanner(**kwargs)
    plot = plots.Spectrum(spectrum=scanner.spectrum)
    scanner.plot = plot
    scanner.start()
    scanner.spectrum.data_updated.wait()
    plot.build_plot()
    scanner.stop()
    return scanner
    
def scan_and_save(filename=None, frequency_format=None, **kwargs):
    scanner = Scanner(**kwargs)
    if filename is None:
        filename = 'scan_%07.3f-%07.3f.csv' % (scanner.scan_range[0], scanner.scan_range[1])
    scanner.run_scan()
    fh = CSVExporter(filename=filename, frequency_format=frequency_format, spectrum=scanner.spectrum)
    fh.write_file()
    return scanner
