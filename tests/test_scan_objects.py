import numpy as np

def test_sample_array(random_samples):
    from wwb_scanner.scan_objects import SampleArray

    rs = 2.048e6
    fc = 600e6

    a = SampleArray()

    freqs, sig, ff = random_samples(rs=rs, fc=fc)

    b = SampleArray.create(frequency=freqs, iq=ff)
    a.insert_sorted(b)

    assert np.array_equal(a.data, b.data)

    assert np.array_equal(a.frequency, freqs)
    assert np.array_equal(a.iq, ff)
    assert np.array_equal(a.magnitude, np.abs(ff))
    assert np.array_equal(a.dbFS, 10 * np.log10(np.abs(ff)))

    assert np.array_equal(a.frequency, a['frequency'])
    assert np.array_equal(a.iq, a['iq'])
    assert np.array_equal(a.magnitude, a['magnitude'])
    assert np.array_equal(a.dbFS, a['dbFS'])

    fc = 900e6

    freqs, sig, ff = random_samples(rs=rs, fc=fc)

    a.set_fields(frequency=freqs, iq=ff)
    c = SampleArray.create(frequency=freqs, iq=ff)

    ix = np.flatnonzero(np.in1d(a.frequency, c.frequency))
    assert np.array_equal(a.data[ix], c.data)

def test_spectrum(random_samples):
    from wwb_scanner.scan_objects import Spectrum

    rs = 2.048e6
    fc = 600e6

    spectrum = Spectrum()
    freqs, sig, ff = random_samples(rs=rs, fc=fc)

    for freq, val in zip(freqs, ff):
        spectrum.add_sample(frequency=freq, iq=val)

    assert np.array_equal(spectrum.sample_data['frequency'], freqs)
    assert np.array_equal(spectrum.sample_data['iq'], ff)
    assert np.array_equal(spectrum.sample_data['magnitude'], np.abs(ff))
    assert np.array_equal(spectrum.sample_data['dbFS'], 10 * np.log10(np.abs(ff)))

def test_add_sample_set(random_samples):
    from wwb_scanner.scan_objects import Spectrum
    from wwb_scanner.scan_objects import SampleArray

    rs = 2.000e6

    def build_data(fc):
        freqs, sig, Pxx = random_samples(n=256, rs=rs, fc=fc)

        return freqs, Pxx

    def build_struct_data(freqs, ff):
        data = np.zeros(freqs.size, dtype=SampleArray.dtype)
        data['frequency'] = freqs
        data['iq'] = ff
        data['magnitude'] = np.abs(ff)
        data['dbFS'] = 10 * np.log10(np.abs(ff))
        return data

    def get_overlap_arrays(data1, data2):
        freqs1 = data1['frequency']
        freqs2 = data2['frequency']
        overlap_data1 = data1[np.flatnonzero(np.in1d(freqs1, freqs2))]
        overlap_data2 = data2[np.flatnonzero(np.in1d(freqs2, freqs1))]
        avg_data = np.zeros(overlap_data1.size, dtype=overlap_data1.dtype)
        avg_data['frequency'] = overlap_data1['frequency']
        for key in ['iq', 'magnitude', 'dbFS']:
            avg_data[key] = np.mean([overlap_data1[key], overlap_data2[key]], axis=0)
        non_overlap_data2 = data2[np.flatnonzero(np.in1d(freqs2, freqs1, invert=True))]
        assert np.array_equal(overlap_data1['frequency'], overlap_data2['frequency'])

        return avg_data, non_overlap_data2

    fc = 600e6

    spectrum = Spectrum()

    freqs, ff = build_data(fc)
    data1 = build_struct_data(freqs, ff)

    spectrum.add_sample_set(frequency=freqs, iq=ff, center_frequency=fc, force_lower_freq=True)

    assert np.array_equal(spectrum.sample_data['frequency'], freqs)
    assert np.array_equal(spectrum.sample_data['iq'], ff)
    assert np.array_equal(spectrum.sample_data['magnitude'], np.abs(ff))
    assert np.array_equal(spectrum.sample_data['dbFS'], 10 * np.log10(np.abs(ff)))

    fc += 1e6

    freqs2, ff2 = build_data(fc)
    assert np.any(np.in1d(freqs, freqs2))

    print('in1d: ', np.nonzero(np.in1d(spectrum.sample_data['frequency'], freqs2)))
    print('spectrum size: ', spectrum.sample_data['frequency'].size)

    spectrum.add_sample_set(frequency=freqs2, iq=ff2, center_frequency=fc, force_lower_freq=True)
    print('spectrum size: ', spectrum.sample_data['frequency'].size)

    assert np.unique(spectrum.sample_data['frequency']).size == spectrum.sample_data['frequency'].size

    data2 = build_struct_data(freqs2, ff2)
    avg_data, non_overlap_data2 = get_overlap_arrays(data1, data2)
    assert data2.size == avg_data.size + non_overlap_data2.size
    assert spectrum.sample_data.size == data1.size + non_overlap_data2.size

    for freq in freqs2:
        mask = np.isin([freq], avg_data['frequency'])
        if np.any(mask):
            val = avg_data[np.searchsorted(avg_data['frequency'], freq)]
        else:
            val = non_overlap_data2[np.searchsorted(non_overlap_data2['frequency'], freq)]
        sample = spectrum.samples[freq]
        ix = sample.spectrum_index
        iq = spectrum.sample_data['iq'][ix]
        m = spectrum.sample_data['magnitude'][ix]
        dB = spectrum.sample_data['dbFS'][ix]
        assert iq == val['iq'] == sample.iq
        assert m == val['magnitude'] == sample.magnitude
        assert dB == val['dbFS'] == sample.dbFS


    fc = 800e6
    freqs3, ff3 = build_data(fc)
    assert not np.any(np.in1d(spectrum.sample_data['frequency'], freqs3))

    spectrum.add_sample_set(frequency=freqs3, iq=ff3, center_frequency=fc, force_lower_freq=True)
    print('spectrum size: ', spectrum.sample_data['frequency'].size)

    assert np.unique(spectrum.sample_data['frequency']).size == spectrum.sample_data['frequency'].size
    assert spectrum.sample_data['frequency'].size == spectrum.sample_data['iq'].size
    assert spectrum.sample_data['frequency'].size == spectrum.sample_data['magnitude'].size

    data3 = build_struct_data(freqs3, ff3)
    avg_data2, non_overlap_data3 = get_overlap_arrays(data2, data3)
    assert data3.size == avg_data2.size + non_overlap_data3.size
    assert spectrum.sample_data.size == data1.size + non_overlap_data2.size + non_overlap_data3.size

    for freq in freqs3:
        mask = np.isin([freq], avg_data2['frequency'])
        if np.any(mask):
            val = avg_data2[np.searchsorted(avg_data2['frequency'], freq)]
        else:
            val = non_overlap_data3[np.searchsorted(non_overlap_data3['frequency'], freq)]
        sample = spectrum.samples[freq]
        ix = sample.spectrum_index
        iq = spectrum.sample_data['iq'][ix]
        m = spectrum.sample_data['magnitude'][ix]
        dB = spectrum.sample_data['dbFS'][ix]
        assert iq == val['iq'] == sample.iq
        assert m == val['magnitude'] == sample.magnitude
        assert dB == val['dbFS'] == sample.dbFS
