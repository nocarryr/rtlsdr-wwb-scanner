import threading

from rtlsdr import RtlSdr

class SdrWrapper(object):
    def __init__(self, **kwargs):
        self.sdr = None
        self.sample_rate = kwargs.get('sample_rate')
        self.bandwidth = kwargs.get('bandwidth')
        self.gain = kwargs.get('gain')
        self.timeout = kwargs.get('timeout', 60.)
        self.device_open = threading.Event()
        self.device_wait = threading.Event()
    def open_sdr(self):
        if self.sdr is not None:
            if self.sdr.device_opened:
                return self.sdr
            else:
                self.sdr = None
                self.device_open.clear()
        try:
            sdr = RtlSdr()
        except IOError:
            if self.timeout is None:
                raise
            sdr = None
        if sdr is None:
            self.device_wait(self.timeout)
            sdr = RtlSdr()
        self.sdr = sdr
        if self.sample_rate is not None:
            sdr.sample_rate = self.sample_rate
        if self.bandwidth is not None:
            sdr.set_bandwidth(self.bandwidth)
        if self.gain is not None:
            sdr.gain = self.gain
        self.device_open.set()
        return sdr
    def close_sdr(self):
        if self.sdr is None:
            return
        self.sdr.close()
        self.sdr = None
        self.device_open.clear()
    def __enter__(self):
        if self.device_open.is_set():
            return
        self.open_sdr()
    def __exit__(self, *args):
        self.close_sdr()
    
