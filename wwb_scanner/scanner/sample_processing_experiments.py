import time
import threading
try:
    import queue
except ImportError:
    import Queue as queue

import numpy as np
from scipy.signal.windows import __all__ as WINDOW_TYPES
from scipy.signal import welch, get_window, detrend
from scipy import signal
import matplotlib.mlab
#import pyfftw

from wwb_scanner.core import JSONMixin

WINDOW_TYPES = [s for s in WINDOW_TYPES if s != 'get_window']

nperseg = 128


def segment_iter(samples, nperseg, noverlap=None):
    if noverlap is None:
        noverlap = nperseg // 2
    if len(samples.shape) > 1:
        samples = samples.flatten()
    num_segments = samples.size // (nperseg-noverlap)
    if samples.size % num_segments > 0:
        num_segments += 1
        samples = np.append(samples, samples[:samples.size%num_segments])

    def slice_iter():
        sl = 0
        i = 0
        while True:
            if i+nperseg >= samples.size-1:
                break
            yield sl, np.s_[i:i+nperseg]
            i += nperseg - noverlap
            sl += 1
            #samples = np.roll(samples, nperseg - noverlap)
    result = np.zeros((num_segments, nperseg), dtype=samples.dtype)
    for sl, ix in slice_iter():
        result[sl] = samples[ix]
    return result


def next_2_to_pow(val):
    val -= 1
    val |= val >> 1
    val |= val >> 2
    val |= val >> 4
    val |= val >> 8
    val |= val >> 16
    return val + 1

def last_2_to_pow(val):
    if val <= 1:
        return val
    n = next_2_to_pow(val) >> 1
    return val - (val % n)

def calc_num_samples(num_samples):
    return next_2_to_pow(int(num_samples))

def sort_psd(f, Pxx, onesided=False):
    a = np.zeros(f.size, dtype=[('f', f.dtype), ('Pxx', Pxx.dtype)])
    a['f'] = f[:]
    a['Pxx'] = Pxx[:]
    a = np.sort(a, order='f')
    return a['f'], a['Pxx']
    # f_index = np.argsort(f)
    # f = f[f_index]
    # Pxx = Pxx[f_index]
    # if onesided:
    #     i = np.searchsorted(f, 0)
    #     f = f[i:]
    #     Pxx = Pxx[i:]
    #     Pxx *= 2
    # return f, Pxx

