import numpy as np


class SampleArray(object):
    dtype = np.dtype([
        ('frequency', np.float64),
        ('iq', np.complex128),
        ('magnitude', np.float64),
        ('dbFS', np.float64)
    ])
    def __init__(self, data=None, keep_sorted=True):
        self.keep_sorted = keep_sorted
        if data is None:
            data = np.empty([0], dtype=self.dtype)
        self.data = data
        if keep_sorted:
            self.data = np.sort(self.data, order='frequency')
    @classmethod
    def create(cls, keep_sorted=True, **kwargs):
        obj = cls(keep_sorted=keep_sorted)
        obj.set_fields(**kwargs)
        return obj
    def set_fields(self, **kwargs):
        f = kwargs.get('frequency')
        if f is None:
            raise Exception('frequency array must be provided')
        if not isinstance(f, np.ndarray):
            f = np.array([f])
        data = np.zeros(f.size, dtype=self.dtype)
        data['frequency'] = f
        for key, val in kwargs.items():
            if key not in self.dtype.fields:
                continue
            if key == 'frequency':
                continue
            if not isinstance(val, np.ndarray):
                val = np.array([val])
            data[key] = val

        if data is None:
            return

        iq = kwargs.get('iq')
        mag = kwargs.get('magnitude')
        dbFS = kwargs.get('dbFS')

        if iq is not None and mag is None:
            mag = data['magnitude'] = np.abs(data['iq'])
        if dbFS is not None and mag is None:
            mag = data['magnitude'] = 10 ** (data['dbFS'] / 10)
        if mag is not None and dbFS is None:
            data['dbFS'] = 10 * np.log10(data['magnitude'])

        self.append(data)
    def __getattr__(self, attr):
        if attr in self.dtype.fields.keys():
            return self.data[attr]
        raise AttributeError
    def __setattr__(self, attr, val):
        if attr in self.dtype.fields.keys():
            self.data[attr] = val
        super(SampleArray, self).__setattr__(attr, val)
    def __getitem__(self, key):
        return self.data[key]
    def __setitem__(self, key, value):
        self.data[key] = value
    def __len__(self):
        return len(self.data)
    def __iter__(self):
        return iter(self.data)
    @property
    def size(self):
        return self.data.size
    @property
    def shape(self):
        return self.data.shape
    def _check_obj_type(self, other):
        if isinstance(other, SampleArray):
            data = other.data
        else:
            if isinstance(other, np.ndarray) and other.dtype == self.dtype:
                data = other
            else:
                raise Exception('Cannot extend this object type: {}'.format(other))
        return data
    def append(self, other):
        if self.keep_sorted:
            self.insert_sorted(other)
        else:
            data = self._check_obj_type(other)
            self.data = np.append(self.data, data)
    def insert_sorted(self, other):
        data = self._check_obj_type(other)
        nin_ix = np.flatnonzero(np.in1d(data['frequency'], self.frequency, invert=True))

        if nin_ix.size:
            d = np.append(self.data, data[nin_ix])
            d = np.sort(d, order='frequency')
            self.data = d
        ix = np.searchsorted(self.frequency, data['frequency'])
        self.iq[ix] = data['iq']
        self.magnitude[ix] = data['magnitude']
        self.dbFS[ix] = data['dbFS']
    def __repr__(self):
        return '<{self.__class__.__name__}: {self}>'.format(self=self)
    def __str__(self):
        return str(self.data)
