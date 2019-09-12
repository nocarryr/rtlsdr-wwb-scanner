from bisect import bisect_left
import numpy as np

from PySide2 import QtCore, QtQml, QtQuick, QtGui
from PySide2.QtCore import Signal, Property, Slot
from PySide2.QtCharts import QtCharts


from wwb_scanner.file_handlers import BaseImporter
from wwb_scanner.scan_objects.spectrum import Spectrum
from wwb_scanner.ui.pyside.utils import IntervalTimer, is_pathlike

GRAPH_DTYPE = np.dtype([
    ('x', np.float64),
    ('y', np.float64),
])

class GraphPoint(QtCore.QPointF):
    def __init__(self, *args):
        self._index = 0
        super().__init__(*args)
    def _g_index(self): return self._index
    def _s_index(self, value):
        self._index = value
    index = Property(int, _g_index, _s_index)

class GraphTableModel(QtCore.QAbstractTableModel):
    def __init__(self, *args):
        # self._data_arr = np.zeros(0, dtype=GRAPH_DTYPE)
        self._data = np.zeros((2,0), dtype=np.float64)
        # self._data = np.zeros((2,64), dtype=np.float64)
        # self._data[0] = np.linspace(0,1,64) * 450e6 + 450e6
        # self._data[1] = np.sin(self._data[0]) * -1
        super().__init__(*args)
    def columnCount(self, parent):
        return self._data.shape[1]
    def rowCount(self, parent):
        return self._data.shape[0]
    def flags(self, index):
        return QtCore.Qt.ItemFlags.ItemIsEnabled
    # def headerData(self, section, orientation, role):
    #
    def data(self, index, role):
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            # print(f'data access: {index}')
            return float(self._data[index.row(), index.column()])
        return QtCore.QVariant()
    def _reshape_data(self, d_arr):
        new_shape = (2, d_arr.size)
        cur_shape = self._data.shape
        # print(f'cur_shape={cur_shape}, new_shape={new_shape}')
        parent = QtCore.QModelIndex()
        if cur_shape[-1] > new_shape[-1]:
            start_col = cur_shape[-1] - 1
            end_col = new_shape[-1] - 1
            ix = self.index(0, 0)
            # parent = self.parent(ix)
            parent = ix
            self.beginRemoveColumns(parent, start_col, end_col)
            self._data = self._data[...,:end_col+1]
            self.endRemoveColumns()
        elif cur_shape[-1] < new_shape[-1]:
            start_col = cur_shape[-1]
            end_col = new_shape[-1] - 1
            # print(f'start_col={start_col}, end_col={end_col}')
            ix = self.index(0, 0)
            # parent = self.parent(ix)
            # parent = ix
            self.beginInsertColumns(parent, start_col, end_col)
            data = np.zeros(new_shape, dtype=np.float64)
            if True:# self._data.size:
                data[:,:start_col] = self._data[:,:]
                data[0,start_col:] = d_arr['x'][start_col:]
                data[1,start_col:] = d_arr['y'][start_col:]
            self._data = data
            self.endInsertColumns()

    def set_from_graph_dtype(self, d_arr):
        if d_arr.size != self._data.shape[-1]:
            # self._reshape_data((2,d_arr.size))
            self._reshape_data(d_arr)
            x_changed = True
            y_changed = True
        else:
            x_changed = not np.array_equal(self._data[0], d_arr['x'])
            y_changed = not np.array_equal(self._data[1], d_arr['y'])
        if not x_changed and not y_changed:
            return
        data = self._data

        change_ix_x = np.flatnonzero(np.not_equal(data[0], d_arr['x']))
        change_ix_y = np.flatnonzero(np.not_equal(data[1], d_arr['y']))

        change_ix = set(change_ix_x) | set(change_ix_y)

        data[0] = d_arr['x']
        data[1] = d_arr['y']
        # for i in range(2):
        #     print('data[{}].min={}, .max={}'.format(
        #         i, data[i].min(), data[i].max(),
        #     ))

        if not len(change_ix):
            return
        tl = self.index(0, min(change_ix))
        br = self.index(data.shape[0]-1, max(change_ix))
        # print(f'tl={tl}, br={br}')
        self.dataChanged.emit(tl, br)


class TableGraphData(QtCore.QObject):
    _n_model = Signal()
    def __init__(self, *args):
        # self._model = GraphTableModel()
        self._model = None
        super().__init__(*args)

    def _g_model(self): return self._model
    def _s_model(self, value):
        self._model = value
        self._n_model.emit()
        self._on_model_changed()
    model = Property(GraphTableModel, _g_model, _s_model, notify=_n_model)

    def _on_model_changed(self):
        pass

    def set_from_graph_dtype(self, d_arr):
        if self.model is None:
            return
        self.model.set_from_graph_dtype(d_arr)

