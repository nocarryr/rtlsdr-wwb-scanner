import os

import pytest
import numpy as np
from scipy import signal

@pytest.fixture
def random_samples():
    def gen(n=1024):
        a = np.random.randint(1, 255, size=n) - 127.5
        a /= 127.5
        iq = signal.hilbert(a)
        return iq
    return gen

@pytest.fixture
def data_files():
    base_path = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_path, 'data')

    files = {}
    for fn in os.listdir(data_dir):
        if os.path.splitext(fn)[1] not in ['.csv', '.sdb2']:
            continue
        s = os.path.splitext(os.path.basename(fn))[0]
        start_freq, end_freq = [float(v) for v in s.split('-')]
        fkey = (start_freq, end_freq)
        skey = os.path.splitext(fn)[1].strip('.')
        if fkey not in files:
            files[fkey] = {}
        files[fkey][skey] = os.path.join(data_dir, fn)

    return files