class SampleSet(JSONMixin):
    __slots__ = ('scanner', 'center_frequency', 'raw', 'current_sweep', 'complete',
                 '_frequencies', 'powers', 'collection', 'process_thread', 'samples_discarded')
    def __init__(self, **kwargs):
        for key in self.__slots__:
            if key == '_frequencies':
                key = 'frequencies'
            setattr(self, key, kwargs.get(key))
        self.complete = threading.Event()
        self.samples_discarded = False
        if self.scanner is None and self.collection is not None:
            self.scanner = self.collection.scanner
    @property
    def frequencies(self):
        f = getattr(self, '_frequencies', None)
        if f is None:
            f = self._frequencies= self.calc_expected_freqs()
        return f
    @frequencies.setter
    def frequencies(self, value):
        self._frequencies = value
    @property
    def sweeps_per_scan(self):
        return self.scanner.sweeps_per_scan
    @property
    def samples_per_sweep(self):
        return self.scanner.samples_per_sweep
    def read_samples(self):
        scanner = self.scanner
        freq = self.center_frequency
        sweeps_per_scan = scanner.sweeps_per_scan
        samples_per_sweep = scanner.samples_per_sweep
        sdr = scanner.sdr
        sdr.set_center_freq(freq)
        self.raw = np.zeros((sweeps_per_scan, samples_per_sweep), 'complex')
        self.powers = np.zeros((sweeps_per_scan, samples_per_sweep), 'float64')
        sdr.read_samples_async(self.samples_callback, num_samples=samples_per_sweep)
    def samples_callback(self, iq, context):
        samples_per_sweep = self.scanner.samples_per_sweep
        if not self.samples_discarded:
            self.samples_discarded = True
            return
        current_sweep = getattr(self, 'current_sweep', None)
        if current_sweep is None:
            current_sweep = self.current_sweep = 0
        if current_sweep >= self.raw.shape[0]:
            self.on_sample_read_complete()
            return
        try:
            self.raw[current_sweep] = iq
            self.process_sweep(current_sweep)
        except:
            self.on_sample_read_complete()
            raise
        self.current_sweep += 1
        if current_sweep > self.raw.shape[0]:
            self.on_sample_read_complete()
    def on_sample_read_complete(self):
        sdr = self.scanner.sdr
        if not sdr.read_async_canceling:
            sdr.cancel_read_async()
        self.process_samples()
    def launch_process_thread(self):
        self.process_thread = ProcessThread(self)
    def process_sweep(self, sweep):
        scanner = self.scanner
        freq = self.center_frequency
        win = get_window('triang', nperseg)
        f, powers = welch(self.raw[sweep], fs=scanner.sample_rate,
                          window=win, nperseg=nperseg, return_onesided=False)
        f += freq
        f /= 1e6
        #powers = 10. * np.log10(powers)
        self.collection.on_sweep_processed(sample_set=self,
                                           powers=powers,
                                           frequencies=f)
    def translate_freq(self, samples, freq):
        # Adapted from https://github.com/vsergeev/luaradio/blob/master/radio/blocks/signal/frequencytranslator.lua
        rs = 2.048e6# self.scanner.sample_rate
        if not np.iscomplexobj(samples):
            samples = signal.hilbert(samples)
        omega = 2 * np.pi * (freq / rs)
        def iter_phase():
            p = 0
            i = 0
            while i < samples.shape[-1]:
                yield p
                p += omega
                p -= 2 * np.pi
                i += 1
        phase_rot = np.fromiter(iter_phase(), dtype=np.float)
        phase_rot = np.unwrap(phase_rot)
        xlator = np.zeros(phase_rot.size, dtype=samples.dtype)
        xlator.real = np.cos(phase_rot)
        xlator.imag = np.sin(phase_rot)
        samples *= xlator
        return samples
    def inst_freq_process_samples(self):
        rs = self.scanner.sample_rate
        fc = self.center_frequency

        samples = self.raw.flatten()

        inst_mag = np.abs(samples)
        inst_phase = np.unwrap(np.angle(samples))
        inst_freq = np.zeros(inst_phase.size, dtype=np.float64)
        inst_freq[1:] = np.diff(inst_phase) / (2*np.pi) * rs

        freqs, freq_ix, freq_counts = np.unique(inst_freq, return_index=True, return_counts=True)
        freqs_mag = np.zeros((freq_counts.max(), freqs.size), dtype=[('frequency', np.float64), ('mag', np.float64)])
        freqs += fc
        freqs_mag['frequency'] = freqs
        freqs_mag['mag'] = inst_mag[freq_ix]

        freqs_mag = np.sort(freqs_mag, order='frequency')

        freqs_interp = self.frequencies * 1e6
        mag_interp = np.interp(freqs_interp, freqs_mag['frequency'], freqs_mag['mag'])

        self.powers = mag_interp

        self.collection.on_sample_set_processed(self)
        self.complete.set()

    def process_samples(self):
        rs = self.scanner.sample_rate
        fc = self.center_frequency

        overlap_ratio = self.scanner.sampling_config.sweep_overlap_ratio

        samples = self.raw.flatten()
        #samples = self.translate_freq(samples, fc)

        win = get_window(self.scanner.sampling_config.window_type, nperseg)
        freqs, Pxx = welch(samples, fs=rs, window=win,
            nperseg=nperseg, scaling='density', return_onesided=False)

        iPxx = np.fft.irfft(Pxx)
        iPxx = self.translate_freq(iPxx, fc)
        Pxx = np.abs(np.fft.rfft(iPxx))

        freqs, Pxx = sort_psd(freqs, Pxx)
        f_ix = np.append(np.nonzero(freqs<-0.25e6), np.nonzero(freqs>0.25e6))
        freqs = freqs[f_ix]
        Pxx = Pxx[f_ix]

        freqs += fc
        freqs /= 1e6

        self.powers = Pxx
        if not np.array_equal(freqs, self.frequencies):
            print('freq not equal: %s, %s' % (self.frequencies.size, freqs.size))
            self.frequencies = freqs

        self.collection.on_sample_set_processed(self)
        self.complete.set()

    def mlab_process_samples(self):
        rs = self.scanner.sample_rate
        fc = self.center_frequency

        overlap_ratio = self.scanner.sampling_config.sweep_overlap_ratio

        samples = self.raw.flatten()
        #samples = self.translate_freq(samples, fc)

        win = get_window(self.scanner.sampling_config.window_type, nperseg)
        freqs, Pxx = matplotlib.mlab.psd(samples, Fs=rs, window=win, NFFT=nperseg)

        #print('freqs: min={}, max={}, size={}'.format(freqs.min(), freqs.max(), freqs.size))
        # iPxx = np.fft.irfft(Pxx)
        # iPxx = self.translate_freq(iPxx, fc)
        # Pxx = np.abs(np.fft.rfft(iPxx))

        freqs, Pxx = sort_psd(freqs, Pxx)
        #print('sorted freqs: {}, Pxx: {}'.format(freqs.size, Pxx.size))
        # f_ix = np.append(np.nonzero(freqs<-0.25e6), np.nonzero(freqs>0.25e6))
        # freqs = freqs[f_ix]
        # Pxx = Pxx[f_ix]
        #print('chopped freqs: {}, Pxx: {}'.format(freqs.size, Pxx.size))

        freqs += fc
        freqs /= 1e6

        self.powers = Pxx
        if not np.array_equal(freqs, self.frequencies):
            ne_ix = np.nonzero(np.not_equal(self.frequencies, freqs))

            print('freq not equal: %s, %s' % (self.frequencies[ne_ix], freqs[ne_ix]))
            self.frequencies = freqs

        self.collection.on_sample_set_processed(self)
        self.complete.set()

    def ff_process_samples(self):
        rs = self.scanner.sample_rate
        fc = self.center_frequency
        nyq = rs / 2.
        overlap_ratio = self.scanner.sampling_config.sweep_overlap_ratio
        win = get_window(self.scanner.sampling_config.window_type, nperseg)
        samples = segment_iter(self.raw, nperseg) * win

        win = get_window(self.scanner.sampling_config.window_type, nperseg, fftbins=True)
        win = np.fft.ifftshift(win)

        #scale = 1. / ((rs + fc) * (win*win).sum())
        scale = 1.0 / (fc - rs/2) * (win.sum()**2)

        ff = np.fft.fft(samples)

        ff = np.conjugate(ff) * ff
        ff *= scale
        #ff = ff.real

        freqs = np.fft.fftfreq(nperseg, 1./rs)
        #ff /= freqs + fc
        mag = np.mean(np.abs(ff), axis=0)

        mag = mag[freqs!=fc]
        mag = mag[1:]
        freqs = freqs[[freqs!=fc]]
        freqs = freqs[1:]


        freqs, mag = sort_psd(freqs, mag)
        crop = int((freqs.size * overlap_ratio) / 2)
        freqs, mag = freqs[crop:crop*-1], mag[crop:crop*-1]
        freqs += fc
        freqs /= 1e6

        self.powers = mag
        if not np.array_equal(freqs, self.frequencies):
            print('freq not equal: %s, %s' % (self.frequencies.size, freqs.size))
            self.frequencies = freqs

        self.collection.on_sample_set_processed(self)
        self.complete.set()
    def calc_expected_freqs(self):
        freq = self.center_frequency
        scanner = self.scanner
        rs = scanner.sample_rate
        num_samples = scanner.samples_per_sweep * scanner.sweeps_per_scan
        overlap_ratio = scanner.sampling_config.sweep_overlap_ratio
        fake_samples = np.zeros(num_samples, 'complex')
        f_expected, Pxx = welch(fake_samples.real, fs=rs, nperseg=nperseg, return_onesided=False)

        # f_expected = f_expected[1:]
        # f_expected = f_expected[f_expected!=freq]
        f_expected, Pxx = sort_psd(f_expected, Pxx)

        f_ix = np.append(np.nonzero(f_expected<-0.25e6), np.nonzero(f_expected>0.25e6))
        f_expected = f_expected[f_ix]

        # crop = int((f_expected.size * overlap_ratio) / 2)
        # f_expected, Pxx = f_expected[crop:crop*-1], Pxx[crop:crop*-1]
        f_expected += freq
        f_expected /= 1e6
        return f_expected
    def correlate(self, other):
        return
        freqs = np.intersect1d(self.frequencies, other.frequencies)
        if not freqs.size:
            return
        if self.center_frequency > other.center_frequency:
            my_ix = np.argwhere(np.less_equal(self.frequencies, freqs.max()))
            oth_ix = np.argwhere(np.greater_equal(other.frequencies, freqs.min()))
        else:
            my_ix = np.argwhere(np.greater_equal(self.frequencies, freqs.min()))
            oth_ix = np.argwhere(np.less_equal(other.frequencies, freqs.max()))
        powers = np.vstack((self.powers[my_ix], other.powers[oth_ix]))
        #powers = detrend(powers, axis=0)
        powers = np.mean(powers, axis=0)


        # my_P = np.fft.ifft(self.powers[my_ix])
        # ot_P = np.fft.ifft(other.powers[oth_ix])
        # powers = np.fft.fft(fftconvolve(my_P, ot_P))

        # my_P = self.powers[my_ix]
        # ot_P = other.powers[oth_ix]
        # print('my_P={}, oth_P={}'.format(my_P.shape, ot_P.shape))
        # powers = signal.correlate(my_P, ot_P, mode='same', method='direct')

        self.powers[my_ix] = powers
        other.powers[my_ix] = powers.copy()
    def _serialize(self):
        d = {}
        for key in self.__slots__:
            if key in ['scanner', 'collection', 'complete']:
                continue
            val = getattr(self, key)
            d[key] = val
        return d


