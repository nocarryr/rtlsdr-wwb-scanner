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
    __slots = ('scanner', 'center_frequency', 'samples', 
               'raw', 'frequencies', 'powers')
    def __init__(self, scanner, center_frequency):
        self.scanner = scanner
        self.center_frequency = center_frequency
        self.read_samples()
    def read_samples(self):
        scanner = self.scanner
        freq = self.center_frequency
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        samples = sdr.read_samples(scanner.samples_per_scan)
        self.samples = samples
        f, powers = welch(samples, fs=scanner.sample_rate, nperseg=scanner.sample_segment_length, scaling='spectrum')
        f = np.fft.fftshift(f)
        f += freq
        self.frequencies = f
        self.raw = powers
        self.powers = 20. * np.log10(powers)
        
