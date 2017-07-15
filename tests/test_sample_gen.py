import numpy as np

def test_sample_gen(random_samples):
    for i in range(256):
        freqs, sig, Pxx = random_samples(256)

        print(i)

        z = np.count_nonzero(Pxx) == Pxx.size
        if not z:
            print('-------sig--------')
            print(sig)
            print('-------Pxx--------')
            print(Pxx)
            print('------')
            ix = np.argwhere(Pxx==0)
            print(ix, sig[ix], Pxx[ix])
        assert z is True
