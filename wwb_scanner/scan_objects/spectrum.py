import threading
import datetime
import time

import numpy as np

from wwb_scanner.core import JSONMixin
from wwb_scanner.utils.dbstore import db_store
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
        self.eid = kwargs.get('eid')
        eid = kwargs.get('scan_config_eid')
        config = kwargs.get('scan_config')
        if config is not None:
            self.scan_config = config
        elif eid is not None:
            self.scan_config_eid = eid
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
        self.sample_data = np.empty([0], dtype=[
            ('frequency', np.float64),
            ('iq', np.complex128),
            ('magnitude', np.float64)
        ])
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
    @property
    def scan_config(self):
        return getattr(self, '_scan_config', None)
    @scan_config.setter
    def scan_config(self, value):
        if value == self.scan_config:
            return
        self._scan_config = value
        if value.get('eid') is None:
            eid = self.scan_config_eid
            if eid is not None:
                value.eid = eid
    @property
    def scan_config_eid(self):
        eid = getattr(self, '_scan_config_eid', None)
        if eid is None:
            config = self.scan_config
            if config is not None:
                eid = self._scan_config_eid = config.get('eid')
        return eid
    @scan_config_eid.setter
    def scan_config_eid(self, value):
        if value == self.scan_config_eid:
            return
        self._scan_config_eid = value
        if value is None:
            return
        config = self.scan_config
        if config is None:
            config = self._scan_config = db_store.get_scan_config(eid=value)
        else:
            if config.get('eid') is None:
                config.eid = value
    def _deserialize(self, **kwargs):
        samples = kwargs.get('samples', {})
        if isinstance(samples, dict):
            for key, data in samples.items():
                if isinstance(data, dict):
                    self.add_sample(**data)
                else:
                    self.add_sample(frequency=key, dbFS=data)
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
                for key in ['iq', 'magnitude', 'dbFS']:
                    if key in kwargs:
                        setattr(sample, key, kwargs[key])
                        break
            return sample
        if len(self.samples) and f < max(self.samples.keys()):
            if not kwargs.get('force_lower_freq', True):
                return
        with self.data_update_lock:
            if f not in self.sample_data['frequency']:
                a = np.zeros(1, dtype=self.sample_data.dtype)
                a['frequency'][0] = f
                self.sample_data = np.append(self.sample_data, a)
                self.sample_data.sort(order='frequency')
                s_ix = np.argwhere(self.sample_data['frequency'] == f)
                for key in ['iq', 'magnitude']:
                    val = kwargs.get(key)
                    self.sample_data[key][s_ix] = np.NaN
                kwargs.setdefault('spectrum', self)
                sample = self._build_sample(**kwargs)
                self.samples[f] = sample
        self.set_data_updated()
        return sample
    def add_sample_set(self, frequencies, iq=None, powers=None, **kwargs):
        with self.data_update_lock:
            self._add_sample_set(frequencies, iq, powers, **kwargs)
        self.set_data_updated()
    def _add_sample_set(self, frequencies, iq=None, powers=None, **kwargs):
        force_lower_freq = kwargs.get('force_lower_freq')
        if iq is not None:
            powers = np.abs(iq)
        else:
            iq = np.zeros(powers.size, dtype=np.complex128)

        sdata = self.sample_data

        if not force_lower_freq and sdata['frequency'].size:
            r_ix = np.flatnonzero(np.greater_equal(frequencies, [sdata['frequency'].max()]))
            frequencies = frequencies[r_ix]
            iq = iq[r_ix]
            powers = powers[r_ix]

        nin_ix = np.flatnonzero(np.in1d(frequencies, sdata['frequency'], invert=True))

        if nin_ix.size:
            a = np.zeros(nin_ix.size, dtype=sdata.dtype)
            a['frequency'] = frequencies[nin_ix]
            sdata = np.append(sdata, a)
            sdata = np.sort(sdata, order='frequency')
        ix = np.searchsorted(sdata['frequency'], frequencies)
        sdata['iq'][ix] = iq
        sdata['magnitude'][ix] = powers
        self.sample_data = sdata

        kwargs = {'spectrum':self, 'init_complete':True}
        for f in frequencies:
            if f in self.samples:
                continue
            kwargs['frequency'] = f
            sample = self._build_sample(**kwargs)
            self.samples[f] = sample
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
    def save_to_dbstore(self):
        db_store.add_scan(self)
    def update_dbstore(self, *attrs):
        if self.eid is None:
            return
        if not len(attrs):
            attrs = ['name', 'color', 'timestamp_utc', 'step_size',
                     'center_frequencies', 'scan_config_eid']
        d = {attr:getattr(self, attr) for attr in attrs}
        db_store.update_scan(self.eid, **d)
    @classmethod
    def from_dbstore(cls, dbdata=None, eid=None):
        if dbdata is None:
            assert eid is not None
            dbdata = db_store.get_scan(eid)
        else:
            eid = dbdata.eid
        return cls.from_json(dbdata, eid=eid)
    def _serialize(self):
        attrs = ['name', 'color', 'timestamp_utc', 'step_size',
                 'center_frequencies', 'scan_config_eid']
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
