from wwb_scanner.utils import numpyjson as json

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
