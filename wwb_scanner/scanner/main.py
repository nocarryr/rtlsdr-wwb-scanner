from rtlsdr import RtlSdr

from wwb_scanner.scanner import sample_processing
from wwb_scanner.scan_objects import Spectrum

SCANNER_DEFAULTS = dict(
    scan_range=[400., 900.], 
    step_size=.025, 
    sample_rate=2e6,  
)

def mhz_to_hz(mhz):
    return mhz * 1000000.0
def hz_to_mhz(hz):
    return hz / 1000000.0
    
class Scanner(object):
    '''
        params:
            scan_range: (list) frequency range to scan (in MHz)
            step_size:  increment (in MHz) to return scan values
    '''
    def __init__(self, **kwargs):
        self._current_freq = None
        self._progress = 0.
        for key, val in SCANNER_DEFAULTS.items():
            if key in kwargs:
                val = kwargs.get(key)
            setattr(self, key, val)
        self.spectrum = Spectrum(step_size=self.step_size)
        self.sdr = RtlSdr()
        self.sdr.sample_rate = self.sample_rate
        self.samples_per_scan = sample_processing.calc_num_samples(self.sample_rate)
        self.sample_segment_length = int(self.sample_rate / mhz_to_hz(self.step_size))
    @property
    def current_freq(self):
        return self._current_freq
    @current_freq.setter
    def current_freq(self, value):
        self._current_freq = value
    @property
    def progress(self):
        return self._progress
    @progress.setter
    def progress(self, value):
        value = round(value, 1)
        if value == self._progress:
            return
        self._progress = value
        print '%s%%' % (int(value * 100))
    def run_scan(self):
        freq, end_freq = self.scan_range
        step_size = self.step_size
        num_steps = (end_freq - freq) / step_size
        print 'num_steps=%s' % (num_steps)
        step = 0
        while freq < end_freq:
            self.current_freq = freq
            try:
                self.scan_freq(mhz_to_hz(freq))
            except KeyboardInterrupt:
                break
            freq += step_size
            step += 1
            self.progress = step / num_steps
    def scan_freq(self, freq):
        spectrum = self.spectrum
        freqs, powers = sample_processing.read_samples(self, freq)
        for f, p in zip(freqs, powers):
            f = hz_to_mhz(f)
            spectrum.add_sample(frequency=f, magnitude=p)