#  NOT USED
class LineGraphData(QtCore.QObject):
    _n_series = Signal()
    def __init__(self, *args):
        super().__init__(*args)
        self._series = QtCharts.QLineSeries()
        self.value_map = {}
        self.index_map = {}

    def _g_series(self): return self._series
    def _s_series(self, value):
        if value == self._series:
            return
        self._series = value
        self._update_series_data()
        self._n_series.emit()
    series = Property(QtCharts.QLineSeries, _g_series, _s_series, notify=_n_series)

    def _update_series_data(self):
        self.series.clear()
        for pt in self:
            self.series.append(pt)

    def set_point(self, x, y):
        pt = self.value_map.get(x)
        if pt is not None:
            if pt.y() == y:
                return
            pt.setY(y)
            self.series.replace(pt.index, pt)
        else:
            pt = GraphPoint(x, y)
            if not len(self.value_map.keys()):
                self.series.append(pt)
                pt.index = 0
            elif x > max(self.value_map.keys()):
                pt.index = self.series.count()
                self.series.append(pt)
            else:
                idx = bisect_left(sorted(self.value_map.keys()), x)
                pt.index = idx
                self.series.insert(idx, pt)
                self._insert_index(idx, x)
            self.value_map[x] = pt
            self.index_map[pt.index] = pt
    def get_point(self, x):
        return self.value_map.get(x)
    def clear_points(self):
        self.series.clear()
        self.value_map.clear()
    def _insert_index(self, idx, x):
        for pt in self.value_map.values():
            if pt.index < idx:
                continue
            elif pt.index == idx:
                if pt.x() == x:
                    continue
            if pt.index in self.index_map:
                del self.index_map[pt.index]
            pt.index += 1
            self.index_map[pt.index] = pt

    def __len__(self):
        return len(self.series_map)
    def iter_indices(self):
        return sorted(self.index_map.keys())
    def __iter__(self):
        for i in self.iter_indices():
            yield self.index_map[i]


# class GraphDataNP(GraphData):
#     def __init__(self, *args):
#         self._xy_arr = np.zeros(0, dtype=GRAPH_DTYPE)
#         super().__init__(*args)

