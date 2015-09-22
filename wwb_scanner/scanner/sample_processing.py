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
        #time.sleep(.1)
        #sdr.read_samples(2048)
        #print 'reading %s samples' % (num_samples)
        self.raw = np.zeros((int(sweeps_per_scan), samples_per_second), 'complex')
        self.powers = np.zeros((int(sweeps_per_scan), samples_per_second), 'float64')
        #print 'raw: %s, powers: %s, samples_per_second: %s' % (self.raw.shape, self.powers.shape, samples_per_second)
        sdr.read_samples_async(self.samples_callback, num_samples=samples_per_second)
    def samples_callback(self, iq, context):
        current_sweep = getattr(self, 'current_sweep', None)
        if current_sweep is None:
            current_sweep = self.current_sweep = 0
        if current_sweep >= self.raw.shape[0]:
            self.on_sample_read_complete()
            return
        try:
            self.raw[current_sweep] = iq#[:self.samples_per_second]
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
        if self.powers.shape[1] != powers.size:
            self.powers.resize((self.powers.shape[0], powers.size))
        if not np.array_equal(f, self.frequencies):
            print 'freq not equal: %s, %s' % (self.frequencies.size, f.size)
            self.frequencies = f
        self.powers[sweep] = powers
        self.collection.on_sweep_processed(sample_set=self, 
                                           powers=powers, 
                                           frequencies=f)
    def process_samples(self):
        f, powers = welch(self.raw.flatten(), fs=self.scanner.sample_rate)
        f += self.center_frequency
        f /= 1e6
        powers = 10. * np.log10(powers)
        self.powers = powers
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
        f_expected, Pxx = welch(fake_samples, fs=sr)#, window=win, nfft=nfft)
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
        self.scanning = threading.Event()
        self.stopped = threading.Event()
        self.sample_sets = {}
        self.process_pool = None
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
    def build_process_pool(self):
        return
        if self.process_pool is not None:
            return
        self.process_pool = ProcessPool()
        self.process_pool.start()
        self.process_pool.running.wait()
    def scan_all_freqs(self):
        self.build_process_pool()
        self.scanning.set()
        for key in sorted(self.sample_sets.keys()):
            if not self.scanning.is_set():
                break
            sample_set = self.sample_sets[key]
            sample_set.read_samples()
        self.scanning.clear()
        self.stop_process_pool()
        self.stopped.set()
    def stop_process_pool(self, cancel=False):
        if self.process_pool is None:
            return
        if cancel:
            self.process_pool.cancel()
        else:
            self.process_pool.stop()
        self.process_pool = None
    def stop(self):
        if self.scanning.is_set():
            self.scanning.clear()
            self.stopped.wait()
        self.stop_process_pool()
    def cancel(self):
        if self.scanning.is_set():
            self.scanning.clear()
            self.stopped.wait()
        self.stop_process_pool(cancel=True)
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
