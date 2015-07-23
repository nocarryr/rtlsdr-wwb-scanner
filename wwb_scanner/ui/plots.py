import numpy as np
import matplotlib.pyplot as plt

from wwb_scanner.scan_objects.spectrum import compare_spectra
from wwb_scanner.file_handlers import BaseImporter

class BasePlot(object):
    def __init__(self, **kwargs):
        self.filename = kwargs.get('filename')
        if self.filename is not None:
            self.spectrum = BaseImporter.import_file(self.filename)
        else:
            self.spectrum = kwargs.get('spectrum')
        
        #self.figure.canvas.mpl_connect('idle_event', self.on_idle)
        
    @property
    def x(self):
        return getattr(self, '_x', None)
    @x.setter
    def x(self, value):
        self._x = value
    @property
    def y(self):
        return getattr(self, '_y', None)
    @y.setter
    def y(self, value):
        self._y = value
    @property
    def figure(self):
        return getattr(self, '_figure', None)
    @figure.setter
    def figure(self, figure):
        self._figure = figure
        #self.timer = figure.canvas.new_timer(interval=100)
        #self.timer.add_callback(self.on_timer)
    def on_timer(self):
        print 'timer'
        spectrum = self.spectrum
        with spectrum.data_update_lock:
            if spectrum.data_updated.is_set():
                print 'update plot'
                self.update_plot()
                spectrum.data_updated.clear()
    def build_data(self):
        dtype = np.dtype(float)
        if not len(self.spectrum.samples):
            x = self.x = np.array(0.)
            y = self.y = np.array(0.)
        else:
            x = self.x = np.fromiter(self.spectrum.iter_frequencies(), dtype)
            y = self.y = np.fromiter((s.magnitude for s in self.spectrum.iter_samples()), dtype)
            if not hasattr(self, 'plot'):
                self.spectrum.data_updated.clear()
        return x, y
    def update_plot(self):
        if not hasattr(self, 'plot'):
            return
        x, y = self.build_data()
        self.plot.set_xdata(x)
        self.plot.set_ydata(y)
        #self.figure.canvas.draw_event(self.figure.canvas)
        self.figure.canvas.draw_idle()
    def build_plot(self):
        pass
    
class SpectrumPlot(BasePlot):
    def build_plot(self):
        self.figure = plt.figure()
        self.plot = plt.plot(*self.build_data())[0]
        plt.xlabel('frequency (MHz)')
        plt.ylabel('dBm')
        center_frequencies = self.spectrum.center_frequencies
        if len(center_frequencies):
            samples = [self.spectrum.samples.get(f) for f in center_frequencies]
            ymin = self.y.min()
            plt.vlines(center_frequencies, 
                       [ymin] * len(center_frequencies), 
                       [s.magnitude-5 if s.magnitude-5 > ymin else s.magnitude for s in samples])
        plt.show()
    
class DiffSpectrum(object):
    def __init__(self, **kwargs):
        self.spectra = []
        self.figure, self.axes = plt.subplots(3, 1, sharex='col')
    def add_spectrum(self, spectrum=None, **kwargs):
        name = kwargs.get('name')
        if name is None:
            name = str(len(self.spectra))
        if spectrum is None:
            spectrum = BaseImporter.import_file(kwargs.get('filename'))
        self.spectra.append({'name':name, 'spectrum':spectrum})
    def build_plots(self):
        dtype = np.dtype(float)
        if len(self.spectra) == 2:
            diff_spec = compare_spectra(self.spectra[0]['spectrum'], 
                                        self.spectra[1]['spectrum'])
            self.spectra.append({'name':'diff', 'spectrum':diff_spec})
        for i, spec_data in enumerate(self.spectra):
            spectrum = spec_data['spectrum']
            x = np.fromiter(spectrum.iter_frequencies(), dtype)
            y = np.fromiter((s.magnitude for s in spectrum.iter_samples()), dtype)
            axes = self.axes[i]
            axes.plot(x, y)
            axes.set_title(spec_data['name'])
        plt.show()
    
