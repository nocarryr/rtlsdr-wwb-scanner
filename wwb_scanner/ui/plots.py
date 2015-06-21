import numpy as np
import matplotlib.pyplot as plt

class BasePlot(object):
    def __init__(self, **kwargs):
        self.spectrum = kwargs.get('spectrum')
    def build_data(self):
        dtype = np.dtype(float)
        self.x = np.fromiter(self.spectrum.iter_frequencies(), dtype)
        self.y = np.fromiter((s.magnitude for s in self.spectrum.iter_samples()), dtype)
    def build_plot(self):
        pass
    
class Spectrum(BasePlot):
    def build_plot(self):
        plt.figure()
        plt.plot(self.x, self.y)
        plt.xlabel('frequency (MHz)')
        plt.ylabel('dBm')
        plt.show()