class SpectrumGraphData(QtQuick.QQuickItem):
    _n_model = Signal()
    _n_name = Signal()
    _n_min_value = Signal()
    _n_max_value = Signal()
    _n_spectrum = Signal()
    _n_color = Signal()
    _n_graphVisible = Signal()
    def __init__(self, *args):
        self.xy_data = np.zeros(0, dtype=GRAPH_DTYPE)
        self._min_value = QtCore.QPointF(0., 0.)
        self._max_value = QtCore.QPointF(0., 0.)
        self._model = None
        self._spectrum = None
        self._name = None
        self._color = None
        self._graphVisible = True
        super().__init__(*args)

    def _g_model(self): return self._model
    def _s_model(self, value):
        self._model = value
        self._n_model.emit()
        self._on_model_changed()
    model = Property(QtCore.QObject, _g_model, _s_model, notify=_n_model)

    def _g_name(self):
        name = self._name
        if name is not None:
            is_p, p = is_pathlike(name)
            if is_p:
                return p.name
        return name
    def _s_name(self, value):
        if value == self._name:
            return
        self._name = value
        self._n_name.emit()
    name = Property(str, _g_name, _s_name, notify=_n_name)

    def _g_color(self): return self._color
    def _s_color(self, value):
        if value == self._color:
            return
        self._color = value
        self._n_color.emit()
        if self.spectrum is not None:
            rgba = value.getRgbF()
            if rgba != self.spectrum.color:
                self.spectrum.color.from_list(rgba)
    color = Property(QtGui.QColor, _g_color, _s_color, notify=_n_color)

    def _g_graphVisible(self): return self._graphVisible
    def _s_graphVisible(self, value):
        if value == self._graphVisible:
            return
        self._graphVisible = value
        self._n_graphVisible.emit()
    graphVisible = Property(bool, _g_graphVisible, _s_graphVisible, notify=_n_graphVisible)

    def _g_min_value(self): return self._min_value
    def _s_min_value(self, value):
        self._min_value = value
        self._n_min_value.emit()
    minValue = Property(QtCore.QPointF, _g_min_value, _s_min_value, notify=_n_min_value)

    def _g_max_value(self): return self._max_value
    def _s_max_value(self, value):
        self._max_value = value
        self._n_max_value.emit()
    maxValue = Property(QtCore.QPointF, _g_max_value, _s_max_value, notify=_n_max_value)

    def _g_spectrum(self): return self._spectrum
    def _s_spectrum(self, value):
        if value == self._spectrum:
            return
        self._spectrum = value
        self._n_spectrum.emit()
        if value is not None:
            if self.name is None:
                self.name = value.name
            else:
                value.name = self.name
            if value.color != value.DEFAULT_COLOR:
                self.color = QtGui.QColor.fromRgbF(*value.color.to_list())
        self.update_spectrum_data()
    spectrum = Property(object, _g_spectrum, _s_spectrum, notify=_n_spectrum)

    def _set_from_graph_dtype(self, d_arr):
        if self.model is None:
            return
        self.model.set_from_graph_dtype(d_arr)
    def _on_model_changed(self):
        self._set_series_from_data()

    @Slot(float, result=QtCore.QPointF)
    def get_nearest_by_x(self, value):
        xy_data = self.xy_data
        if not xy_data.size:
            return QtCore.QPointF(-1, -1)
        ix = np.searchsorted(xy_data['x'], value)
        if ix >= xy_data.size:
            ix = xy_data.size - 1
        x = xy_data['x'][ix]
        y = xy_data['y'][ix]
        return QtCore.QPointF(x, y)

    @Slot()
    def update_spectrum_data(self):
        if self.spectrum is None:
            return
        if not self.spectrum.data_updated.is_set():
            return
        self._update_data_from_spectrum()
        self._set_series_from_data()

    def _update_data_from_spectrum(self):
        spectrum = self.spectrum
        dtype = np.dtype(float)
        with spectrum.data_update_lock:
            xy_data = np.zeros(spectrum.sample_data.size, dtype=GRAPH_DTYPE)
            data = spectrum.sample_data.data
            # print(f'data: shape={data.shape}, dtype={data.dtype}')
            xy_data['x'] = data['frequency']
            freqmin = xy_data['x'].min()
            freqmax = xy_data['x'].max()
            # print(f'freq_range: "{freqmin}" - "{freqmax}"')
            xy_data['y'] = spectrum.sample_data.data['dbFS']
            nan_ix = np.flatnonzero(np.isnan(xy_data['y']))
            xy_data['y'][nan_ix] = -110
            # if np.any(np.isnan(y)):
            #     # print('NaN in ydata')
            #     if hasattr(self, 'xy_data'):
            #         return
            #     y = np.array([-110])
            # self.xy_data = {'x':x, 'y':y}
            self.xy_data = xy_data
            spectrum.data_updated.clear()
        self._update_extents()

    def _update_extents(self):
        self.minValue = QtCore.QPointF(self.xy_data['x'].min(), self.xy_data['y'].min())
        self.maxValue = QtCore.QPointF(self.xy_data['x'].max(), self.xy_data['y'].max())

    def _set_series_from_data(self):
        if self.model is None:
            return
        self.model.set_from_graph_dtype(self.xy_data)
        # self.set_from_graph_dtype(self.xy_data)
        # xy_data = self.xy_data
        # for x, y in np.nditer([xy_data['x'], xy_data['y']]):
        #     # print(x)
        #     # print(y)
        #     self.set_point(float(x), float(y))
    @Slot(QtCore.QUrl)
    def load_from_file(self, uri):
        # orig_fn = filename
        # filename = str(filename)
        filename = uri.toLocalFile()
        # if filename.startswith('file://'):
        #     filename = filename.lstrip('file://')
        print(f'load_from_file: "{filename}"')
        # spectrum = Spectrum.import_from_file(filename)
        spectrum = BaseImporter.import_file(filename)
        spectrum.set_data_updated()
        print('spectrum created')
        self.spectrum = spectrum
        print('update_spectrum_data')
        self.update_spectrum_data()
        print('load complete')

    @Slot(QtCore.QUrl)
    def save_to_file(self, uri):
        filename = uri.toLocalFile()
        print('save_to_file: ', filename)
        self.spectrum.export_to_file(filename=filename)

