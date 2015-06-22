from wwb_scanner.scan_objects import Spectrum

class BaseImporter(object):
    def __init__(self, **kwargs):
        self.spectrum = Spectrum()
        self.filename = kwargs.get('filename')
    def __call__(self):
        self.file_data = self.load_file()
        self.parse_file_data()
        return self.spectrum
    def load_file(self):
        with open(self.filename, 'r') as f:
            s = f.read()
        return s
    def parse_file_data(self):
        raise NotImplementedError('Method must be implemented by subclasses')
    
class CSVImporter(BaseImporter):
    delimiter_char = ','
    def parse_file_data(self):
        spectrum = self.spectrum
        for line in self.file_data.splitlines():
            line = line.rstrip('\n').rstrip('\r')
            if ',' not in line:
                continue
            f, v = line.split(',')
            spectrum.add_sample(frequency=float(f), magnitude=float(v))
            
