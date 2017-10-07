import time
import threading
try:
    import queue
except ImportError:
    import Queue as queue

import numpy as np
from scipy.signal.windows import __all__ as WINDOW_TYPES
from scipy.signal import welch, get_window, hilbert

from wwb_scanner.core import JSONMixin

WINDOW_TYPES = [s for s in WINDOW_TYPES if s != 'get_window']

NPERSEG = 128

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
    a = np.zeros(f.size, dtype=[('f', f.dtype), ('Pxx', Pxx.dtype)])
    a['f'] = f[:]
    a['Pxx'] = Pxx[:]
    a = np.sort(a, order='f')
    return a['f'], a['Pxx']

class SampleSet(JSONMixin):
    __slots__ = ('scanner', 'center_frequency', 'raw', 'current_sweep', 'complete', 'read_complete'
                 '_frequencies', 'powers', 'collection', 'process_thread', 'samples_discarded')
    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key == '_frequencies':
                key = 'frequencies'
            setattr(self, key, kwargs.get(key))
        self.complete = threading.Event()
        self.read_complete = threading.Event()
        self.samples_discarded = False
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
    @property
    def sweeps_per_scan(self):
        return self.scanner.sweeps_per_scan
    @property
    def samples_per_sweep(self):
        return self.scanner.samples_per_sweep
    def read_samples(self):
        scanner = self.scanner
        freq = self.center_frequency
        sweeps_per_scan = scanner.sweeps_per_scan
        samples_per_sweep = scanner.samples_per_sweep
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        self.raw = np.zeros((sweeps_per_scan, samples_per_sweep), 'complex')
        self.powers = np.zeros((sweeps_per_scan, samples_per_sweep), 'float64')
        sdr.read_samples_async(self.samples_callback, num_samples=samples_per_sweep)
    def samples_callback(self, iq, context):
        samples_per_sweep = self.scanner.samples_per_sweep
        if not self.samples_discarded:
            self.samples_discarded = True
            return
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
        self.collection.on_sample_set_read_complete(self)
        self.read_complete.set()
    def process_sweep(self, sweep):
        scanner = self.scanner
        freq = self.center_frequency
        win = get_window('triang', NPERSEG)
        f, powers = welch(self.raw[sweep], fs=scanner.sample_rate,
                          window=win, nperseg=NPERSEG, return_onesided=False)
        f += freq
        f /= 1e6
        self.collection.on_sweep_processed(sample_set=self,
                                           powers=powers,
                                           frequencies=f)
    def translate_freq(self, samples, freq, rs):
        # Adapted from https://github.com/vsergeev/luaradio/blob/master/radio/blocks/signal/frequencytranslator.lua
        if not np.iscomplexobj(samples):
            samples = hilbert(samples)
        omega = 2 * np.pi * (freq / rs)
        def iter_phase():
            p = 0
            i = 0
            while i < samples.shape[-1]:
                yield p
                p += omega
                p -= 2 * np.pi
                i += 1
        phase_rot = np.fromiter(iter_phase(), dtype=np.float)
        phase_rot = np.unwrap(phase_rot)
        xlator = np.zeros(phase_rot.size, dtype=samples.dtype)
        xlator.real = np.cos(phase_rot)
        xlator.imag = np.sin(phase_rot)
        samples *= xlator
        return samples
    def process_samples(self):
        rs = self.scanner.sample_rate
        fc = self.center_frequency

        samples = self.raw.flatten()

        overlap_ratio = self.scanner.sampling_config.sweep_overlap_ratio

        win = get_window(self.scanner.sampling_config.window_type, NPERSEG)
        freqs, Pxx = welch(samples, fs=rs, window=win,
            nperseg=NPERSEG, scaling='density', return_onesided=False)

        iPxx = np.fft.irfft(Pxx)
        iPxx = self.translate_freq(iPxx, fc, rs)
        Pxx = np.abs(np.fft.rfft(iPxx))

        freqs, Pxx = sort_psd(freqs, Pxx)
        f_ix = np.append(np.nonzero(freqs<-0.25e6), np.nonzero(freqs>0.25e6))
        freqs = freqs[f_ix]
        Pxx = Pxx[f_ix]

        freqs += fc
        freqs /= 1e6

        self.powers = Pxx
        if not np.array_equal(freqs, self.frequencies):
            print('freq not equal: %s, %s' % (self.frequencies.size, freqs.size))
            self.frequencies = freqs

        self.collection.on_sample_set_processed(self)
        self.complete.set()
    def calc_expected_freqs(self):
        freq = self.center_frequency
        scanner = self.scanner
        rs = scanner.sample_rate
        num_samples = scanner.samples_per_sweep * scanner.sweeps_per_scan
        overlap_ratio = scanner.sampling_config.sweep_overlap_ratio
        fake_samples = np.zeros(num_samples, 'complex')
        f_expected, Pxx = welch(fake_samples.real, fs=rs, nperseg=NPERSEG, return_onesided=False)

        f_expected, Pxx = sort_psd(f_expected, Pxx)

        f_ix = np.append(np.nonzero(f_expected<-0.25e6), np.nonzero(f_expected>0.25e6))
        f_expected = f_expected[f_ix]

        f_expected += freq
        f_expected /= 1e6
        return f_expected
    def _serialize(self):
        d = {}
        for key in self.__slots__:
            if key in ['scanner', 'collection', 'complete']:
                continue
            val = getattr(self, key)
            d[key] = val
        return d