class LiveSpectrumGraphData(SpectrumGraphData):
    _n_update_interval = Signal()
    _n_update_timer = Signal()
    _n_scanner = Signal()
    updateSpectrumData = Signal()
    def __init__(self, *args):
        self._update_interval = None
        self._update_timer = None
        self._scanner = None
        super().__init__(*args)
        self.updateSpectrumData.connect(self.update_spectrum_data)
    def _g_scanner(self): return self._scanner
    def _s_scanner(self, value):
        if value == self._scanner:
            return
        if self._scanner is not None:
            self._scanner.disconnect(self)
        self._scanner = value
        print('scanner: ', self._scanner)
        self._n_scanner.emit()
        if self._scanner is not None:
            self.spectrum = self._scanner.spectrum
            self._scanner.scannerRunState.connect(self.on_scanner_run_state)
            self.update_interval = .1
        else:
            self.update_interval = -1
    scanner = Property(QtCore.QObject, _g_scanner, _s_scanner, notify=_n_scanner)

    def on_scanner_run_state(self, state):
        if self.scanner is None:
            return
        if not self.scanner.running:
            self.update_interval = -1
            if self.spectrum is not None:
                with self.spectrum.data_update_lock:
                    self.spectrum.set_data_updated()
                    self.update_spectrum_data()
            self.scanner = None

    def _g_update_interval(self): return self._update_interval
    def _s_update_interval(self, value):
        if value == self._update_interval:
            return
        self._update_interval = value
        if self.update_timer is not None:
            self.update_timer.stop.emit()
        if value is not None and value > 0:
            ms = int(round(value * 1000))
            if self.update_timer is None:
                self.update_timer = IntervalTimer(interval_ms=ms)
                self.update_timer.trigger.connect(self.on_update_timer_trigger)
            else:
                self.update_timer.interval_ms = ms
            self.update_timer.start.emit()
        self._n_update_interval.emit()
    update_interval = Property(float, _g_update_interval, _s_update_interval, notify=_n_update_interval)

    def _g_update_timer(self): return self._update_timer
    def _s_update_timer(self, value):
        self._update_timer = value
        self._n_update_timer.emit()
    update_timer = Property(QtCore.QObject, _g_update_timer, _s_update_timer, notify=_n_update_timer)

    def on_update_timer_trigger(self, *args):
        self.updateSpectrumData.emit()

    def _update_extents(self):
        if self.scanner is not None:
            min_x = self.scanner.startFreq
            if self.xy_data.size and self.xy_data['x'].min() < min_x:
                min_x = self.xy_data['x'].min()
            max_x = self.scanner.endFreq
            if self.xy_data.size and self.xy_data['x'].max() > max_x:
                max_x = self.xy_data['x'].max()
        else:
            min_x = self.xy_data['x'].min()
            max_x = self.xy_data['y'].max()
        self.minValue = QtCore.QPointF(min_x, self.xy_data['y'].min())
        self.maxValue = QtCore.QPointF(max_x, self.xy_data['y'].max())

# NOT USED
class SpectrumLoader(QtCore.QObject):
    _n_instance = Signal()
    # loadFromFile = Signal(QtCore.QObject)
    # loadComplete = Signal(QtCore.QObject, SpectrumGraphData)
    def __init__(self, *args):
        self._instance = None
        super().__init__(*args)
        # self.loadFromFile.connect(self.load_from_file)

    def _g_instance(self): return self._instance
    def _s_instance(self, value):
        self._instance = value
        self._n_instance.emit()
    instance = Property(SpectrumGraphData, _g_instance, _s_instance, notify=_n_instance)

    @Slot(QtCore.QUrl)
    def load_from_file(self, uri):
        # orig_fn = filename
        # filename = str(filename)
        filename = uri.fileName()
        # if filename.startswith('file://'):
        #     filename = filename.lstrip('file://')
        print(f'load_from_file: "{filename}"')
        # spectrum = Spectrum.import_from_file(filename)
        spectrum = BaseImporter.import_file(filename)
        spectrum.set_data_updated()
        print('spectrum created')
        graph_data = SpectrumGraphData()
        print('attaching to graph_data')
        graph_data.spectrum = spectrum
        print('update_spectrum_data')
        graph_data.update_spectrum_data()
        print('len: ', len(graph_data.xy_data))
        print('returning to qml')
        self.instance = graph_data
        # self.loadComplete.emit(uri, graph_data)
        # return graph_data

def register_qml_types():
    QtQml.qmlRegisterType(GraphTableModel, 'GraphUtils', 1, 0, 'GraphTableModel')
    QtQml.qmlRegisterType(TableGraphData, 'GraphUtils', 1, 0, 'TableGraphData')
    QtQml.qmlRegisterType(LineGraphData, 'GraphUtils', 1, 0, 'LineGraphData')
    QtQml.qmlRegisterType(SpectrumGraphData, 'GraphUtils', 1, 0, 'SpectrumGraphData')
    QtQml.qmlRegisterType(LiveSpectrumGraphData, 'GraphUtils', 1, 0, 'LiveSpectrumGraphData')
    QtQml.qmlRegisterType(SpectrumLoader, 'GraphUtils', 1, 0, 'SpectrumLoader')
