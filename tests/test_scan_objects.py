import numpy as np

def test_spectrum(random_samples):
    from wwb_scanner.scan_objects import Spectrum

    rs = 2.048e6
    fc = 600e6

    spectrum = Spectrum()
    samples = random_samples()

    freqs = np.fft.fftfreq(samples.size, 1/rs)
    freqs = np.fft.fftshift(freqs)
    freqs += fc
    freqs /= 1e6

    ff = np.fft.fft(samples)
    ff = np.fft.fftshift(ff)

    for freq, val in zip(freqs, ff):
        spectrum.add_sample(frequency=freq, iq=val)

    assert np.array_equal(spectrum.sample_data['frequency'], freqs)
    assert np.array_equal(spectrum.sample_data['iq'], ff)
    assert np.array_equal(spectrum.sample_data['magnitude'], np.abs(ff))

def test_add_sample_set(random_samples):
    from wwb_scanner.scan_objects import Spectrum

    rs = 2.048e6

    def build_data(fc):
        samples = random_samples(256)

        freqs = np.fft.fftfreq(samples.size, 1/rs)
        freqs = np.fft.fftshift(freqs)
        freqs += fc
        freqs /= 1e6

        ff = np.fft.fft(samples)
        ff = np.fft.fftshift(ff)

        return freqs, ff

    fc = 600e6

    spectrum = Spectrum()

    freqs, ff = build_data(fc)
    spectrum.add_sample_set(freqs, iq=ff, center_frequency=fc, force_lower_freq=True)

    assert np.array_equal(spectrum.sample_data['frequency'], freqs)
    assert np.array_equal(spectrum.sample_data['iq'], ff)
    assert np.array_equal(spectrum.sample_data['magnitude'], np.abs(ff))

    fc += 1e6

    freqs2, ff2 = build_data(fc)
    assert np.any(np.in1d(freqs, freqs2))

    print('in1d: ', np.nonzero(np.in1d(spectrum.sample_data['frequency'], freqs2)))
    print('spectrum size: ', spectrum.sample_data['frequency'].size)

    spectrum.add_sample_set(freqs2, iq=ff2, center_frequency=fc, force_lower_freq=True)
    print('spectrum size: ', spectrum.sample_data['frequency'].size)

    assert np.unique(spectrum.sample_data['frequency']).size == spectrum.sample_data['frequency'].size

    for freq, val in zip(freqs2, ff2):
        sample = spectrum.samples[freq]
        ix = sample.spectrum_index
        iq = spectrum.sample_data['iq'][ix]
        m = spectrum.sample_data['magnitude'][ix]
        assert iq == val == sample.iq
        assert m == np.abs(val) == sample.magnitude


    fc = 800e6
    freqs3, ff3 = build_data(fc)
    assert not np.any(np.in1d(spectrum.sample_data['frequency'], freqs3))

    spectrum.add_sample_set(freqs3, iq=ff3, center_frequency=fc, force_lower_freq=True)
    print('spectrum size: ', spectrum.sample_data['frequency'].size)

    assert np.unique(spectrum.sample_data['frequency']).size == spectrum.sample_data['frequency'].size
    assert spectrum.sample_data['frequency'].size == spectrum.sample_data['iq'].size
    assert spectrum.sample_data['frequency'].size == spectrum.sample_data['magnitude'].size

    for freq, val in zip(freqs3, ff3):
        sample = spectrum.samples[freq]
        ix = sample.spectrum_index
        iq = spectrum.sample_data['iq'][ix]
        m = spectrum.sample_data['magnitude'][ix]
        assert iq == val == sample.iq
        assert m == np.abs(val) == sample.magnitude
