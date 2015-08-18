from wwb_scanner.core import JSONMixin

class ScanConfig(JSONMixin):
    SCAN_DEFAULTS = dict(
        scan_range=[400., 900.],
        step_size=.05,
        sample_rate=2e6,
        sampling_period=.0125,
        save_raw_values=False,
        gain=30.,
        freq_correction=0, 
    )
    def __init__(self, initdict=None, **kwargs):
        data = {}
        if initdict is not None:
            data.update(initdict)
        data.update(kwargs)
        if '__from_json__' in data:
            del data['__from_json__']
        for key, val in self.SCAN_DEFAULTS.items():
            data.setdefault(key, val)
        self._config_keys = set(data.keys())
        self._data = data
    def __setitem__(self, key, item):
        self._data[key] = item
        self._config_keys.add(key)
    def __getitem__(self, key):
        return self._data[key]
    def __delitem__(self, key):
        del self._data[key]
        self._config_keys.discard(key)
    def get(self, key, default=None):
        return self._data.get(key, default)
    def setdefault(self, key, default):
        self._config_keys.add(key)
        return self._data.setdefault(key, default)
    def update(self, other):
        self._data.update(other)
        self._config_keys |= set(other.keys())
    def keys(self):
        return self._data.keys()
    def values(self):
        return self._data.values()
    def items(self):
        return self._data.items()
    def __getattr__(self, attr):
        if hasattr(self, '_data') and attr in self._config_keys:
            return self[attr]
        raise AttributeError
    def __setattr__(self, attr, value):
        if attr not in ['_config_keys', '_data']:
            self[attr] = value
        else:
            super(ScanConfig, self).__setattr__(attr, value)
    def _serialize(self):
        return self._data
