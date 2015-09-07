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

class SampleSet(JSONMixin):
    __slots__ = ('scanner', 'center_frequency', 'raw', 
                 'frequencies', 'powers', 'collection', 'process_thread')
    def __init__(self, **kwargs):
        for key in self.__slots__:
            setattr(self, key, kwargs.get(key))
        if self.scanner is None and self.collection is not None:
            self.scanner = self.collection.scanner
        if not kwargs.get('__from_json__'):
            self.read_samples()
    def read_samples(self):
        scanner = self.scanner
        freq = self.center_frequency
        num_samples = scanner.samples_per_scan
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        time.sleep(.1)
        #print 'reading %s samples' % (num_samples)
        self.raw = sdr.read_samples(num_samples)
        f_expected = self.calc_expected_freqs()
        self.frequencies = f_expected
        self.launch_process_thread()
    def launch_process_thread(self):
        self.process_thread = ProcessThread(self)
    def process_samples(self):
        samples = self.raw.copy()
        scanner = self.scanner
        freq = self.center_frequency
        num_samples = scanner.samples_per_scan
        sweeps_per_scan = scanner.sample_rate / num_samples
        samples_per_second = int(num_samples / sweeps_per_scan)
        win_size = scanner.window_size
        nfft = scanner.sampling_config.get('fft_size')
        total_size = samples.size
        if total_size % samples_per_second != 0:
            total_size -= samples.size % samples_per_second
            #print 'sweeps_per_scan=%s, samples_per_second=%s, total_size=%s, tsize/spersec=%s' % (
            #    sweeps_per_scan, samples_per_second, total_size, total_size/samples_per_second)
            samples.resize(total_size)
        samples.resize(total_size / samples_per_second, samples_per_second)
        win = get_window(scanner.sampling_config.window_type, win_size)
        f = None
        powers = None
        for i, sample_chunk in enumerate(samples):
            _f, _powers = welch(sample_chunk, fs=scanner.sample_rate, window=win, nfft=nfft)
            if f is None:
                f = _f
            if powers is None:
                powers = np.zeros((samples.shape[0], _powers.size), dtype=_powers.dtype)
            powers[i] = _powers
        powers = np.array(powers)
        powers = powers.mean(axis=-1)
        f = np.fft.fftshift(f)
        if f.size % 2 == 0:
            f = f[1:]
            powers = powers[1:]
        f += freq
        f /= 1e6
        self.frequencies = f
        self.powers = 10. * np.log10(powers)
        self.collection.on_sample_set_processed(self)
    def calc_expected_freqs(self):
        freq = self.center_frequency
        win_size = self.scanner.window_size
        sr = self.scanner.sample_rate
        f_expected = np.fft.fftfreq(win_size, 1 / sr)
        f_expected = np.fft.fftshift(f_expected)
        if f_expected.size % 2 == 0:
            f_expected = f_expected[1:]
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
        
class ProcessPool(threading.Thread):
    MAX_ACTIVE_THREADS = 4
    def __init__(self):
        super(ProcessPool, self).__init__()
        self.threads_waiting = {}
        self.threads_active = {}
        self.thread_indecies = set()
        self.lock = threading.Lock()
        self.running = threading.Event()
        self.stopped = threading.Event()
        self.cancelling = threading.Event()
        self.all_threads_complete = threading.Event()
        self.thread_launch_wait = threading.Event()
    def run(self):
        self.running.set()
        while True:
            self.thread_launch_wait.wait()
            if self.cancelling.is_set():
                break
            self.check_thread_launch()
            if self.all_threads_complete.is_set():
                break
        self.all_threads_complete.wait()
        self.stopped.set()
    def stop(self):
        self.running.clear()
        self.thread_launch_wait.set()
        self.stopped.wait()
    def cancel(self):
        self.cancelling.set()
        self.stop()
    def add_thread(self, t):
        if not self.running.is_set():
            return
        with self.lock:
            if not len(self.thread_indecies):
                i = 0
            else:
                i = max(self.thread_indecies) + 1
            t.index = i
            self.threads_waiting[i] = t
            self.thread_indecies.add(i)
        self.check_thread_launch()
    def check_thread_launch(self):
        if self.cancelling.is_set():
            return
        threads_waiting = self.threads_waiting
        threads_active = self.threads_active
        max_threads = self.MAX_ACTIVE_THREADS
        with self.lock:
            if threading.current_thread().ident != self.ident:
                self.thread_launch_wait.set()
            else:
                self.thread_launch_wait.clear()
                if not len(threads_waiting):
                    return
                if len(threads_active) >= max_threads:
                    return
                while len(threads_waiting) and len(threads_active) < max_threads:
                    i = min(threads_waiting.keys())
                    t = threads_waiting[i]
                    threads_active[i] = t
                    del threads_waiting[i]
                    t.start()
                    t.running.wait()
    def on_thread_complete(self, t):
        with self.lock:
            del self.threads_active[t.index]
            self.thread_indecies.discard(t.index)
            if not self.running.is_set():
                if not len(self.threads_active):
                    if self.cancelling.is_set():
                        self.all_threads_complete.set()
                    elif not len(self.threads_waiting):
                        self.all_threads_complete.set()
                        self.thread_launch_wait.set()
        self.check_thread_launch()

class ProcessThread(threading.Thread):
    def __init__(self, sample_set):
        super(ProcessThread, self).__init__()
        self.sample_set = sample_set
        self.running = threading.Event()
        self.complete = threading.Event()
        self.index = None
        sample_set.collection.process_pool.add_thread(self)
    def run(self):
        self.running.set()
        self.sample_set.process_samples()
        self.running.clear()
        self.complete.set()
        self.sample_set.collection.process_pool.on_thread_complete(self)
    def __repr__(self):
        return 'ProcessThread (%s) at %s' % (self, self.ident)
    def __str__(self):
        return '%s - %s' % (self.index, self.sample_set.center_frequency)

class SampleCollection(JSONMixin):
    def __init__(self, **kwargs):
        self.scanner = kwargs.get('scanner')
        self.sample_sets = {}
        self.process_pool = None
    def add_sample_set(self, sample_set):
        self.sample_sets[sample_set.center_frequency] = sample_set
    def scan_freq(self, freq):
        if self.process_pool is None:
            self.process_pool = ProcessPool()
            self.process_pool.start()
            self.process_pool.running.wait()
        sample_set = SampleSet(collection=self, center_frequency=freq)
        self.add_sample_set(sample_set)
        return sample_set
    def stop(self):
        if self.process_pool is not None:
            self.process_pool.stop()
    def cancel(self):
        if self.process_pool is not None:
            self.process_pool.cancel()
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
