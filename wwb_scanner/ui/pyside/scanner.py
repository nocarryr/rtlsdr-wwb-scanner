import threading

import numpy as np

from PySide2 import QtCore, QtQml, QtQuick
from PySide2.QtCore import Signal, Property, Slot

from wwb_scanner.scanner import config
from wwb_scanner.scanner import Scanner
from wwb_scanner.scanner.main import get_freq_resolution
from wwb_scanner.scan_objects import Spectrum

from wwb_scanner.ui.pyside.utils import GenericQObject, QObjectThread

class ScanConfigData(GenericQObject):
    _n_startFreq = Signal()
    _n_endFreq = Signal()
    _n_samplesPerSweep = Signal()
    _n_sweepsPerScan = Signal()
    _n_sweepOverlapRatio = Signal()
    _n_windowType = Signal()
    _n_windowSize = Signal()
    _n_smoothingEnabled = Signal()
    _n_smoothingFactor = Signal()
    _n_scalingEnabled = Signal()
    _n_scalingMinDB = Signal()
    _n_scalingMaxDB = Signal()
    configUpdate = Signal()
    def __init__(self, *args):
        self._startFreq = 470.
        self._endFreq = 536.
        self._samplesPerSweep = 8192
        self._sweepsPerScan = 20
        self._sweepOverlapRatio = .5
        self._windowType = 'hann'
        self._windowSize = 128
        self._smoothingEnabled = False
        self._smoothingFactor = 1.
        self._scalingEnabled = False
        self._scalingMinDB = -140.
        self._scalingMaxDB = -55.
        super().__init__(*args)

    def _generic_property_changed(self, attr, old_value, new_value):
        self.configUpdate.emit()

    def _g_startFreq(self): return self._startFreq
    def _s_startFreq(self, value): self._generic_setter('_startFreq', value)
    startFreq = Property(float, _g_startFreq, _s_startFreq, notify=_n_startFreq)

    def _g_endFreq(self): return self._endFreq
    def _s_endFreq(self, value): self._generic_setter('_endFreq', value)
    endFreq = Property(float, _g_endFreq, _s_endFreq, notify=_n_endFreq)

    def _g_samplesPerSweep(self): return self._samplesPerSweep
    def _s_samplesPerSweep(self, value): self._generic_setter('_samplesPerSweep', value)
    samplesPerSweep = Property(int, _g_samplesPerSweep, _s_samplesPerSweep, notify=_n_samplesPerSweep)

    def _g_sweepsPerScan(self): return self._sweepsPerScan
    def _s_sweepsPerScan(self, value): self._generic_setter('_sweepsPerScan', value)
    sweepsPerScan = Property(int, _g_sweepsPerScan, _s_sweepsPerScan, notify=_n_sweepsPerScan)

    def _g_sweepOverlapRatio(self): return self._sweepOverlapRatio
    def _s_sweepOverlapRatio(self, value): self._generic_setter('_sweepOverlapRatio', value)
    sweepOverlapRatio = Property(float, _g_sweepOverlapRatio, _s_sweepOverlapRatio, notify=_n_sweepOverlapRatio)

    def _g_windowType(self): return self._windowType
    def _s_windowType(self, value): self._generic_setter('_windowType', value)
    windowType = Property(str, _g_windowType, _s_windowType, notify=_n_windowType)

    def _g_windowSize(self): return self._windowSize
    def _s_windowSize(self, value): self._generic_setter('_windowSize', value)
    windowSize = Property(int, _g_windowSize, _s_windowSize, notify=_n_windowSize)

    def _g_smoothingEnabled(self): return self._smoothingEnabled
    def _s_smoothingEnabled(self, value): self._generic_setter('_smoothingEnabled', value)
    smoothingEnabled = Property(bool, _g_smoothingEnabled, _s_smoothingEnabled, notify=_n_smoothingEnabled)

    def _g_smoothingFactor(self): return self._smoothingFactor
    def _s_smoothingFactor(self, value): self._generic_setter('_smoothingFactor', value)
    smoothingFactor = Property(float, _g_smoothingFactor, _s_smoothingFactor, notify=_n_smoothingFactor)

    def _g_scalingEnabled(self): return self._scalingEnabled
    def _s_scalingEnabled(self, value): self._generic_setter('_scalingEnabled', value)
    scalingEnabled = Property(bool, _g_scalingEnabled, _s_scalingEnabled, notify=_n_scalingEnabled)

    def _g_scalingMinDB(self): return self._scalingMinDB
    def _s_scalingMinDB(self, value): self._generic_setter('_scalingMinDB', value)
    scalingMinDB = Property(float, _g_scalingMinDB, _s_scalingMinDB, notify=_n_scalingMinDB)

    def _g_scalingMaxDB(self): return self._scalingMaxDB
    def _s_scalingMaxDB(self, value): self._generic_setter('_scalingMaxDB', value)
    scalingMaxDB = Property(float, _g_scalingMaxDB, _s_scalingMaxDB, notify=_n_scalingMaxDB)

