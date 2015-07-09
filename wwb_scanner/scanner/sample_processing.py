import numpy as np
from scipy.signal import welch, get_window

from wwb_scanner.core import JSONMixin

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

class SampleSet(JSONMixin):
    __slots__ = ('scanner', 'center_frequency', 'samples',
                 'raw', 'frequencies', 'powers', 'collection')
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
        num_samples = next_2_to_pow(int(scanner.sample_rate * scanner.sampling_period))
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        samples = self.samples = sdr.read_samples(num_samples)
        win = get_window('hanning', int(scanner.bandwidth / (scanner.step_size * 1e6)))
        f, powers = welch(samples, fs=scanner.sample_rate, window=win)
        f = np.fft.fftshift(f)
        f += freq
        f /= 1e6
        self.frequencies = f
        self.raw = powers.copy()
        self.powers = 10. * np.log10(powers)
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
        self.sample_sets = {}
    def add_sample_set(self, sample_set):
        self.sample_sets[sample_set.center_frequency] = sample_set
    def scan_freq(self, freq):
        sample_set = SampleSet(collection=self, center_frequency=freq)
        self.add_sample_set(sample_set)
        return sample_set
    def _serialize(self):
        return {'sample_sets':
            {k: v._serialize() for k, v in self.sample_sets.items()}, 
        }
    def _deserialize(self, **kwargs):
        for key, val in kwargs.get('sample_sets', {}).items():
            sample_set = SampleSet.from_json(val, collection=self)
            self.sample_sets[key] = sample_set
