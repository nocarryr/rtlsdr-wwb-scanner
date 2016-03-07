import base64
import json
import numpy as np

## From http://stackoverflow.com/questions/27909658/

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            data_b64 = base64.b64encode(obj.dumps())
            return dict(__ndarray__=data_b64)
        return json.JSONEncoder.default(self, obj)

def json_numpy_obj_hook(dct):
    if isinstance(dct, dict) and '__ndarray__' in dct:
        data = base64.b64decode(dct['__ndarray__'])
        return np.loads(data)
    return dct

def dumps(*args, **kwargs):
    kwargs.setdefault('cls', NumpyEncoder)
    return json.dumps(*args, **kwargs)

def loads(*args, **kwargs):
    kwargs.setdefault('object_hook', json_numpy_obj_hook)
    return json.loads(*args, **kwargs)

def dump(*args, **kwargs):
    kwargs.setdefault('cls', NumpyEncoder)
    return json.dump(*args, **kwargs)

def load(*args, **kwargs):
    kwargs.setdefault('object_hook', json_numpy_obj_hook)
    return json.load(*args, **kwargs)
