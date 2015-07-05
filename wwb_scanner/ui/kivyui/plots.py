import numpy as np

from kivy.garden.graph import Graph, MeshLinePlot

class SpectrumGraph(Graph):
    def __init__(self, **kwargs):
        self.spectrum = kwargs.get('spectrum')
        self.build_data()
        kwargs.update(self.calc_plot_params())
        print kwargs
        super(SpectrumGraph, self).__init__(**kwargs)
        print 'post super'
        self.bind(parent=self.on_parent_set)
    def on_parent_set(self, *args):
        if self.parent is None:
            return
        if hasattr(self, '_plot'):
            return
        self._plot = SpectrumPlot(spectrum=self.spectrum)
        self.add_plot(self._plot)
    def build_data(self):
        spectrum = self.spectrum
        dtype = np.dtype(float)
        x = np.fromiter(spectrum.iter_frequencies(), dtype)
        y = np.fromiter((s.magnitude for s in spectrum.iter_samples()), dtype)
        self.xy_data = np.vstack((x, y))
    def calc_plot_params(self):
        xy = self.xy_data
        d = dict(
            x_label='Frequency (mHz)', 
            y_label='dBm', 
            x_min=int(xy[0].min()), 
            x_max=int(xy[0].max()) + 1, 
            y_min=int(xy[1].min()), 
            y_max=int(xy[1].max()) + 1, 
            x_ticks_minor=xy[0].size / 16, 
            x_ticks_major=xy[0].size / 64, 
            y_ticks_minor=xy[1].size / 16, 
            y_ticks_major=xy[1].size / 64, 
            x_grid_label=True, 
            y_grid_label=True, 
            x_grid=True, 
            y_grid=True, 
            padding=5, 
        )
        return d
class SpectrumPlot(MeshLinePlot):
    def __init__(self, **kwargs):
        super(SpectrumPlot, self).__init__(**kwargs)
        self.spectrum = kwargs.get('spectrum')
        self.points = self.build_points_from_spectrum()
    def build_points_from_spectrum(self):
        spectrum = self.spectrum
        return tuple(((s.frequency, s.magnitude) for s in spectrum.iter_samples()))