class SampleCollection(JSONMixin):
    def __init__(self, **kwargs):
        self.scanner = kwargs.get('scanner')
        self.scanning = threading.Event()
        self.stopped = threading.Event()
        self.sample_sets = {}
    def add_sample_set(self, sample_set):
        self.sample_sets[sample_set.center_frequency] = sample_set
    def build_sample_set(self, freq):
        sample_set = SampleSet(collection=self, center_frequency=freq)
        self.add_sample_set(sample_set)
        return sample_set
    def __iter__(self):
        for f in sorted(self.sample_sets):
            yield self.sample_sets[f]
    def build_arrays(self):
        f = np.concatenate(tuple((ss.frequencies for ss in self)))
        self.frequencies = np.unique(f)
        self.powers = np.zeros(self.frequencies.size, dtype='complex')
        print('freq size: ', self.frequencies.size)
    def scan_freq(self, freq):
        self.build_process_pool()
        sample_set = self.sample_sets.get(freq)
        if sample_set is None:
            sample_set = self.build_sample_set(freq)
        sample_set.read_samples()
        return sample_set
    def scan_all_freqs(self):
        self.scanning.set()
        complete_events = set()
        for key in sorted(self.sample_sets.keys()):
            if not self.scanning.is_set():
                break
            sample_set = self.sample_sets[key]
            sample_set.read_samples()
            if not sample_set.complete.is_set():
                complete_events.add(sample_set.complete)
        if self.scanning.is_set():
            print('waiting for {} sample sets'.format(len(complete_events)))
            for e in complete_events.copy():
                if e.is_set():
                    complete_events.discard(e)
                else:
                    e.wait()
            print('wait complete ({} events)'.format(len(complete_events)))
        self.scanning.clear()
        self.stopped.set()
    def stop(self):
        if self.scanning.is_set():
            self.scanning.clear()
            self.stopped.wait()
    def cancel(self):
        if self.scanning.is_set():
            self.scanning.clear()
            self.stopped.wait()
    def on_sweep_processed(self, **kwargs):
        self.scanner.on_sweep_processed(**kwargs)
    def on_sample_set_processed(self, sample_set):
        fc = sample_set.center_frequency
        keys = [k for k in self.sample_sets.keys() if k < fc]
        if len(keys):
            prev_fc = max(keys)
            prev_samp = self.sample_sets[prev_fc]
            sample_set.correlate(prev_samp)
        self.scanner.on_sample_set_processed(sample_set)
    def _serialize(self):
        return {'sample_sets':
            {k: v._serialize() for k, v in self.sample_sets.items()},
        }
    def _deserialize(self, **kwargs):
        for key, val in kwargs.get('sample_sets', {}).items():
            sample_set = SampleSet.from_json(val, collection=self)
            self.sample_sets[key] = sample_set

