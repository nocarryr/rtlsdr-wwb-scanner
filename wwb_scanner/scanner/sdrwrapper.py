import threading

from rtlsdr import RtlSdr

class SdrWrapper(object):
    def __init__(self, **kwargs):
        self.sdr = None
        self.scanner = kwargs.get('scanner')
        self.enable_scanner_updates = kwargs.get('enable_scanner_updates', True)
        self.device_open = threading.Event()
        self.device_wait = threading.Event()
        self.device_lock = threading.RLock()
    def set_sdr_values(self):
        if not self.enable_scanner_updates:
            return
        scanner = self.scanner
        if scanner is None:
            return
        sdr = self.sdr
        if sdr is None:
            return
        keys = ['sample_rate', 'gain']
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
        with self.device_lock:
            new_sdr = True
            if self.sdr is not None:
                if not self.sdr.device_opened:
                    self.sdr.close()
                    self.sdr = None
                    self.device_open.clear()
                else:
                    self.device_open.wait()
            if self.sdr is not None:
                new_sdr = False
            else:
                try:
                    self.sdr = RtlSdr()
                except IOError:
                    self.sdr = None
                    new_sdr = False
                if new_sdr:
                    self.set_sdr_values()
                    self.device_open.set()
        return self.sdr
    def close_sdr(self):
        with self.device_lock:
            if self.sdr is not None:
                self.sdr.close()
                self.sdr = None
                self.device_open.clear()
    def __enter__(self):
        self.open_sdr()
    def __exit__(self, *args):
        self.close_sdr()
    
