import threading

from wwb_scanner.core import JSONMixin
from wwb_scanner.scanner.sdrwrapper import SdrWrapper
from wwb_scanner.scanner.sample_processing import SampleCollection
from wwb_scanner.scan_objects import Spectrum

SCANNER_DEFAULTS = dict(
    scan_range=[400., 900.],
    step_size=.0125,
    sample_rate=2e6,
    sampling_period=.05,
    save_raw_values=False,
    gain=30.,
)

def mhz_to_hz(mhz):
    return mhz * 1000000.0
def hz_to_mhz(hz):
    return hz / 1000000.0

class StopScanner(Exception):
    pass

class ScannerBase(JSONMixin):
    def __init__(self, **kwargs):
        self._running = threading.Event()
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
        if not kwargs.get('__from_json__'):
            self.sample_collection = SampleCollection(scanner=self)
    @property
    def current_freq(self):
        return self._current_freq
    @current_freq.setter
    def current_freq(self, value):
        self._current_freq = value
        if value is not None:
            f_min, f_max = self.scan_range
            self.progress = (value - f_min) / (f_max - f_min)
        self.on_current_freq(value)
    def on_current_freq(self, value):
        print 'scanning %s' % (value)
    @property
    def progress(self):
        return self._progress
    @progress.setter
    def progress(self, value):
        if value == self._progress:
            return
        self._progress = value
        self.on_progress(value)
    def on_progress(self, value):
        print '%s%%' % (int(value * 100))
    def calc_next_center_freq(self, sample_set):
        f = sample_set.frequencies
        fmax = f.max()
        fsize = fmax - f.min()
        return (fmax + (fsize / 2.)) + (f[1] - f[2])
    def run_scan(self):
        freq, end_freq = self.scan_range
        running = self._running
        running.set()
        while freq < end_freq and running.is_set():
            self.current_freq = freq
            sample_set = self.scan_freq(mhz_to_hz(freq))
            if sample_set is False:
                break
            freq = self.calc_next_center_freq(sample_set)
    def stop_scan(self):
        self._running.clear()
    def scan_freq(self, freq):
        pass
    def _serialize(self):
        d = {k: getattr(self, k) for k in SCANNER_DEFAULTS.keys()}
        d['spectrum'] = self.spectrum._serialize()
        d['sample_collection'] = self.sample_collection._serialize()
        return d
    def _deserialize(self, **kwargs):
        data = kwargs.get('sample_collection')
        self.sample_collection = SampleCollection.from_json(data, scanner=self)

class Scanner(ScannerBase):
    '''
        params:
            scan_range: (list) frequency range to scan (in MHz)
            step_size:  increment (in MHz) to return scan values
    '''
    def __init__(self, **kwargs):
        super(Scanner, self).__init__(**kwargs)
        self.sdr_wrapper = SdrWrapper(scanner=self)
        self.bandwidth = self.sample_rate / 2.
    @property
    def sdr(self):
        return self.sdr_wrapper.sdr
    def get_gains(self):
        reset_timeout = False
        if not self.sdr_wrapper.device_open.is_set():
            timeout = self.sdr_wrapper.timeout
            if timeout is not None:
                self.sdr_wrapper.timeout = None
                reset_timeout = True
        try:
            with self.sdr_wrapper:
                gains = self.sdr.get_gains()
        except IOError:
            gains = None
        if reset_timeout:
            self.sdr_wrapper.timeout = timeout
        if gains is not None:
            gains = [gain / 10. for gain in gains]
        return gains
    def run_scan(self):
        with self.sdr_wrapper:
            super(Scanner, self).run_scan()
    def scan_freq(self, freq):
        sample_set = self.sample_collection.scan_freq(freq)
        spectrum = self.spectrum
        freqs = sample_set.frequencies
        powers = sample_set.powers
        center_freq = freqs[freqs.size / 2]
        print 'adding %s samples: range=%s - %s' % (len(freqs), min(freqs), max(freqs))
        for f, p in zip(freqs, powers):
            is_center = f == center_freq
            spectrum.add_sample(frequency=f, magnitude=p, force_magnitude=True,
                                is_center_frequency=is_center)
        return sample_set

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
    scanner = Scanner(**kwargs)
    scanner.run_scan()
    scanner.spectrum.show_plot()
    return scanner

def scan_and_save(filename=None, frequency_format=None, **kwargs):
    scanner = Scanner(**kwargs)
    scanner.run_scan()
    scanner.spectrum.export_to_file(filename=filename, frequency_format=frequency_format)
    return scanner
