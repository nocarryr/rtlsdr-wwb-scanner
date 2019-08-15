import sys
import base64
import json
import pickle

import numpy as np

PY3 = sys.version_info.major >= 3

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
            if PY3:
                if not isinstance(data, bytes):
                    data = bytes(data, 'UTF-8')
                return pickle.loads(data, encoding='bytes')
            return pickle.loads(data)
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
