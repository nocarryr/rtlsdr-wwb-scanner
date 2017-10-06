from wwb_scanner.utils.config import Config

class ScanConfig(Config):
    DEFAULTS = dict(
        scan_range=[400., 900.],
        save_raw_values=False,
    )
    def __init__(self, initdict=None, **kwargs):
        kwargs.setdefault('_child_conf_keys', ['device', 'sampling', 'processing'])
        super(ScanConfig, self).__init__(initdict, **kwargs)
        if 'device' not in self._data:
            self['device'] = DeviceConfig()
        if 'sampling' not in self._data:
            self['sampling'] = SamplingConfig()
        if 'processing' not in self._data:
            self['processing'] = ProcessingConfig()
    def _deserialize_child(self, key, val, cls=None):
        if key == 'device':
            cls = DeviceConfig
        elif key == 'sampling':
            cls = SamplingConfig
        elif key == 'processing':
            cls = ProcessingConfig
        return super(ScanConfig, self)._deserialize_child(key, val, cls)

class DeviceConfig(Config):
    DEFAULTS = dict(
        serial_number=None,
        gain=30.,
        freq_correction=0,
        is_remote=False,
        remote_hostname='127.0.0.1',
        remote_port=1235,
    )

class SamplingConfig(Config):
    DEFAULTS = dict(
        sample_rate=2.048e6,
        sweep_overlap_ratio=.5,
        sweeps_per_scan=20,
        samples_per_sweep=8192,
        window_size=None,
        fft_size=1024,
        window_type='boxcar',
        rtl_bin_size=0.025,
        rtl_crop=50,
        rtl_fir_size=4,
    )

class ProcessingConfig(Config):
    DEFAULTS = dict(
        smoothing_enabled=False,
        smoothing_factor=1.,
        scaling_enabled=True,
        scaling_min_db=-140.,
        scaling_max_db=-50.,
    )
