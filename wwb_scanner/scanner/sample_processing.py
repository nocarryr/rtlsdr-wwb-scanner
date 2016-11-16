import time
import threading
import numpy as np
from scipy.signal.windows import __all__ as WINDOW_TYPES
from scipy.signal import welch, get_window

from wwb_scanner.core import JSONMixin

WINDOW_TYPES = [s for s in WINDOW_TYPES if s != 'get_window']

def next_2_to_pow(val):
    val -= 1
    val |= val >> 1
    val |= val >> 2
    val |= val >> 4
    val |= val >> 8
    val |= val >> 16
    return val + 1

def calc_num_samples(num_samples):
    return next_2_to_pow(int(num_samples))

def sort_psd(f, Pxx, onesided=False):
    f_index = np.argsort(f)
    f = f[f_index]
    Pxx = Pxx[f_index]
    if onesided:
        i = np.searchsorted(f, 0)
        f = f[i:]
        Pxx = Pxx[i:]
        Pxx *= 2
    return f, Pxx

class SampleSet(JSONMixin):
    __slots__ = ('scanner', 'center_frequency', 'raw', 'current_sweep',
                 '_frequencies', 'powers', 'collection', 'process_thread',
                 'samples_per_second')
    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key == '_frequencies':
                key = 'frequencies'
            setattr(self, key, kwargs.get(key))
        if self.scanner is None and self.collection is not None:
            self.scanner = self.collection.scanner
    @property
    def frequencies(self):
        f = getattr(self, '_frequencies', None)
        if f is None:
            f = self._frequencies= self.calc_expected_freqs()
        return f
    @frequencies.setter
    def frequencies(self, value):
        self._frequencies = value
    def read_samples(self):
        scanner = self.scanner
        freq = self.center_frequency
        num_samples = scanner.samples_per_scan
        sweeps_per_scan = scanner.sample_rate / num_samples
        samples_per_second = self.samples_per_second
        if samples_per_second is None:
            samples_per_second = next_2_to_pow(int(num_samples / sweeps_per_scan))
            self.samples_per_second = samples_per_second
        win_size = scanner.window_size
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        self.raw = np.zeros((int(sweeps_per_scan), samples_per_second), 'complex')
        self.powers = np.zeros((int(sweeps_per_scan), samples_per_second), 'float64')
        sdr.read_samples_async(self.samples_callback, num_samples=samples_per_second)
    def samples_callback(self, iq, context):
        current_sweep = getattr(self, 'current_sweep', None)
        if current_sweep is None:
            current_sweep = self.current_sweep = 0
        if current_sweep >= self.raw.shape[0]:
            self.on_sample_read_complete()
            return
        try:
            self.raw[current_sweep] = iq
            self.process_sweep(current_sweep)
        except:
            self.on_sample_read_complete()
            raise
        self.current_sweep += 1
        if current_sweep > self.raw.shape[0]:
            self.on_sample_read_complete()
    def on_sample_read_complete(self):
        sdr = self.scanner.sdr
        if not sdr.read_async_canceling:
            sdr.cancel_read_async()
        self.process_samples()
    def launch_process_thread(self):
        self.process_thread = ProcessThread(self)
    def process_sweep(self, sweep):
        scanner = self.scanner
        freq = self.center_frequency
        win_size = scanner.window_size
        nfft = scanner.sampling_config.get('fft_size')
        win = get_window(scanner.sampling_config.window_type, win_size)
        f, powers = welch(self.raw[sweep], fs=scanner.sample_rate)
        f += freq
        f /= 1e6
        powers = 10. * np.log10(powers)
        self.collection.on_sweep_processed(sample_set=self,
                                           powers=powers,
                                           frequencies=f)
    def process_samples(self):
        f, powers = welch(self.raw.flatten(), fs=self.scanner.sample_rate)
        f, powers = sort_psd(f, powers)
        f += self.center_frequency
        f /= 1e6
        self.powers = powers
        if not np.array_equal(f, self.frequencies):
            print 'freq not equal: %s, %s' % (self.frequencies.size, f.size)
            self.frequencies = f
        self.collection.on_sample_set_processed(self)
    def calc_expected_freqs(self):
        freq = self.center_frequency
        win_size = self.scanner.window_size
        sr = self.scanner.sample_rate
        num_samples = self.scanner.samples_per_scan
        sweeps_per_scan = sr / num_samples
        samples_per_second = self.samples_per_second
        if samples_per_second is None:
            samples_per_second = next_2_to_pow(int(num_samples / sweeps_per_scan))
            self.samples_per_second = samples_per_second
        fake_samples = np.zeros(samples_per_second, 'complex')
        win = get_window('hanning', win_size)
        nfft = self.scanner.sampling_config.get('fft_size')
        f_expected, Pxx = welch(fake_samples, fs=sr)
        f_expected, Pxx = sort_psd(f_expected, Pxx)
        f_expected += freq
        f_expected /= 1e6
        return f_expected
    def _serialize(self):
        d = {}
        for key in self.__slots__:
            if key in ['scanner', 'collection']:
                continue
            val = getattr(self, key)
            d[key] = val
        return d


class SampleCollection(JSONMixin):
    def __init__(self, **kwargs):
        self.scanner = kwargs.get('scanner')
        self.scanning = threading.Event()
        self.stopped = threading.Event()
        self.sample_sets = {}
    def add_sample_set(self, sample_set):
        self.sample_sets[sample_set.center_frequency] = sample_set
    def build_sample_set(self, freq):
        sample_set = SampleSet(collection=self, center_frequency=freq)
        self.add_sample_set(sample_set)
        return sample_set
    def scan_freq(self, freq):
        self.build_process_pool()
        sample_set = self.sample_sets.get(freq)
        if sample_set is None:
            sample_set = self.build_sample_set(freq)
        sample_set.read_samples()
        return sample_set
    def scan_all_freqs(self):
        self.scanning.set()
        for key in sorted(self.sample_sets.keys()):
            if not self.scanning.is_set():
                break
            sample_set = self.sample_sets[key]
            sample_set.read_samples()
        self.scanning.clear()
        self.stopped.set()
    def stop(self):
        if self.scanning.is_set():
            self.scanning.clear()
            self.stopped.wait()
    def cancel(self):
        if self.scanning.is_set():
            self.scanning.clear()
            self.stopped.wait()
    def on_sweep_processed(self, **kwargs):
        self.scanner.on_sweep_processed(**kwargs)
    def on_sample_set_processed(self, sample_set):
        self.scanner.on_sample_set_processed(sample_set)
    def _serialize(self):
        return {'sample_sets':
            {k: v._serialize() for k, v in self.sample_sets.items()},
        }
    def _deserialize(self, **kwargs):
        for key, val in kwargs.get('sample_sets', {}).items():
            sample_set = SampleSet.from_json(val, collection=self)
            self.sample_sets[key] = sample_set
