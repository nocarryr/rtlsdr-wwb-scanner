import numpy as np

#from kivy.garden.graph import Graph, MeshLinePlot
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import Color, Line
from kivy.garden.tickline import Tickline, Tick, LabellessTick
from kivy.core.text import Label as CoreLabel
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.properties import (
    ListProperty, 
    ReferenceListProperty, 
    DictProperty, 
    NumericProperty, 
    AliasProperty, 
    BooleanProperty, 
    StringProperty, 
    ObjectProperty, 
)

from wwb_scanner.core import JSONMixin
from wwb_scanner.scan_objects import Spectrum

class TickContainer(FloatLayout):
    def do_layout(self, *args, **kwargs):
        super(TickContainer, self).do_layout(*args, **kwargs)
        for c in self.children:
            if isinstance(c, Tickline):
                c.redraw()
    
class CustomLabelTick(Tick):
    spectrum_graph = ObjectProperty(None)
    tickline_parent = ObjectProperty(None)
    def get_label_texture(self, index, **kwargs):
        if self.tickline_parent is None:
            return super(CustomLabelTick, self).get_label_texture(index, **kwargs)
        kwargs['font_size'] = self.tick_size[1] * 2
        pos = self.tickline_parent.index2pos(index)
        lbl_text = self._get_custom_label_text(pos)
        label = CoreLabel(
            text=lbl_text, 
            **kwargs)
        label.refresh()
        return label.texture
        
class FrequencyTick(CustomLabelTick):
    def _get_custom_label_text(self, pos):
        s = '%07.3f' % (self.spectrum_graph.x_to_freq(pos))
        if s.split('.')[1] == '000':
            s = s.split('.')[0]
        return s
        
class DbTick(CustomLabelTick):
    def _get_custom_label_text(self, pos):
        return '%5.1f' % (self.spectrum_graph.y_to_db(pos))
        
class GraphViewControls(BoxLayout):
    spectrum_graph = ObjectProperty(None)
    h_slider = ObjectProperty(None)
    zoom_in_btn = ObjectProperty(None)
    zoom_out_btn = ObjectProperty(None)
    h_scroll_range = ListProperty([100, 1000])
    h_scroll_value = NumericProperty(500)
    h_scroll_step = NumericProperty(1)
    h_scrolling = BooleanProperty(False)
    zoom_step = NumericProperty(1.)
    zoom_timeout = NumericProperty(.25)
    zoom_event = ObjectProperty(None, allownone=True)
    def on_spectrum_graph(self, *args):
        sg = self.spectrum_graph
        if sg is None:
            return
        sg.bind(x_range=self.on_spectrum_graph_x_range, 
                x_center=self.on_spectrum_graph_x_center)
    def on_spectrum_graph_x_range(self, instance, value):
        pass
    def on_spectrum_graph_x_center(self, instance, value):
        if self.h_scrolling:
            return
        self.h_scroll_value = value
    def on_h_scroll_value(self, *args):
        sg = self.spectrum_graph
        if sg is None:
            return
        self.h_scrolling = True
        sg.x_center = self.h_scroll_value
        self.h_scrolling = False
    def on_zoom_btn_press(self, btn):
        self.cancel_zoom()
        if btn == self.zoom_in_btn:
            m = self.zoom_in
        else:
            m = self.zoom_out
        m()
        self.zoom_event = Clock.schedule_interval(m, self.zoom_timeout)
    def on_zoom_btn_release(self, btn):
        self.cancel_zoom()
    def cancel_zoom(self, *args):
        if self.zoom_event is None:
            return
        Clock.unschedule(self.zoom_event)
        self.zoom_event = None
    def zoom_in(self, *args):
        sg = self.spectrum_graph
        if sg is None:
            return
        sg.x_size -= self.zoom_step
    def zoom_out(self, *args):
        sg = self.spectrum_graph
        if sg is None:
            return
        sg.x_size += self.zoom_step
        
