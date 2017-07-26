import base64
import json

import numpy as np

import jsonfactory

## From http://stackoverflow.com/questions/27909658/

@jsonfactory.register
class NumpyEncoder(object):
    def encode(self, obj):
        if isinstance(obj, np.ndarray):
            data_b64 = base64.b64encode(obj.dumps())
            if isinstance(data_b64, bytes):
                data_b64 = data_b64.decode('UTF-8')
            return dict(__ndarray__=data_b64)
        return None
    def decode(self, d):
        if '__ndarray__' in d:
            data = base64.b64decode(d['__ndarray__'])
            return np.loads(data)
        return d

def dumps(obj, **kwargs):
    return jsonfactory.dumps(obj, **kwargs)

def loads(s, **kwargs):
    return jsonfactory.loads(s, **kwargs)

def dump(*args, **kwargs):
    kwargs.setdefault('cls', jsonfactory.Encoder)
    return json.dump(*args, **kwargs)

def load(*args, **kwargs):
    kwargs.setdefault('object_hook', jsonfactory.obj_hook)
    return json.load(*args, **kwargs)
