import os

import numpy as np

def test_importers(data_files):
    from wwb_scanner.file_handlers import BaseImporter

    spec = {}
    for fkey, d in data_files.items():
        if fkey not in spec:
            spec[fkey] = {}
        for skey, fn in d.items():
            spectrum = BaseImporter.import_file(fn)
            spec[fkey][skey] = spectrum

    for fkey, d in spec.items():
        start_freq, end_freq = fkey
        for spectrum in d.values():
            freqs = spectrum.sample_data['frequency']
            assert freqs.min() <= start_freq
            assert freqs.max() >= end_freq

def test_exporters(data_files, tmpdir):
    from wwb_scanner.scan_objects import Spectrum

    for fkey, d in data_files.items():
        p = tmpdir.mkdir('-'.join((str(f) for f in fkey)))
        for skey, fn in d.items():
            src_spectrum = Spectrum.import_from_file(fn)
            for ext in ['csv', 'sdb2']:
                exp_fn = p.join('{}_src.{}'.format(skey, ext))
                src_spectrum.export_to_file(filename=str(exp_fn))
                imp_spectrum = Spectrum.import_from_file(str(exp_fn))

                # Account for frequency units in KHz for sdb2
                assert np.allclose(src_spectrum.sample_data['frequency'], imp_spectrum.sample_data['frequency'])
                assert np.array_equal(src_spectrum.sample_data['magnitude'], imp_spectrum.sample_data['magnitude'])

def test_io(tmpdir, random_samples):
    from wwb_scanner.scan_objects import Spectrum

    rs = 1.024e6
    nsamp = 256
    step_size = 0.5e6
    freq_range = [572e6, 636e6]

    def build_data(fc):
        freqs, sig, Pxx = random_samples(n=nsamp, rs=rs, fc=fc)

        return freqs, Pxx

    spectrum = Spectrum(step_size=step_size)
    spectrum.color['r'] = 1.

    fc = freq_range[0]

    while True:
        freqs, ff = build_data(fc)
        spectrum.add_sample_set(freqs, iq=ff)
        if spectrum.sample_data['frequency'].max() >= freq_range[1] / 1e6:
            break
        fc += step_size

    dB = np.around(10 * np.log10(spectrum.sample_data['magnitude']), decimals=1)

    p = tmpdir.mkdir('test_io')
    for ext in ['csv', 'sdb2']:
        fn = p.join('foo.{}'.format(ext))
        spectrum.export_to_file(filename=str(fn))
        imp_spectrum = Spectrum.import_from_file(str(fn))

        assert np.allclose(spectrum.sample_data['frequency'], imp_spectrum.sample_data['frequency'])
        imp_dB = 10 * np.log10(imp_spectrum.sample_data['magnitude'])
        assert np.allclose(dB, imp_dB)
