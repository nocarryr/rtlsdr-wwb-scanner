import threading

from rtlsdr import RtlSdr

class SdrWrapper(object):
    def __init__(self, **kwargs):
        self.sdr = None
        self.scanner = kwargs.get('scanner')
        self.timeout = kwargs.get('timeout', 60.)
        self.device_open = threading.Event()
        self.device_wait = threading.Event()
    def set_sdr_values(self):
        scanner = self.scanner
        if scanner is None:
            return
        sdr = self.sdr
        if sdr is None:
            return
        keys = ['sample_rate', 'gain', 'bandwidth']
        scanner_vals = {key: getattr(scanner, key, None) for key in keys}
        for key, scanner_val in scanner_vals.items():
            if key == 'gain':
                sdr_val = None
            else:
                sdr_val = getattr(sdr, key)
            if sdr_val == scanner_val:
                continue
            setattr(sdr, key, scanner_val)
            if key == 'gain' and scanner_val == 0:
                sdr_val = 0.
            else:
                sdr_val = getattr(sdr, key)
            if sdr_val != scanner_val:
                setattr(scanner, key, sdr_val)
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
        self.set_sdr_values()
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
    
