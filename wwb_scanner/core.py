from wwb_scanner.utils import numpyjson as json

class JSONMixin(object):
    _serialization_attrs = []
    def _get_serialization_attrs(self):
        inst_attrs = self._serialization_attrs
        cls_attrs = getattr(self.__class__, '_serialization_attrs', None)
        if inst_attrs is not cls_attrs and type(inst_attrs) is set:
            return inst_attrs
        def cls_iter(cls):
            _cls_iter = (c for c in (cls,) + cls.__bases__)
            _cls = cls
            while True:
                try:
                    next_cls = next(_cls_iter)
                    print next_cls
                except StopIteration:
                    if _cls is cls:
                        _cls_iter = cls_iter(_cls)
                        _cls = None
                    else:
                        _cls_iter = None
                    next_cls = None
                if next_cls is not None:
                    yield next_cls
                if _cls_iter is None:
                    break
        attrs = self._serialization_attrs = set()
        for cls in cls_iter(self.__class__):
            if not hasattr(cls, '_serialization_attrs'):
                continue
            attrs |= set(cls._serialization_attrs)
        return attrs
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
        attrs = self._get_serialization_attrs()
        return {attr: getattr(self, attr) for attr in attrs}
    def _deserialize(self, **kwargs):
        attrs = self._get_serialization_attrs()
        for attr in attrs:
            val = kwargs.get(attr)
            if getattr(self, attr, None) != val:
                setattr(self, attr, val)
