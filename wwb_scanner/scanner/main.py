import threading

import numpy as np

from wwb_scanner.core import JSONMixin
from wwb_scanner.scanner.sdrwrapper import SdrWrapper
from wwb_scanner.scanner.sample_processing import (
    SampleCollection, 
    calc_num_samples, 
    WINDOW_TYPES, 
)
from wwb_scanner.scan_objects import Spectrum

SCANNER_DEFAULTS = dict(
    scan_range=[400., 900.],
    step_size=.05,
    sample_rate=2e6,
    sampling_period=.0125,
    save_raw_values=False,
    gain=30.,
    freq_correction=0, 
)

def mhz_to_hz(mhz):
    return mhz * 1000000.0
def hz_to_mhz(hz):
    return hz / 1000000.0

class StopScanner(Exception):
    pass

class ScannerBase(JSONMixin):
    WINDOW_TYPES = WINDOW_TYPES
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
        self._samples_per_scan = None
        self._window_size = None
        super(Scanner, self).__init__(**kwargs)
        self.samples_per_scan = kwargs.get('samples_per_scan')
        self.window_size = kwargs.get('window_size')
        self.window_type = kwargs.get('window_type', 'boxcar')
        self.fft_size = kwargs.get('fft_size')
        self.sdr_wrapper = SdrWrapper(scanner=self)
        self.bandwidth = self.sample_rate / 2.
        self.gain = self.gain
    @property
    def sdr(self):
        return self.sdr_wrapper.sdr
    @property
    def samples_per_scan(self):
        v = self._samples_per_scan
        if v is None:
            v = self.sample_rate * self.sampling_period
            v = self._samples_per_scan = calc_num_samples(v)
        return v
    @samples_per_scan.setter
    def samples_per_scan(self, value):
        if value == self._samples_per_scan:
            return
        if value is not None:
            value = calc_num_samples(value)
        self._samples_per_scan = value
    @property
    def window_size(self):
        v = self._window_size
        if v is None:
            v = self._window_size = int(self.bandwidth / mhz_to_hz(self.step_size))
        return v
    @window_size.setter
    def window_size(self, value):
        if value == self._window_size:
            return
        self._window_size = value
    @property
    def gain(self):
        return getattr(self, '_gain', None)
    @gain.setter
    def gain(self, value):
        if value is not None and hasattr(self, 'sdr_wrapper'):
            value = self.get_nearest_gain(value)
        self._gain = value
    @property
    def gains(self):
        gains = getattr(self, '_gains', None)
        if gains is None:
            gains = self._gains = self.get_gains()
        return gains
    def get_gains(self):
        self.sdr_wrapper.enable_scanner_updates = False
        with self.sdr_wrapper:
            sdr = self.sdr
            if sdr is None:
                gains = None
            else:
                gains = self.sdr.get_gains()
        self.sdr_wrapper.enable_scanner_updates = True
        if gains is not None:
            gains = [gain / 10. for gain in gains]
        return gains
    def get_nearest_gain(self, gain):
        gains = self.gains
        if gains is None:
            return gain
        npgains = np.array(gains)
        return gains[np.abs(npgains - gain).argmin()]
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
    def _serialize(self):
        d = super(Scanner, self)._serialize()
        keys = ['samples_per_scan', 'window_size', 'window_type', 'fft_size']
        d.update({key: getattr(self, key) for key in keys})
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
    scanner = Scanner(**kwargs)
    scanner.run_scan()
    scanner.spectrum.show_plot()
    return scanner

def scan_and_save(filename=None, frequency_format=None, **kwargs):
    scanner = Scanner(**kwargs)
    scanner.run_scan()
    scanner.spectrum.export_to_file(filename=filename, frequency_format=frequency_format)
    return scanner
