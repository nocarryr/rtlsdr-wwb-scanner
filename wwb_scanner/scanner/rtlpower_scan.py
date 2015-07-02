import subprocess

from wwb_scanner.scanner.main import ScannerBase, hz_to_mhz

class RtlPowerScanner(ScannerBase):
    def run_scan(self):
        cmd_str = 'rtl_power -f %fM:%fM:%fM -g %s -1 -'
        cmd_str = cmd_str % (
            self.scan_range[0], 
            self.scan_range[1], 
            self.step_size, 
            self.gain, 
        )
        self.result = subprocess.check_output(cmd_str, shell=True)
        spectrum = self.spectrum
        for line in self.result.splitlines():
            values = line.split(',')
            f = hz_to_mhz(float(values[2]))
            step = hz_to_mhz(float(values[4]))
            for p in values[6:]:
                spectrum.add_sample(frequency=f, magnitude=float(p))
                f += step
