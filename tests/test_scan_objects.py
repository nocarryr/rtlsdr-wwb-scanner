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

    rs = 2.048e6

    def build_data(fc):
        freqs, sig, Pxx = random_samples(n=256, rs=rs, fc=fc)

        return freqs, Pxx

    fc = 600e6

    spectrum = Spectrum()

    freqs, ff = build_data(fc)
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

    for freq, val in zip(freqs2, ff2):
        sample = spectrum.samples[freq]
        ix = sample.spectrum_index
        iq = spectrum.sample_data['iq'][ix]
        m = spectrum.sample_data['magnitude'][ix]
        dB = spectrum.sample_data['dbFS'][ix]
        assert iq == val == sample.iq
        assert m == np.abs(val) == sample.magnitude
        assert dB == 10 * np.log10(np.abs(val)) == sample.dbFS


    fc = 800e6
    freqs3, ff3 = build_data(fc)
    assert not np.any(np.in1d(spectrum.sample_data['frequency'], freqs3))

    spectrum.add_sample_set(frequency=freqs3, iq=ff3, center_frequency=fc, force_lower_freq=True)
    print('spectrum size: ', spectrum.sample_data['frequency'].size)

    assert np.unique(spectrum.sample_data['frequency']).size == spectrum.sample_data['frequency'].size
    assert spectrum.sample_data['frequency'].size == spectrum.sample_data['iq'].size
    assert spectrum.sample_data['frequency'].size == spectrum.sample_data['magnitude'].size

    for freq, val in zip(freqs3, ff3):
        sample = spectrum.samples[freq]
        ix = sample.spectrum_index
        iq = spectrum.sample_data['iq'][ix]
        m = spectrum.sample_data['magnitude'][ix]
        dB = spectrum.sample_data['dbFS'][ix]
        assert iq == val == sample.iq
        assert m == np.abs(val) == sample.magnitude
        assert dB == 10 * np.log10(np.abs(val)) == sample.dbFS
