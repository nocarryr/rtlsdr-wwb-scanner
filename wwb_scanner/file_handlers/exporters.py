import os

class CSVExporter(object):
    newline_chars = '\r\n'
    delimiter_char = ','
    def __init__(self, **kwargs):
        self.spectrum = kwargs.get('spectrum')
        self.filename = kwargs.get('filename')
    @property
    def filename(self):
        return getattr(self, '_filename', None)
    @filename.setter
    def filename(self, value):
        if value is None:
            return 
        if os.path.splitext(value)[1] == '.CSV':
            value = '.'.join([os.path.splitext(value)[0], 'csv'])
        if value == self.filename:
            return
        self._filename = value
    def build_data(self):
        newline_chars = self.newline_chars
        delim = self.delimiter_char
        lines = []
        for sample in self.spectrum.iter_samples():
            lines.append(delim.join([
                sample.formatted_frequency, 
                sample.formatted_magnitude
            ]))
        return newline_chars.join(lines)
    def write_file(self):
        s = self.build_data()
        with open(self.filename, 'w') as f:
            f.write(s)
        
