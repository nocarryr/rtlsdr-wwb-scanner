from __future__ import annotations
from typing import NamedTuple
from dataclasses import dataclass
import os.path
import datetime
import xml.etree.ElementTree as ET
import itertools
import json

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

class NumpyImporter(BaseImporter):
    _extension = 'npz'
    def __call__(self):
        data = np.load(self.filename)
        spectrum = self.spectrum
        spectrum.name = os.path.basename(self.filename)
        spectrum.add_sample_set(data=data['sample_data'])
        return spectrum


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
        name = root.get('name')
        if name is not None:
            spectrum.name = name
        freq_set = root.find('*/freq_set')
        data_set = root.find('*/data_set')
        ts = data_set.get('date_time')
        if ts is not None:
            spectrum.timestamp_utc = float(ts) / 1000.
        else:
            dt_str = ' '.join([root.get('date'), root.get('time')])
            dt_fmt = '%a %b %d %Y %H:%M:%S'
            dt = datetime.datetime.strptime(dt_str, dt_fmt)
            spectrum.datetime_utc = dt
        freqs = np.fromiter((float(t.text) / 1000. for t in freq_set), dtype=np.float64)
        dB = np.fromiter((float(t.text) for t in data_set), dtype=np.float64)
        spectrum.add_sample_set(frequency=freqs, dbFS=dB)


class WWB7Importer(BaseImporter):
    _extension = 'sdb3'

    def load_file(self):
        with open(self.filename, 'rb') as f:
            s = f.read()
        return s

    def parse_file_data(self):
        params = SDB3ScanParams.parse(self.file_data)
        data = parse_sdb3_binary(params, self.file_data)
        spectrum = self.spectrum
        data['freqs'] /= 1e6
        spectrum.add_sample_set(frequency=data['freqs'], dbFS=data['values'])
        spectrum.timestamp_utc = params.scan_datetime.timestamp()
        spectrum.name = params.title
        spectrum.color = spectrum.color.from_hex(params.color)



class SDB3ByteDef(NamedTuple):
    num_bytes: int
    data_value: str


class FrequencyRange(NamedTuple):
    start: int
    stop: int
    step: int

    @property
    def num_freqs(self) -> int:
        return ((self.stop - self.start) // self.step) + 1

    def build_freq_array(self) -> np.ndarray:
        return np.arange(self.start, self.stop+self.step, self.step)


class FrequencyUnit(NamedTuple):
    name: str
    multiplier: int

    @classmethod
    def create(cls, name: str) -> FrequencyUnit:
        _name = name.lower()
        assert _name.endswith('hz')
        multiplier = {'hz':1, 'khz':1e3, 'mhz':1e6}[_name]
        return cls(name, int(multiplier))


@dataclass
class SDB3BinarySchema:
    byte_values: list[SDB3ByteDef]
    start_of_sweep: int
    color: str
    freq_range: FrequencyRange
    resolution_bandwidth: int
    @classmethod
    def parse(cls, data: list[dict]) -> SDB3BinarySchema:
        kw = {'byte_values':[]}
        for item in data:
            if 'Bytes' in item:
                bdef = SDB3ByteDef(item['Bytes'], item['DataValue'])
                if bdef.data_value == 'start-of-sweep':
                    kw['start_of_sweep'] = bdef.num_bytes
                kw['byte_values'].append(bdef)
            elif 'Curve' in item:
                c = item['Curve']
                kw['color'] = c['Color']
                kw['resolution_bandwidth'] = c['ResolutionBandWidth']
                if len(c['FreqRanges']) != 1:
                    raise ValueError("More than one frequency range.  I wasn't expecting that")
                d = c['FreqRanges'][0]
                kw['freq_range'] = FrequencyRange(
                    start=d['StartFreq'], stop=d['EndFreq'], step=d['StepFreq'],
                )
        return cls(**kw)

    @property
    def num_freqs(self) -> int:
        return self.freq_range.num_freqs

    def build_freq_array(self) -> np.ndarray:
        return self.freq_range.build_freq_array()


@dataclass
class SDB3ScanParams:
    amplitude_units: str
    binary_schema: SDB3BinarySchema
    bit_width: int
    freq_units: FrequencyUnit
    no_data_value: int
    scale_factor: int
    scanner_model: str
    scanner_name: str
    scan_datetime: datetime.datetime
    title: str
    version: str

    @classmethod
    def parse(cls, indata: bytes) -> SDB3ScanParams:
        to_parse = indata.split(b'//@ShureScan')[1]
        to_parse = to_parse.split(b'@Binary:@Swp')[0]
        data = json.loads(to_parse)
        keys = [
            ('amplitude_units', 'AmplUnits'),
            ('bit_width', 'BitWidth'),
            ('no_data_value', 'NoDataValue'),
            ('scale_factor', 'Scale Factor'),
            ('scanner_model', 'ScannerModel'),
            ('scanner_name', 'ScannerName'),
            ('title', 'Title'),
            ('version', 'Version'),
        ]
        kw = {attr:data[key] for attr, key in keys}
        dt_str = f'{data["StartDate"]} {data["StartTime"]}'
        dt_fmt = '%m/%d/%Y %H:%M:%S'
        kw['scan_datetime'] = datetime.datetime.strptime(dt_str, dt_fmt)
        kw['freq_units'] = FrequencyUnit.create(data['FreqUnits'])
        kw['binary_schema'] = SDB3BinarySchema.parse(data['BinarySchema'])
        return cls(**kw)

    @property
    def byte_width(self) -> int:
        return self.bit_width // 8

    @property
    def num_freqs(self) -> int:
        return self.binary_schema.num_freqs

    @property
    def color(self) -> str:
        return self.binary_schema.color

    def build_freq_array(self) -> np.ndarray:
        return self.binary_schema.build_freq_array()


def parse_sdb3_binary(params: SDB3ScanParams, indata: bytes):
    start_str = b'@Binary:@Swp'
    start_offset_bytes = params.binary_schema.start_of_sweep * params.byte_width
    len_bytes = params.num_freqs * params.byte_width
    bin_data = indata.split(start_str)[1]
    bin_data = bin_data[start_offset_bytes:]
    assert len(bin_data) >= len_bytes
    dtype = np.dtype(f'>i{params.byte_width}')
    data = np.frombuffer(bin_data, dtype=dtype, count=params.num_freqs)
    struct_dtype = np.dtype([
        ('freqs', np.float64),
        ('values', np.float64),
    ])
    result = np.zeros(data.size, dtype=struct_dtype)
    result['values'] = data / params.scale_factor
    result['freqs'] = params.build_freq_array() * params.freq_units.multiplier
    return result
