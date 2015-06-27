import json
import numpy as np
from scipy.signal import welch, find_peaks_cwt

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
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        samples = self.samples = sdr.read_samples(scanner.samples_per_scan)
        f, powers = welch(samples, fs=scanner.sample_rate, nperseg=scanner.sample_segment_length)#, scaling='spectrum')
        f = np.fft.fftshift(f)
        f += freq
        f /= 1e6
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
        self.frequencies = None
        self.raw = None
    def add_sample_set(self, sample_set):
        self.sample_sets[sample_set.center_frequency] = sample_set
        self.combine_samples(sample_set)
    def scan_freq(self, freq):
        sample_set = SampleSet(collection=self, center_frequency=freq)
        self.add_sample_set(sample_set)
        return sample_set
    def iter_frequencies(self):
        return sorted(self.sample_sets.keys())
    def iter_sample_sets(self):
        sample_sets = self.sample_sets
        for key in self.iter_frequencies():
            yield sample_sets[key]
    def combine_samples(self, sample_set):
        if self.frequencies is None:
            self.frequencies = sample_set.frequencies.copy()
            self.raw = sample_set.raw.copy()
            return
        f = self.frequencies
        r = self.raw
        indecies = np.searchsorted(f, sample_set.frequencies)
        for i, insert_i in enumerate(indecies):
            f = np.insert(f, insert_i, sample_set.frequencies[i])
            r = np.insert(r, insert_i, sample_set.raw[i])
        self.frequencies = f
        self.raw = r
    def convert_powers(self):
        self.powers = 10. * np.log10(self.raw)
    def smooth_peaks(self):
        f = self.frequencies
        p = self.powers
        width = np.arange(1, int(len(self.sample_sets.values()[0].raw) / 4.))
        peakind = find_peaks_cwt(p, width)
        f = np.delete(f, peakind)
        p = np.delete(p, peakind)
        self.frequencies = f
        self.powers = p
    def finalize(self):
        #self.combine_samples()
        self.convert_powers()
        #self.smooth_peaks()