class SpectrumGraph(RelativeLayout, JSONMixin):
    scan_controls = ObjectProperty(None)
    plot_params = DictProperty()
    x_min = NumericProperty(0.)
    x_max = NumericProperty(1.)
    auto_scale_x = BooleanProperty(True)
    auto_scale_y = BooleanProperty(True)
    selected = ObjectProperty(None)
    tick_container = ObjectProperty(None)
    x_tick_line = ObjectProperty(None)
    y_tick_line = ObjectProperty(None)
    tick_redraw_event = ObjectProperty(None, allownone=True)
    def get_x_size(self):
        return self.x_max - self.x_min
    def set_x_size(self, value):
        x_center = self.x_center
        x_min = x_center - (value / 2.)
        x_max = x_center + (value / 2.)
        self.x_range = [x_min, x_max]
        return True
    x_size = AliasProperty(get_x_size, set_x_size, bind=('x_min', 'x_max'))
    x_range = ReferenceListProperty(x_min, x_max)
    def get_x_center(self):
        return (self.x_size / 2.) + self.x_min
    def set_x_center(self, value):
        size = self.x_size
        x_min = value - (size / 2.)
        x_max = x_min + size
        self.x_range = [x_min, x_max]
        return True
    x_center = AliasProperty(get_x_center, set_x_center, bind=('x_min', 'x_max'))
    y_min = NumericProperty(-100.)
    y_max = NumericProperty(0.)
    def get_y_size(self):
        return self.y_max - self.y_min
    def set_y_size(self, value):
        pass
    y_size = AliasProperty(get_y_size, set_y_size, bind=('y_min', 'y_max'))
    def __init__(self, **kwargs):
        super(SpectrumGraph, self).__init__(**kwargs)
        props = ['x_min', 'x_max', 'y_min', 'y_max']
        bind_kwargs = {prop: self.trigger_tick_redraw for prop in props}
        self.bind(**bind_kwargs)
        Window.bind(mouse_pos=self.on_mouse_pos)
    def on_mouse_pos(self, instance, pos):
        if self.parent is None:
            return
        if self.graph_overlay is None:
            return
        if self.selected is None:
            return
        ppos = self.parent.to_widget(*pos)
        real_x, real_y = self.to_local(*ppos)
        if not self.collide_point(real_x, real_y):
            return
        real_freq = self.x_to_freq(real_x)
        freq, db = self.selected.get_nearest_by_freq(real_freq)
        if freq is None:
            return
        x = self.freq_to_x(freq)
        y = self.db_to_y(db)
        self.graph_overlay.plot_values.update({
            'x':x, 'y':y, 'freq':freq, 'db':db, 
        })
    def on_tick_container(self, *args):
        if self.tick_container is None:
            return
        self.build_ticklines()
    def on_x_min(self, instance, value):
        self.plot_params['x_min'] = value
    def on_x_max(self, instance, value):
        self.plot_params['x_max'] = value
    def on_y_min(self, instance, value):
        self.plot_params['y_min'] = value
    def on_y_max(self, instance, value):
        self.plot_params['y_max'] = value
    def trigger_tick_redraw(self, *args):
        if self.tick_redraw_event is not None:
            return
        if self.x_tick_line is None:
            return
        if self.y_tick_line is None:
            return
        self.tick_redraw_event = Clock.schedule_once(self._redraw_ticklines)
    def _redraw_ticklines(self, *args, **kwargs):
        if self.tick_redraw_event is not None:
            self.tick_redraw_event = None
        self.x_tick_line.redraw()
        self.y_tick_line.redraw()
    def on_scan_controls(self, *args):
        if self.scan_controls is None:
            return
        scan_range = self.scan_controls.scan_range
        self.x_min = scan_range[0]
        self.x_max = scan_range[1]
    def add_plot(self, **kwargs):
        plot = kwargs.get('plot')
        if plot is None:
            if self.selected is None:
                kwargs['selected'] = True
            plot = SpectrumPlot(**kwargs)
        plot.bind(selected=self.on_plot_selected)
        self.add_widget(plot)
        self.calc_plot_scale()
        if plot.selected:
            self.selected = plot
        return plot
    def add_widget(self, w, index=0, canvas=None):
        if isinstance(w, GraphOverlay):
            index = 0
        elif len(self.children):
            index += 1
        super(SpectrumGraph, self).add_widget(w, index)
    def on_plot_selected(self, instance, value):
        if not value:
            return
        self.selected = instance
    def calc_plot_scale(self):
        auto_x = self.auto_scale_x
        auto_y = self.auto_scale_y
        if not auto_x and not auto_y:
            return
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
        for attr, val in d.items():
            if not auto_x and attr.split('_')[0] == 'x':
                continue
            if not auto_y and attr.split('_')[0] == 'y':
                continue
            setattr(self, attr, val)
        if self.x_tick_line is None:
            self.build_ticklines()
    def build_ticklines(self):
        def fake_collide_point(*args):
            return False
        x_ticks = [
            FrequencyTick(spectrum_graph=self, halign='line_right', valign='bottom'), 
            LabellessTick(scale_factor=2., halign='line_right', valign='bottom'), 
        ]
        y_ticks = [
            DbTick(spectrum_graph=self, halign='left', valign='bottom'), 
            LabellessTick(scale_factor=2., halign='left'), 
        ]
        self.x_tick_line = Tickline(cover_background=False, background_color=(0.,0.,0.,0.), draw_line=False,
                                    orientation='horizontal', zoomable=False, 
                                    ticks=x_ticks)
        self.y_tick_line = Tickline(cover_background=False, background_color=(0.,0.,0.,0.), draw_line=False,
                                    orientation='vertical', zoomable=False, 
                                    ticks=y_ticks)
        self.x_tick_line.collide_point = fake_collide_point
        self.y_tick_line.collide_point = fake_collide_point
        x_ticks[0].tickline_parent = self.x_tick_line
        y_ticks[0].tickline_parent = self.y_tick_line
        self.tick_container.add_widget(self.x_tick_line)
        self.tick_container.add_widget(self.y_tick_line)
    def freq_to_x(self, freq):
        x = (freq - self.x_min) / self.x_size
        return x * self.width
    def x_to_freq(self, x):
        return (x / self.width * self.x_size) + self.x_min
    def db_to_y(self, db):
        y = (db - self.y_min) / self.y_size
        return y * self.height
    def y_to_db(self, y):
        return (y / self.height * self.y_size) + self.y_min
    def _serialize(self):
        attrs = ['x_max', 'x_min', 'y_max', 'y_min', 
                 'auto_scale_x', 'auto_scale_y']
        d = {attr:getattr(self, attr) for attr in attrs}
        d['plots'] = []
        for plot in self.children:
            if not isinstance(plot, SpectrumPlot):
                continue
            d['plots'].append(plot._serialize())
        return d
    def _deserialize(self, **kwargs):
        for c in self.children[:]:
            if isinstance(c, SpectrumPlot):
                self.remove_widget(c)
        for key, val in kwargs.items():
            if key == 'plots':
                for pldata in val:
                    plot = SpectrumPlot.from_json(pldata)
                    self.add_plot(plot=plot)
                    self.parent.tool_panel.add_plot(plot)
            else:
                setattr(self, key, val)
        
