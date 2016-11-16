import time
import numbers
import numpy as np

from wwb_scanner.core import JSONMixin

class Sample(JSONMixin):
    def __init__(self, **kwargs):
        self.spectrum = kwargs.get('spectrum')
        self.frequency = kwargs.get('frequency')
        self.iq = kwargs.get('iq')
        self.magnitude = kwargs.get('magnitude')
        self.power = kwargs.get('power')
        self.dbFS = kwargs.get('dbFS')
    @property
    def frequency(self):
        return getattr(self, '_frequency', None)
    @frequency.setter
    def frequency(self, value):
        if not isinstance(value, numbers.Number):
            return
        if self.frequency == value:
            return
        if not isinstance(value, float):
            value = float(value)
        self._frequency = value
    @property
    def iq(self):
        return getattr(self, '_iq', None)
    @iq.setter
    def iq(self, value):
        old = self.iq
        if old == value:
            return
        if isinstance(value, (list, tuple)):
            i, q = value
            value = np.complex128(float(i) + 1j*float(q))
        self._iq = value
        self.spectrum.on_sample_change(sample=self, iq=value, old=old)
    @property
    def magnitude(self):
        m = getattr(self, '_magnitude', None)
        if m is None and self.iq is not None:
            m = np.abs(self.iq)
        return m
    @magnitude.setter
    def magnitude(self, value):
        if not isinstance(value, numbers.Number):
            return
        old = self.magnitude
        if old == value:
            return
        if not isinstance(value, float):
            value = float(value)
        self._magnitude = value
        self.spectrum.on_sample_change(sample=self, magnitude=value, old=old)
    @property
    def dbFS(self):
        db = getattr(self, '_dbFS', None)
        if db is None:
            m = self.magnitude
            if m is not None:
                db = 10. * np.log10(m)
        return db
    @dbFS.setter
    def dbFS(self, value):
        old = self.dbFS
        if old == value:
            return
        self._dbFS = value
        self.spectrum.on_sample_change(sample=self, dbFS=value, old=old)
    @property
    def formatted_frequency(self):
        return '%07.4f' % (self.frequency)
    @property
    def formatted_magnitude(self):
        return '%03.1f' % (self.magnitude)
    @property
    def formatted_dbFS(self):
        return '%03.1f' % (self.dbFS)
    def _serialize(self):
        d = {'frequency':self.frequency}
        if self.iq is not None:
            d['iq'] = (str(self.iq.real), str(self.iq.imag))
        elif self.magnitude is not None:
            d['magnitude'] = self.magnitude
        else:
            d['dbFS'] = self.dbFS
        return d
    def __repr__(self):
        return str(self)
    def __str__(self):
        return '%s (%s dB)' % (self.formatted_frequency, self.dbFS)

class TimeBasedSample(Sample):
    def __init__(self, **kwargs):
        ts = kwargs.get('timestamp')
        if ts is None:
            ts = time.time()
        self.timestamp = ts
        super(TimeBasedSample, self).__init__(**kwargs)
