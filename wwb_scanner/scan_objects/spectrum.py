import threading
import datetime
import time

from wwb_scanner.core import JSONMixin
from wwb_scanner.utils.color import Color
from wwb_scanner.scan_objects import Sample, TimeBasedSample
try:
    from wwb_scanner import file_handlers
except ImportError:
    file_handlers = None
try:
    from wwb_scanner.ui.plots import SpectrumPlot
except ImportError:
    SpectrumPlot = None
    
EPOCH = datetime.datetime(1970, 1, 1)

def get_file_handlers():
    global file_handlers
    if file_handlers is None:
        from wwb_scanner import file_handlers as _file_handlers
        file_handlers = _file_handlers
    return file_handlers
def get_importer():
    return get_file_handlers().BaseImporter
def get_exporter():
    return get_file_handlers().BaseExporter
    
def get_spectrum_plot():
    global SpectrumPlot
    if SpectrumPlot is None:
        from wwb_scanner.ui.plots import SpectrumPlot as _SpectrumPlot
        SpectrumPlot = _SpectrumPlot
    return SpectrumPlot

class Spectrum(JSONMixin):
    def __init__(self, **kwargs):
        self.name = kwargs.get('name')
        self.color = Color(kwargs.get('color'))
        datetime_utc = kwargs.get('datetime_utc')
        timestamp_utc = kwargs.get('timestamp_utc')
        if datetime_utc is not None:
            self.datetime_utc = datetime_utc
        else:
            if timestamp_utc is None:
                timestamp_utc = time.time()
            self.timestamp_utc = timestamp_utc
        self.step_size = kwargs.get('step_size')
        self.data_updated = threading.Event()
        self.data_update_lock = threading.Lock()
        self.samples = {}
        self.center_frequencies = kwargs.get('center_frequencies', [])
    @property
    def datetime_utc(self):
        return getattr(self, '_datetime_utc', None)
    @datetime_utc.setter
    def datetime_utc(self, value):
        if value == self.datetime_utc:
            return
        if value is None:
            return
        self._datetime_utc = value
        td = value - EPOCH
        timestamp = td.total_seconds()
        if timestamp != self.timestamp_utc:
            self.timestamp_utc = timestamp
    @property
    def timestamp_utc(self):
        return getattr(self, '_timestamp_utc', None)
    @timestamp_utc.setter
    def timestamp_utc(self, value):
        if value == self.timestamp_utc:
            return
        if value is None:
            return
        self._timestamp_utc = value
        dt = datetime.datetime.utcfromtimestamp(value)
        if dt != self.datetime_utc:
            self.datetime_utc = dt
    def _deserialize(self, **kwargs):
        samples = kwargs.get('samples', {})
        if isinstance(samples, dict):
            for key, data in samples.items():
                if isinstance(data, dict):
                    self.add_sample(**data)
                else:
                    self.add_sample(frequency=key, magnitude=data)
        else:
            for sample_kwargs in samples:
                self.add_sample(**sample_kwargs)
    @classmethod
    def import_from_file(cls, filename):
        importer = get_importer()
        return importer.import_file(filename)
    def export_to_file(self, **kwargs):
        exporter = get_exporter()
        kwargs['spectrum'] = self
        exporter.export_to_file(**kwargs)
    def show_plot(self):
        plot_cls = get_spectrum_plot()
        plot = plot_cls(spectrum=self)
        plot.build_plot()
        return plot
    def add_sample(self, **kwargs):
        f = kwargs.get('frequency')
        if kwargs.get('is_center_frequency') and f not in self.center_frequencies:
            self.center_frequencies.append(f)
        if f in self.samples:
            sample = self.samples[f]
            if kwargs.get('force_magnitude'):
                sample.magnitude = kwargs.get('magnitude')
            return sample
        kwargs.setdefault('spectrum', self)
        sample = self._build_sample(**kwargs)
        self.set_data_updated()
        return sample
    def _build_sample(self, **kwargs):
        sample = Sample(**kwargs)
        self.samples[sample.frequency] = sample
        return sample
    def iter_frequencies(self):
        for key in sorted(self.samples.keys()):
            yield key
    def iter_samples(self):
        for key in self.iter_frequencies():
            yield self.samples[key]
    def on_sample_change(self, **kwargs):
        sample = kwargs.get('sample')
        if sample.frequency not in self.samples:
            return
        self.set_data_updated()
    def set_data_updated(self):
        with self.data_update_lock:
            self.data_updated.set()
    def _serialize(self):
        attrs = ['name', 'color', 'timestamp_utc', 'step_size', 'center_frequencies']
        d = {attr: getattr(self, attr) for attr in attrs}
        samples = self.samples
        d['samples'] = {k: samples[k]._serialize() for k in samples.keys()}
        return d
    
class TimeBasedSpectrum(Spectrum):
    def _build_sample(self, **kwargs):
        sample = TimeBasedSample(**kwargs)
        if sample.frequency not in self.samples:
            self.samples[sample.frequency] = {}
        self.samples[sample.frequency][sample.timestamp] = sample
        return sample
    def iter_samples(self):
        samples = self.samples
        last_ts = None
        for key in self.iter_frequencies():
            if last_ts is None:
                last_ts = min(samples[key])
                sample = samples[key][last_ts]
            else:
                if last_ts in samples[key]:
                    sample = samples[key][last_ts]
                else:
                    l = [ts for ts in samples[key] if last_ts < ts]
                    if not len(l):
                        sample = None
                    else:
                        last_ts = min(l)
                        sample = samples[key][last_ts]
            if sample is None:
                break
            yield sample

def compare_spectra(spec1, spec2):
    diff_spec = Spectrum()
    for sample in spec1.iter_samples():
        other_sample = spec2.samples.get(sample.frequency)
        if other_sample is None:
            continue
        magnitude = sample.magnitude - other_sample.magnitude
        diff_spec.add_sample(frequency=sample.frequency, magnitude=magnitude)
    return diff_spec
