import datetime

import jsonfactory

from wwb_scanner.utils import numpyjson as json

try:
    basestring = basestring
except NameError:
    basestring = str

class JSONMixin(object):
    @classmethod
    def from_json(cls, data, **kwargs):
        if isinstance(data, basestring):
            data = json.loads(data)
        kwargs.update(data)
        kwargs['__from_json__'] = True
        obj = cls(**kwargs)
        obj._deserialize(**kwargs)
        return obj
    def instance_from_json(self, data, **kwargs):
        if isinstance(data, basestring):
            data = json.loads(data)
        kwargs.update(data)
        self._deserialize(**kwargs)
    def to_json(self, **kwargs):
        d = self._serialize()
        return json.dumps(d, **kwargs)
    def _serialize(self):
        raise NotImplementedError('method must be implemented by subclasses')
    def _deserialize(self, **kwargs):
        pass

@jsonfactory.register
class JSONEncoder(object):
    _dt_fmt = '%Y-%m-%dT%H:%M:%S.%f %z'
    def encode(self, o):
        if isinstance(o, datetime.datetime):
            return {'__datetime.datetime__':o.strftime(self._dt_fmt)}
        return None
    def decode(self, d):
        if '__datetime.datetime__' in d:
            s = d['__datetime.datetime__']
            fmt = self._dt_fmt
            if s.endswith(' '):
                s = s.strip(' ')
                fmt = fmt.split(' ')[0]
            return datetime.datetime.strptime(s, fmt)
        return d
