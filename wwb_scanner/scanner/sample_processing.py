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
    return next_2_to_pow(int(sample_rate * .5))
    
def read_samples(scanner, freq):
    sdr = scanner.sdr
    sdr.set_center_freq(freq)
    samples = sdr.read_samples(scanner.samples_per_scan)
    f, powers = welch(samples, fs=scanner.sample_rate, nperseg=scanner.sample_segment_length, scaling='spectrum')
    f = np.fft.fftshift(f)
    f += freq
    powers = 20. * np.log10(powers)
    return f, powers
