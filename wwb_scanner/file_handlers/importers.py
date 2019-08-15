import os.path
import datetime
import xml.etree.ElementTree as ET
import itertools

import numpy as np

from wwb_scanner.scan_objects import Spectrum

class BaseImporter(object):
    def __init__(self, **kwargs):
        self.spectrum = Spectrum()
        self.filename = kwargs.get('filename')
    @classmethod
    def import_file(cls, filename):
        ext = os.path.splitext(filename)[1].strip('.').lower()
        def find_importer(_cls):
            if getattr(_cls, '_extension', None) == ext:
                return _cls
            for _subcls in _cls.__subclasses__():
                r = find_importer(_subcls)
                if r is not None:
                    return r
            return None
        cls = find_importer(BaseImporter)
        fh = cls(filename=filename)
        return fh()
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
    _extension = 'csv'
    def parse_file_data(self):
        spectrum = self.spectrum
        spectrum.name = os.path.basename(self.filename)
        def iter_lines():
            for line in self.file_data.splitlines():
                line = line.rstrip('\n').rstrip('\r')
                if ',' not in line:
                    continue
                f, v = line.split(',')
                yield float(f)
                yield float(v)
        a = np.fromiter(iter_lines(), dtype=np.float64)
        freqs = a[::2]
        dB = a[1::2]
        spectrum.add_sample_set(frequency=freqs, dbFS=dB)

class BaseWWBImporter(BaseImporter):
    def load_file(self):
        return ET.parse(self.filename)

class WWBImporter(BaseWWBImporter):
    _extension = 'sdb2'
    def parse_file_data(self):
        spectrum = self.spectrum
        root = self.file_data.getroot()
        color = root.get('color')
        if color is not None:
            spectrum.color = spectrum.color.from_hex(color)
        freq_set = root.find('*/freq_set')
        data_set = root.find('*/data_set')
        ts = data_set.get('date_time')
        if ts is not None:
            try:
                spectrum.timestamp_utc = float(ts)
            except ValueError:
                spectrum.timestamp_utc = float(ts) / 1000.
        else:
            dt_str = ' '.join([root.get('date'), root.get('time')])
            dt_fmt = '%a %b %d %Y %H:%M:%S'
            dt = datetime.datetime.strptime(dt_str, dt_fmt)
            spectrum.datetime_utc = dt
        freqs = np.fromiter((float(t.text) / 1000. for t in freq_set), dtype=np.float)
        dB = np.fromiter((float(t.text) for t in data_set), dtype=np.float64)
        spectrum.add_sample_set(frequency=freqs, dbFS=dB)
