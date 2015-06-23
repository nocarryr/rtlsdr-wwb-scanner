import json
import numpy as np
from scipy.signal import welch

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
                 'raw', 'frequencies', 'powers')
    def __init__(self, scanner, center_frequency, **kwargs):
        self.scanner = scanner
        self.center_frequency = center_frequency
        if not kwargs.get('from_json'):
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
        samples = sdr.read_samples(scanner.samples_per_scan)
        self.samples = np.absolute(samples)
        f, powers = welch(samples, fs=scanner.sample_rate, nperseg=scanner.sample_segment_length, scaling='spectrum')
        f = np.fft.fftshift(f)
        f += freq
        f /= 1e6
        self.frequencies = f
        self.raw = powers
        self.powers = 20. * np.log10(powers)
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
        