class SpectrumPlot(Widget, JSONMixin):
    name = StringProperty('')
    points = ListProperty([])
    color = ListProperty([0., 1., 0., .8])
    enabled = BooleanProperty(True)
    selected = BooleanProperty(False)
    spectrum = ObjectProperty(None)
    def __init__(self, **kwargs):
        super(SpectrumPlot, self).__init__(**kwargs)
        if self.parent is not None:
            self.parent.bind(plot_params=self._trigger_update)
            self.parent.calc_plot_scale()
        self.bind(parent=self.on_parent_set)
        self.bind(pos=self._trigger_update, size=self._trigger_update)
    def on_spectrum(self, *args):
        if self.spectrum is None:
            return
        self.build_data()
        if self.spectrum.name is not None:
            self.name = self.spectrum.name
        else:
            self.spectrum.name = self.name
        if self.color != [0., 1., 0., .8]:
            self.spectrum.color.from_list(self.color)
        else:
            self.color = self.spectrum.color.to_list()
    def on_name(self, instance, value):
        if self.spectrum is None:
            return
        if self.spectrum.name == value:
            return
        self.spectrum.name = value
    def on_color(self, instance, value):
        if self.spectrum is None:
            return
        if list(value) == self.spectrum.color.to_list():
            return
        self.spectrum.color.from_list(value)
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
        xy_data = self.xy_data
        for freq, db in zip(xy_data['x'], xy_data['y']):
            xy = [freq_to_x(freq), db_to_y(db)]
            self.points.extend(xy)
    def update_data(self):
        if not self.spectrum.data_updated.is_set():
            return
        self.build_data()
        self.parent.calc_plot_scale()
        self.draw_plot()
    def build_data(self):
        spectrum = self.spectrum
        dtype = np.dtype(float)
        with spectrum.data_update_lock:
            x = np.fromiter(spectrum.iter_frequencies(), dtype)
            y = np.fromiter((s.magnitude for s in spectrum.iter_samples()), dtype)
            self.xy_data = {'x':x, 'y':y}
            spectrum.data_updated.clear()
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
    def get_nearest_by_freq(self, freq):
        spectrum = self.spectrum
        sample = spectrum.samples.get(freq)
        if sample is not None:
            return sample.frequency, sample.magnitude
        xy_data = self.xy_data
        if freq > xy_data['x'].max():
            return None, None
        if freq < xy_data['x'].min():
            return None, None
        i = np.abs(xy_data['x'] - freq).argmin()
        return xy_data['x'][i], xy_data['y'][i]
    def _serialize(self):
        attrs = ['name', 'color', 'enabled', 'selected']
        d = {attr: getattr(self, attr) for attr in attrs}
        d['spectrum_data'] = self.spectrum._serialize()
        return d
    def _deserialize(self, **kwargs):
        spdata = kwargs.get('spectrum_data')
        self.spectrum = Spectrum.from_json(spdata)