class ScannerInterface(GenericQObject):
    _n_running = Signal()
    _n_scanConfig = Signal()
    _n_deviceInfo = Signal()
    _n_gain = Signal()
    _n_sampleRate = Signal()
    _n_spectrum = Signal()
    _n_progress = Signal()
    _n_scannerInitialized = Signal()
    scannerRunState = Signal(bool)
    # scannerFreqsReady = Signal()
    def __init__(self, *args):
        self._running = False
        self._scanConfig = None
        self._deviceInfo = None
        self._gain = None
        self._sampleRate = None
        self._spectrum = None
        self._scannerInitialized = False
        self._progress = -1
        super().__init__(*args)
        self.scanner = None
        self.scan_thread = None

    @property
    def startFreq(self): return self.scanConfig.startFreq

    @property
    def endFreq(self): return self.scanConfig.endFreq

    def _g_running(self): return self._running
    def _s_running(self, value):
        if value == self._running:
            return
        self._running = value
        self._n_running.emit()
        self.scannerRunState.emit(value)
    running = Property(bool, _g_running, _s_running, notify='_n_running')

    def _g_scannerInitialized(self): return self._scannerInitialized
    def _s_scannerInitialized(self, value): self._generic_setter('_scannerInitialized', value)
    scannerInitialized = Property(bool, _g_scannerInitialized, _s_scannerInitialized, notify=_n_scannerInitialized)

    def _g_scanConfig(self): return self._scanConfig
    def _s_scanConfig(self, value): self._generic_setter('_scanConfig', value)
    scanConfig = Property(ScanConfigData, _g_scanConfig, _s_scanConfig, notify=_n_scanConfig)

    def _g_deviceInfo(self): return self._deviceInfo
    def _s_deviceInfo(self, value): self._generic_setter('_deviceInfo', value)
    deviceInfo = Property(QtCore.QObject, _g_deviceInfo, _s_deviceInfo, notify=_n_deviceInfo)

    def _g_gain(self): return self._gain
    def _s_gain(self, value): self._generic_setter('_gain', value)
    gain = Property(float, _g_gain, _s_gain, notify=_n_gain)

    def _g_sampleRate(self): return self._sampleRate
    def _s_sampleRate(self, value): self._generic_setter('_sampleRate', value)
    sampleRate = Property(float, _g_sampleRate, _s_sampleRate, notify=_n_sampleRate)

    def _g_spectrum(self): return self._spectrum
    def _s_spectrum(self, value): self._generic_setter('_spectrum', value)
    spectrum = Property(object, _g_spectrum, _s_spectrum, notify=_n_spectrum)

    def _g_progress(self): return self._progress
    def _s_progress(self, value): self._generic_setter('_progress', value)
    progress = Property(float, _g_progress, _s_progress, notify=_n_progress)

    def build_scan_config(self):
        conf = config.ScanConfig()
        conf.scan_range = [self.startFreq, self.endFreq]
        conf.device.serial_number = self.deviceInfo.device_serial
        conf.device.gain = self.gain
        conf.sampling.sample_rate = self.sampleRate * 1e3
        conf.sampling.samples_per_sweep = self.scanConfig.samplesPerSweep
        conf.sampling.sweeps_per_scan = self.scanConfig.sweepsPerScan
        conf.sampling.sweep_overlap_ratio = self.scanConfig.sweepOverlapRatio
        conf.sampling.window_size = self.scanConfig.windowSize
        return conf

    # def get_all_freqs(self):
    #     if self.scanner._running.is_set():
    #         return self.scanner.get_all_freqs()

    @Slot(int, float, result=float)
    def getFreqResolution(self, nfft, fs):
        return get_freq_resolution(nfft, fs*1e3) / 1e6

    @Slot()
    def start(self):
        if self.running:
            return
        self._start()

    @Slot()
    def stop(self):
        if not self.running:
            return
        self._stop()

    def _start(self):
        self.scannerInitialized = False
        conf = self.build_scan_config()
        self.scanner = Scanner(config=conf)
        self.spectrum = self.scanner.spectrum
        self.spectrum.name = f'{self.startFreq} - {self.endFreq} (live)'
        self.progress = 0.
        self.running = True
        self.scan_thread = ScanThread(target=self.scanner.run_scan)
        self.scanner.on_progress = self.scan_thread._on_scanner_progress
        self.scan_thread.complete.connect(self.on_scanner_finished)
        self.scan_thread.scannerProgress.connect(self.on_scanner_progress)
        self.scan_init_thread = QObjectThread(target=self.scanner._running.wait)
        self.scan_init_thread.complete.connect(self.on_scanner_ready)
        self.scan_thread.start()
        self.scan_init_thread.start()

    def _stop(self):
        if self.scanner is not None:
            if self.scanner._running.is_set():
                self.scanner.stop_scan()

    @Slot()
    def on_scanner_progress(self, value):
        self.progress = value

    @Slot()
    def on_scanner_finished(self):
        print('on_scanner_finished')
        self.scan_thread.stop()
        print('scan_thread stopped')
        if self.scanConfig.smoothingEnabled:
            self.smooth_scan()
        if self.scanConfig.scalingEnabled:
            self.scale_scan()
        self.scan_thread = None
        self.scanner = None
        self.running = False

    @Slot()
    def smooth_scan(self):
        print('Smoothing scan')
        N = int(self.spectrum.sample_data.size * self.scanConfig.smoothingFactor / 100.)
        self.spectrum.smooth(N)
        # TODO: figure out why interpolate stopped working
        # self.spectrum.interpolate()

    @Slot()
    def scale_scan(self):
        print('Scaling scan')
        conf = self.scanConfig
        self.spectrum.scale(conf.scalingMinDB, conf.scalingMaxDB)

    @Slot()
    def on_scanner_ready(self):
        print('on_scanner_ready: ', threading.current_thread())
        self.scannerInitialized = True
        # self.scannerFreqsReady.emit()
        self.scan_init_thread.stop()
        self.scan_init_thread = None


class ScanThread(QObjectThread):
    scannerProgress = Signal(float)
    def _on_scanner_progress(self, value):
        self.scannerProgress.emit(value)

def register_qml_types():
    QtQml.qmlRegisterType(ScanConfigData, 'ScanTools', 1, 0, 'ScanConfigData')
    QtQml.qmlRegisterType(ScannerInterface, 'ScanTools', 1, 0, 'ScannerInterface')
