from wwb_scanner.core import JSONMixin

class Config(JSONMixin):
    def __init__(self, initdict=None, **kwargs):
        data = {}
        if initdict is not None:
            data.update(initdict)
        data.update(kwargs)
        if '__from_json__' in data:
            del data['__from_json__']
        if hasattr(self, 'DEFAULTS'):
            for key, val in self.DEFAULTS.items():
                data.setdefault(key, val)
        self._config_keys = set(data.keys())
        self._child_conf_keys = set(data.get('_child_conf_keys', []))
        self._data = {}
        for key, val in data.items():
            if key == '_child_conf_keys':
                continue
            self[key] = val
    def __setitem__(self, key, item):
        if key in self._child_conf_keys:
            if not isinstance(item, Config):
                item = self._deserialize_child(key, item)
        elif isinstance(item, Config):
            self._child_conf_keys.add(key)
        self._data[key] = item
        self._config_keys.add(key)
    def __getitem__(self, key):
        return self._data[key]
    def __delitem__(self, key):
        del self._data[key]
        self._config_keys.discard(key)
        self._child_conf_keys.discard(key)
    def get(self, key, default=None):
        return self._data.get(key, default)
    def setdefault(self, key, default):
        self._config_keys.add(key)
        return self._data.setdefault(key, default)
    def update(self, other):
        for key, val in other.items():
            self[key] = val
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
        if attr not in ['_config_keys', '_child_conf_keys', '_data']:
            self[attr] = value
        else:
            super(Config, self).__setattr__(attr, value)
    def _serialize(self):
        keys = self._config_keys - self._child_conf_keys
        d = {k:self._data.get(k) for k in keys}
        d['_child_conf_keys'] = list(self._child_conf_keys)
        for key in self._child_conf_keys:
            d[key] = self[key]._serialize()
        return d
    def _deserialize_child(self, key, data, cls=None):
        if cls is None:
            cls = Config
        return cls(data)