class SampleCollection(JSONMixin):
    def __init__(self, **kwargs):
        self.scanner = kwargs.get('scanner')
        self.scanning = threading.Event()
        self.stopped = threading.Event()
        self._process_lock = threading.Lock()
        self._scan_queue = queue.Queue()
        self._scan_queue_lock = threading.Lock()
        self._process_queue = queue.Queue()
        self.sample_sets = {}
        self.process_thread = None
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
        t = self.process_thread = ProcessThread(self)
        t.start()
        complete_events = set()
        with self._scan_queue_lock:
            for key in sorted(self.sample_sets.keys()):
                if not self.scanning.is_set():
                    break
                sample_set = self.sample_sets[key]
                complete_events.add(sample_set.complete)
                self._scan_queue.put(sample_set)

        while self.scanning.is_set():
            r = self.scan_next_sample_set()
            if r is False:
                break

        if self.scanning.is_set():
            self._scan_queue.join()
            self._process_queue.join()

        self.process_thread.stop()
        self.process_thread = None
        self.scanning.clear()
        self.stopped.set()
    def on_sample_set_read_complete(self, sample_set):
        if self.scanning.is_set():
            with self._process_lock:
                self._process_queue.put(sample_set)
    def scan_next_sample_set(self):
        with self._scan_queue_lock:
            try:
                sample_set = self._scan_queue.get_nowait()
            except queue.Empty:
                return False
            if sample_set is None:
                self._scan_queue.task_done()
                return False
        sample_set.read_samples()
        sample_set.read_complete.wait()
        if self.scanning.is_set():
            self._scan_queue.task_done()
        return True
    def process_next_item(self):
        with self._process_lock:
            try:
                item = self._process_queue.get(timeout=.1)
            except queue.Empty:
                return True
            if item is None:
                self._process_queue.task_done()
                return False
        item.process_samples()
        if self.scanning.is_set():
            self._process_queue.task_done()
        return True
    def stop(self):
        if self.scanning.is_set():
            self.scanning.clear()
            with self._scan_queue_lock:
                while not self._scan_queue.empty():
                    try:
                        self._scan_queue.task_done()
                    except ValueError:
                        break
                self._scan_queue.put(None)
            for sample_set in self.sample_sets.items():
                sample_set.complete.set()
            self.stopped.wait()
    def cancel(self):
        if self.scanning.is_set():
            self.scanning.clear()
            with self._scan_queue_lock:
                while not self._scan_queue.empty():
                    try:
                        self._scan_queue.task_done()
                    except ValueError:
                        break
                self._scan_queue.put(None)
            for sample_set in self.sample_sets.values():
                sample_set.complete.set()
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

class ProcessThread(threading.Thread):
    def __init__(self, sample_collection):
        super(ProcessThread, self).__init__()
        self.sample_collection = sample_collection
        self._running = threading.Event()
        self._stopped = threading.Event()
    def run(self):
        self._running.set()
        while self._running.is_set():
            r = self.sample_collection.process_next_item()
            if r is False:
                break
        self._stopped.set()
    def stop(self):
        self._running.clear()
        with self.sample_collection._process_lock:
            while not self.sample_collection._process_queue.empty():
                self.sample_collection._process_queue.task_done()
            self.sample_collection._process_queue.put(None)
        self._stopped.wait()
