import numpy as np

def test_dbstore_monkeypatch(tmp_db_store):
    from wwb_scanner.scan_objects import Spectrum
    from wwb_scanner.scan_objects.spectrum import db_store as _spec_db_store
    from wwb_scanner.utils import dbstore


    assert dbstore.DBStore.DB_PATH == dbstore.db_store.DB_PATH == tmp_db_store['db_path']
    assert dbstore.DBStore.SCAN_DB_PATH == dbstore.db_store.SCAN_DB_PATH == tmp_db_store['scan_db_path']
    assert _spec_db_store.DB_PATH == tmp_db_store['db_path']
    assert _spec_db_store.SCAN_DB_PATH == tmp_db_store['scan_db_path']

def test_dbstore(tmp_db_store, data_files, random_samples):
    from wwb_scanner.file_handlers import BaseImporter
    from wwb_scanner.scan_objects import Spectrum
    from wwb_scanner.utils.dbstore import db_store

    spec = {}
    for fkey, d in data_files.items():
        for skey, fn in d.items():
            spectrum = BaseImporter.import_file(fn)
            spectrum.save_to_dbstore()
            assert spectrum.eid is not None
            spec[spectrum.eid] = spectrum

    rs = 1.024e6
    nsamp = 256
    step_size = 0.5e6
    freq_range = [572e6, 636e6]

    spectrum = Spectrum()
    fc = freq_range[0]
    while True:
        freqs, sig, Pxx = random_samples(n=nsamp, rs=rs, fc=fc)
        spectrum.add_sample_set(frequency=freqs, iq=Pxx)
        if spectrum.sample_data['frequency'].max() >= freq_range[1] / 1e6:
            break
        fc += step_size

    spectrum.save_to_dbstore()
    assert spectrum.eid is not None
    spec[spectrum.eid] = spectrum

    for eid, spectrum in spec.items():
        db_spectrum = Spectrum.from_dbstore(eid=spectrum.eid)
        for attr in Spectrum._serialize_attrs:
            assert getattr(spectrum, attr) == getattr(db_spectrum, attr)
        assert np.array_equal(spectrum.sample_data, db_spectrum.sample_data)

    db_data = db_store.get_all_scans()

    assert set(db_data.keys()) == set(spec.keys())
