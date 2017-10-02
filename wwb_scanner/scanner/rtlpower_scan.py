import subprocess
import shlex

import numpy as np

from rtlsdr import RtlSdr

from wwb_scanner.scanner.main import ScannerBase, hz_to_mhz, mhz_to_hz

class RtlPowerScanner(ScannerBase):
    @property
    def device_index(self):
        i = getattr(self, '_device_index', None)
        if i is None:
            serial_number = self.device_config.serial_number
            if serial_number is None:
                i = 0
            else:
                i = RtlSdr.get_device_index_by_serial(serial_number)
            self._device_index = i
        return i
    def run_scan(self):
        self.rtl_bin_size_hz = mhz_to_hz(self.sampling_config.rtl_bin_size)
        self.rtl_gain = self.device_config.gain# / 10.

        cmd_str = [
            'rtl_power -i 1 -d {self.device_index}',
            '-f {self.config.scan_range[0]}M:{self.config.scan_range[1]}M:{self.rtl_bin_size_hz}',
            '-g {self.rtl_gain} -w {self.sampling_config.window_type}',# -i {self.integration_interval}',
            '-c {self.sampling_config.rtl_crop}% -F {self.sampling_config.rtl_fir_size}',
            '-1 -',
        ]
        cmd_str = ' '.join(cmd_str).format(self=self)
        print(cmd_str)
        proc = self.proc = subprocess.Popen(
            shlex.split(cmd_str),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
        )
        spectrum = self.spectrum
        while True:
            line = proc.stdout.readline().strip()
            if not line and proc.poll() is not None:
                break
            values = line.split(',')
            if len(values) < 6:
                print(line)
                continue
            f_lo = hz_to_mhz(float(values[2]))
            f_hi = hz_to_mhz(float(values[3]))
            step = hz_to_mhz(float(values[4]))

            dbvals = np.array([float(v) for v in values[6:]])
            freqs = np.linspace(f_lo, f_hi, dbvals.size)
            spectrum.add_sample_set(frequency=freqs, dbFS=dbvals)
        self._running.clear()
        self._stopped.set()
        self.progress = 1.