class PlotToolPanel(GridLayout):
    def add_plot(self, plot_widget):
        self.add_widget(PlotTools(plot=plot_widget))
        
class PlotTools(BoxLayout):
    label_widget = ObjectProperty(None)
    switch_widget = ObjectProperty(None)
    color_btn = ObjectProperty(None)
    plot = ObjectProperty(None)
    root_widget = ObjectProperty(None)
    def on_plot(self, *args, **kwargs):
        if self.plot is None:
            return
        self.plot.bind(parent=self.on_plot_parent)
    def on_plot_parent(self, *args, **kwargs):
        if self.plot is None:
            return
        if self.plot.parent is None:
            self.parent.remove_widget(self)
    def on_color_btn_release(self, *args, **kwargs):
        self.color_picker = PlotColorPicker(color=self.plot.color)
        self.color_picker.bind(on_select=self.on_color_picker_select, 
                               on_cancel=self.on_color_picker_cancel)
        root = self.root_widget
        popup = root.show_popup(title='Choose Color', content=self.color_picker, 
                                size_hint=(.9, .9), auto_dismiss=False)
        popup.bind(on_dismiss=self.on_popup_dismiss)
    def on_color_picker_select(self, *args):
        self.plot.color = self.color_picker.color
        self.root_widget.close_popup()
    def on_color_picker_cancel(self, *args):
        self.root_widget.close_popup()
    def on_popup_dismiss(self, *args, **kwargs):
        self.color_picker = None
        
class PlotColorPicker(BoxLayout):
    color = ListProperty([.8, .8, .8, 1.])
    color_picker = ObjectProperty(None)
    ok_btn = ObjectProperty(None)
    cancel_btn = ObjectProperty(None)
    __events__ = ('on_select', 'on_cancel')
    def on_select(self, *args):
        pass
    def on_cancel(self, *args):
        pass
        
class GraphOverlay(Widget):
    spectrum_graph = ObjectProperty(None)
    label_widget = ObjectProperty(None)
    crosshair_widget = ObjectProperty(None)
    label_text = StringProperty()
    plot_values = DictProperty()
    def on_plot_values(self, *args, **kwargs):
        freq = self.plot_values.get('freq')
        db = self.plot_values.get('db')
        if freq is None or db is None:
            self.label_text = ''
        else:
            self.label_text = '%07.3f (MHz) - %04.1f (dBm)' % (freq, db)
    
class GraphCrosshair(Widget):
    def on_parent(self, *args, **kwargs):
        if self.parent is None:
            return
        self.parent.bind(plot_values=self.on_plot_values)
    def on_plot_values(self, *args, **kwargs):
        self._trigger_update()
    def _trigger_update(self, *args, **kwargs):
        self.draw_crosshairs()
    def draw_crosshairs(self, *args, **kwargs):
        plot_values = self.parent.plot_values
        self.canvas.clear()
        x, y, f = [plot_values.get(key) for key in ['x', 'y', 'freq']]
        if f is None:
            return
        with self.canvas:
            Color(1., 1., 1.)
            Line(points=[x, self.y, x, self.height])
            Line(points=[self.x, y, self.width, y])
