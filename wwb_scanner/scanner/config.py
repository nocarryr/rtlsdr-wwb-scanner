from wwb_scanner.utils.config import Config

class ScanConfig(Config):
    SCAN_DEFAULTS = dict(
        scan_range=[400., 900.],
        step_size=.05,
        sample_rate=2e6,
        sampling_period=.0125,
        save_raw_values=False,
        gain=30.,
        freq_correction=0, 
        is_remote=False, 
        remote_hostname='127.0.0.1', 
        remote_port=1235, 
    )
    def __init__(self, initdict=None, **kwargs):
        super(ScanConfig, self).__init__(initdict, **kwargs)
        for key, val in self.SCAN_DEFAULTS.items():
            self.setdefault(key, val)
    
