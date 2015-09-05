from wwb_scanner.utils.config import Config

class ScanConfig(Config):
    DEFAULTS = dict(
        scan_range=[400., 900.],
        step_size=.05,
        save_raw_values=False,
    )
    def __init__(self, initdict=None, **kwargs):
        kwargs.setdefault('_child_conf_keys', ['device', 'sampling'])
        super(ScanConfig, self).__init__(initdict, **kwargs)
        if 'device' not in self._data:
            self['device'] = DeviceConfig()
        if 'sampling' not in self._data:
            self['sampling'] = SamplingConfig()
    def _deserialize_child(self, key, val, cls=None):
        if key == 'device':
            cls = DeviceConfig
        elif key == 'sampling':
            cls = SamplingConfig
        return super(ScanConfig, self)._deserialize_child(key, val, cls)
    
class DeviceConfig(Config):
    DEFAULTS = dict(
        gain=30., 
        freq_correction=0, 
        is_remote=False, 
        remote_hostname='127.0.0.1', 
        remote_port=1235, 
    )
    
class SamplingConfig(Config):
    DEFAULTS = dict(
        sample_rate=2e6,
        sampling_period=.0125,
        samples_per_scan=None, 
        windows_size=None, 
        window_type='boxcar', 
    )