def open_collection():
    fn = '/home/nocarrier/wwb_scanner_data/sample_collection.json'
    with open(fn, 'r') as f:
        s = f.read()
    return SampleCollection.from_json(s)

# import matplotlib
# matplotlib.use('Qt5Agg')
# import matplotlib.pyplot as plt
# from matplotlib.widgets import Cursor
def plot_collection():
    fig = plt.figure()
    #figtext = fig.text(x=0., y=0., s='000.000 0')
    all_axes = {}

    rs = 2.048e6
    coll = open_collection()
    k = min(coll.sample_sets.keys())
    ss = coll.sample_sets[k]

    #samples = ss.raw.flatten()
    samples = ss.raw[0]

    samples_rot = ss.translate_freq(samples, ss.center_frequency)
    inst_mag = np.abs(samples_rot)
    inst_phase = np.unwrap(np.angle(samples_rot))
    inst_freq = np.zeros(inst_phase.size, dtype=np.float64)
    inst_freq[1:] = np.diff(inst_phase) / (2*np.pi) * rs

    t = np.arange(samples.size, dtype=np.float64)
    t /= rs


    # ax1 = fig.add_subplot(3, 2, 1)
    # plt.plot(t, inst_mag)
    # plt.title('mag')
    #
    # ax2 = fig.add_subplot(3, 2, 2, sharex=ax1)
    # plt.plot(t, np.angle(samples))
    # plt.title('angle')
    #
    # ax3 = fig.add_subplot(3, 2, 3, sharex=ax1)
    # plt.plot(t, inst_freq)
    # plt.title('freq')

    freqs, freq_ix = np.unique(inst_freq, return_index=True)
    freqs_mag = np.zeros(freqs.size, dtype=[('frequency', np.float64), ('mag', np.float64)])
    freqs += ss.center_frequency
    freqs_mag['frequency'] = freqs
    freqs_mag['mag'] = inst_mag[freq_ix]

    freqs_mag = np.sort(freqs_mag, order='frequency')

    ax4 = fig.add_subplot(4, 1, 1)
    l = plt.plot(freqs_mag['frequency'], freqs_mag['mag'])
    all_axes[ax4.get_gid()] = {'ax':ax4, 'line':l}
    plt.title('freqs/mag')
    plt.grid(True)

    freqs_interp = np.linspace(freqs.min(), freqs.max(), 256)
    mag_interp = np.interp(freqs_interp, freqs_mag['frequency'], freqs_mag['mag'])

    ax5 = fig.add_subplot(4, 1, 2, sharex=ax4)
    l = plt.plot(freqs_interp, mag_interp)
    all_axes[ax5.get_gid()] = {'ax':ax5, 'line':l}
    plt.title('freqs/mag interp')
    plt.grid(True)

    # ax6 = plt.subplot(3, 1, 3)
    # Mxx, Mfreqs, _ = plt.magnitude_spectrum(samples, Fs=rs, Fc=ss.center_frequency)
    # plt.title('mag spec')

    ax7 = fig.add_subplot(4, 1, 3)
    Pxx, Pfreqs, l = plt.psd(samples, Fs=rs, Fc=ss.center_frequency, return_line=True)
    all_axes[ax7.get_gid()] = {'ax':ax7, 'line':l}
    plt.title('mlab psd')
    plt.ylabel('')
    plt.xlabel('')
    plt.grid(True)

    ax8 = fig.add_subplot(4, 1, 4)
    nperseg = 256
    win = get_window('hann', 256)
    sc_freqs, sc_Pxx = signal.welch(samples, fs=rs, window=win, nperseg=nperseg, return_onesided=False)
    sc_freqs += ss.center_frequency
    sc_Pxx = 10 * np.log10(np.abs(sc_Pxx))
    sc_f_p = np.zeros(sc_freqs.size, dtype=[('freq', sc_freqs.dtype), ('Pxx', sc_Pxx.dtype)])
    sc_f_p['freq'] = sc_freqs
    sc_f_p['Pxx'] = sc_Pxx
    sc_f_p = np.sort(sc_f_p, order='freq')
    l = plt.plot(sc_f_p['freq'], sc_f_p['Pxx'])
    all_axes[ax8.get_gid()] = {'ax':ax8, 'line':l}
    plt.title('scipy psd')
    plt.grid(True)
    c = Cursor(ax8, useblit=True, color='black', linewidth=2)

    print('sc_freqs: ', sc_freqs.shape, sc_freqs.dtype, sc_freqs.min(), sc_freqs.max())
    print('sc_Pxx: ', sc_Pxx.shape, sc_Pxx.dtype, sc_Pxx.min(), sc_Pxx.max())
    print('Fc in Pxx: ', ss.center_frequency in sc_freqs)
    if ss.center_frequency in sc_freqs:
        print('Pxx at Fc: ', sc_Pxx[np.argwhere(sc_freqs==ss.center_frequency)])




    plt.subplots_adjust(hspace=0.5)

    class TextUpdate(object):
        def __init__(self, figure, fig_axes):
            self.figure = figure
            self.fig_axes = fig_axes
            self.figtext = figure.text(0., 0., '')
            figure.canvas.mpl_connect('motion_notify_event', self.on_move)
        def set_x_markers(self, xdata):
            for gid, d in self.fig_axes.items():
                for line in d['ax'].get_lines():
                    line_xdata = line.xdata
                    if not isinstance(line_xdata, np.ndarray):
                        line_xdata = np.array(line_xdata)
                    idx = np.abs(line_xdata - xdata).argmin()
                    line.set_markerevery([idx])
        def on_move(self, event):
            # get the x and y pixel coords
            x, y = event.x, event.y

            if event.inaxes:
                ax = event.inaxes  # the axes instance
                self.figtext.set_text('%07.3f %f' % (event.xdata/1e6, event.ydata))
                #figtext.text = '%07.3f %f' % (event.xdata, event.ydata)
                self.set_x_markers(event.xdata)

                self.figure.canvas.draw()
    #fig.canvas.mpl_connect('motion_notify_event', on_move)
    txt_update = TextUpdate(fig, all_axes)
    plt.show()

    return dict(
        coll=coll,
        ss=ss,
        t=t,
        inst_mag=inst_mag,
        inst_phase=inst_phase,
        inst_freq=inst_freq,
    )

if __name__ == '__main__':
    d = plot_collection()
