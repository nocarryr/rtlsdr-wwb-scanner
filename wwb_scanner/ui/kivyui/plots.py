import numpy as np

#from kivy.garden.graph import Graph, MeshLinePlot
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    ListProperty, 
    DictProperty, 
    NumericProperty, 
    AliasProperty, 
    BooleanProperty, 
    StringProperty, 
    ObjectProperty, 
)

class SpectrumGraph(RelativeLayout):
    plot_params = DictProperty()
    x_min = NumericProperty(0.)
    x_max = NumericProperty(1.)
    def get_x_size(self):
        return self.x_max - self.x_min
    def set_x_size(self, value):
        pass
    x_size = AliasProperty(get_x_size, set_x_size, bind=('x_min', 'x_max'))
    y_min = NumericProperty(0.)
    y_max = NumericProperty(1.)
    def get_y_size(self):
        return self.y_max - self.y_min
    def set_y_size(self, value):
        pass
    y_size = AliasProperty(get_y_size, set_y_size, bind=('y_min', 'y_max'))
    def __init__(self, **kwargs):
        super(SpectrumGraph, self).__init__(**kwargs)
    def add_plot(self, **kwargs):
        plot = SpectrumPlot(**kwargs)
        self.add_widget(plot)
        self.calc_plot_scale()
        return plot
    def calc_plot_scale(self):
        d = {}
        for w in self.children:
            if not isinstance(w, SpectrumPlot):
                continue
            if not w.enabled:
                continue
            pscale = w.calc_plot_scale()
            for key, val in pscale.items():
                if key not in d:
                    d[key] = val
                    continue
                if 'min' in key:
                    if val < d[key]:
                        d[key] = val
                elif 'max' in key:
                    if val > d[key]:
                        d[key] = val
        print d
        for attr, val in d.items():
            setattr(self, attr, val)
        self.plot_params.update(d)
    def freq_to_x(self, freq):
        x = (freq - self.x_min) / self.x_size
        return x * self.width
    def db_to_y(self, db):
        y = (db - self.y_min) / self.y_size
        return y * self.height
        
class SpectrumPlot(Widget):
    name = StringProperty('')
    points = ListProperty([])
    color = ListProperty([0., 1., 0., .8])
    enabled = BooleanProperty(True)
    selected = BooleanProperty(False)
    def __init__(self, **kwargs):
        super(SpectrumPlot, self).__init__(**kwargs)
        self.spectrum = kwargs.get('spectrum')
        self.build_data()
        if self.parent is not None:
            self.parent.bind(plot_params=self._trigger_update)
            self.parent.calc_plot_scale()
        self.bind(parent=self.on_parent_set)
        self.bind(pos=self._trigger_update, size=self._trigger_update)
    def on_parent_set(self, *args, **kwargs):
        if self.parent is None:
            return
        self.parent.bind(plot_params=self._trigger_update)
        self.parent.calc_plot_scale()
    def on_enabled(self, instance, value):
        if value:
            self._trigger_update()
        else:
            self.points = []
    def _trigger_update(self, *args, **kwargs):
        self.draw_plot()
    def draw_plot(self):
        if self.parent is None:
            return
        freq_to_x = self.parent.freq_to_x
        db_to_y = self.parent.db_to_y
        self.points = []
        if not self.enabled:
            return
        for sample in self.spectrum.iter_samples():
            xy = [freq_to_x(sample.frequency), 
                  db_to_y(sample.magnitude)]
            self.points.extend(xy)
    def build_data(self):
        spectrum = self.spectrum
        dtype = np.dtype(float)
        x = np.fromiter(spectrum.iter_frequencies(), dtype)
        y = np.fromiter((s.magnitude for s in spectrum.iter_samples()), dtype)
        self.xy_data = {'x':x, 'y':y}
    def calc_plot_scale(self):
        d = {}
        for key, data in self.xy_data.items():
            for mkey in ['min', 'max']:
                _key = '_'.join([key, mkey])
                m = getattr(data, mkey)
                val = float(m())
                if mkey == 'min':
                    val -= 1
                else:
                    val += 1
                d[_key] = val
        return d

class PlotToolPanel(GridLayout):
    def add_plot(self, plot_widget):
        self.add_widget(PlotTools(plot=plot_widget))
        
class PlotTools(BoxLayout):
    label_widget = ObjectProperty(None)
    switch_widget = ObjectProperty(None)
    color_btn = ObjectProperty(None)
    plot = ObjectProperty(None)
    root_widget = ObjectProperty(None)
    def on_color_btn_release(self, *args, **kwargs):
        self.color_picker = PlotColorPicker(color=self.plot.color)
        self.color_picker.bind(color=self.on_color_picker_color)
        root = self.root_widget
        popup = root.show_popup(title='Choose Color', content=self.color_picker, 
                                size_hint=(.9, .9), auto_dismiss=False)
        popup.bind(on_dismiss=self.on_popup_dismiss)
    def on_color_picker_color(self, instance, value):
        self.plot.color = value
        self.root_widget.close_popup()
    def on_popup_dismiss(self, *args, **kwargs):
        self.color_picker = None
        
class PlotColorPicker(BoxLayout):
    color = ListProperty([])
    color_picker = ObjectProperty(None)
    ok_btn = ObjectProperty(None)
    cancel_btn = ObjectProperty(None)
    