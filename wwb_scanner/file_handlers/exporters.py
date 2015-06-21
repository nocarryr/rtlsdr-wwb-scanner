import os
import datetime
import uuid
import xml.etree.ElementTree as ET

EPOCH = datetime.datetime(1970, 1, 1)

class BaseExporter(object):
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
        self.set_filename(value)
    def set_filename(self, value):
        if value == self.filename:
            return
        self._filename = value
    def build_data(self):
        raise NotImplementedError('Method must be implemented by subclasses')
    def write_file(self):
        s = self.build_data()
        with open(self.filename, 'w') as f:
            f.write(s)
        
class CSVExporter(BaseExporter):
    newline_chars = '\r\n'
    delimiter_char = ','
    def set_filename(self, value):
        if os.path.splitext(value)[1] == '.CSV':
            value = '.'.join([os.path.splitext(value)[0], 'csv'])
        super(CSVExporter, self).set_filename(value)
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
        
class WWBLegacyExporter(BaseExporter):
    def set_filename(self, value):
        if os.path.splitext(value[1]).lower() != '.sbd':
            value = '.'.join([os.path.splitext(value)[0], 'sbd'])
        super(WWBLegacyExporter, self).set_filename(value)
    def build_data(self):
        spectrum = self.spectrum
        now = datetime.datetime.utcnow()
        attribs = dict(
            ver='0.0.0.1', 
            id='{%s}' % (uuid.uuid4()), 
            model='TODO', 
            name='Rtlsdr WWB Scanner', 
            date=now.strftime('%a %b %d %Y'), 
            time=now.strftime('%H:%M:%S'), 
            color='#00ff00',
        )
        root = ET.Element('scan_data_source', attribs)
        attribs = dict(
            count='1', 
            no_data_value='-140', 
        )
        data_sets = ET.SubElement(root, 'data_sets', attribs)
        attribs = dict(
            index='0', 
            freq_units='KHz', 
            ampl_units='dBm', 
            start_freq=min(spectrum.samples.keys()), 
            stop_freq=max(spectrum.samples.keys()), 
            step_freq=spectrum.step_size, 
            res_bandwidth='TODO', 
            scale_factor='1', 
            date=root.get('date'), 
            time=root.get('time'), 
            date_time=str(int((now - EPOCH).total_seconds())), 
        )
        data_set = ET.SubElement(data_sets, 'data_set', attribs)
        for sample in spectrum.iter_samples():
            ET.SubElement(data_set, text=sample.formatted_magnitude)
        tree = self.tree = ET.ElementTree(root)
        return tree
    def write_file(self):
        tree = self.build_data()
        tree.write(self.filename, encoding='UTF-8', xml_declaration=True)
        
