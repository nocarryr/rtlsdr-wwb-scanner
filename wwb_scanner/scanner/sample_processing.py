import json
import numpy as np
from scipy.signal import welch, get_window

def next_2_to_pow(val):
    val -= 1
    val |= val >> 1
    val |= val >> 2
    val |= val >> 4
    val |= val >> 8
    val |= val >> 16
    return val + 1

def calc_num_samples(sample_rate):
    return next_2_to_pow(int(sample_rate * .25))

class SampleSet(object):
    __slots__ = ('scanner', 'center_frequency', 'samples',
                 'raw', 'frequencies', 'powers', 'collection')
    def __init__(self, **kwargs):
        for key in self.__slots__:
            setattr(self, key, kwargs.get(key))
        if self.scanner is None and self.collection is not None:
            self.scanner = self.collection.scanner
        if 'from_json' in kwargs or self.raw is None:
            self.read_samples()
    @classmethod
    def from_json(cls, scanner, data):
        if isinstance(data, basestring):
            data = json.loads(data)
        obj = cls(scanner, data['center_frequency'], from_json=True)
        np_keys = ['samples', 'frequencies', 'raw', 'powers']
        for key, val in data.items():
            if key in np_keys:
                val = np.array(val)
            setattr(obj, key, val)
        return obj
    def read_samples(self):
        scanner = self.scanner
        freq = self.center_frequency
        num_samples = next_2_to_pow(int(scanner.bandwidth))
        #num_samples = int(scanner.bandwidth)
        #scan_freqs = np.fft.fftfreq(num_samples, 1/scanner.bandwidth)
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        samples = self.samples = sdr.read_samples(num_samples)
        win = get_window('hanning', int(scanner.bandwidth / (scanner.step_size * 1e6)))
        f, powers = welch(samples, fs=scanner.sample_rate, window=win)
        f = np.fft.fftshift(f)
        f += freq
        f /= 1e6
        #f = f[4:-4]
        #powers = powers[4:-4]
        self.frequencies = f
        self.raw = powers.copy()
        self.powers = 10. * np.log10(powers)

    def _serialize(self):
        d = {}
        for key in self.__slots__:
            if key == 'scanner':
                continue
            val = getattr(self, key)
            if isinstance(val, np.ndarray):
                val = val.tolist()
            d[key] = val
        return d

class SampleCollection(object):
    def __init__(self, **kwargs):
        self.scanner = kwargs.get('scanner')
        self.sample_sets = {}
    def add_sample_set(self, sample_set):
        self.sample_sets[sample_set.center_frequency] = sample_set
    def scan_freq(self, freq):
        sample_set = SampleSet(collection=self, center_frequency=freq)
        self.add_sample_set(sample_set)
        return sample_set
