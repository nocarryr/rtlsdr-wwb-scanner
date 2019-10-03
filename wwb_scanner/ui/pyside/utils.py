import time
import threading
import pathlib

from PySide2 import QtCore, QtQml
from PySide2.QtCore import QObject, Property, Signal
import logging
logger = logging.getLogger(__name__)

def is_pathlike(s):
    if '/' in s or '\\' in s:
        try:
            p = pathlib.PurePosixPath(s)
            uri = p.as_uri()
            return True, p
        except ValueError:
            pass
        try:
            p = pathlib.PureWindowsPath(s)
            uri = p.as_uri()
            return True, p
        except ValueError:
            pass
    return False, None


class GenericQObject(QtCore.QObject):
    def _generic_property_changed(self, attr, old_value, new_value):
        pass
    def _generic_setter(self, attr, value):
        cur_value = getattr(self, attr)
        if cur_value == value:
            return
        setattr(self, attr, value)
        sig_name = f'_n{attr}'
        sig = getattr(self, sig_name)
        sig.emit()
        self._generic_property_changed(attr, cur_value, value)

class IntervalTimer(QObject):
    trigger = Signal()
    start = Signal()
    stop = Signal()
    def __init__(self, parent=None, **kwargs):
        interval_ms = kwargs.pop('interval_ms', 100)
        super().__init__(parent=parent)
        self._interval_ms = interval_ms
        self._active = False
        self._working = False
        self._timer_id = None
        self.start.connect(self._start)
        self.stop.connect(self._stop)

    def _get_interval_ms(self):
        return self._interval_ms
    def _set_interval_ms(self, value):
        if value == self._interval_ms:
            return
        self._interval_ms = value
        if self._active:
            self._stop()
            self._start()
        self._interval_ms_changed.emit()
    @Signal
    def _interval_ms_changed(self):
        pass
    interval_ms = Property(float, _get_interval_ms, _set_interval_ms, notify=_interval_ms_changed)

    def _get_active(self):
        return self._active
    @Signal
    def _on_active_changed(self):
        pass
    active = Property(bool, _get_active)

    def _get_working(self):
        return self._working
    def _set_working(self, value):
        if value == self._working:
            return
        self._working = value
    working = Property(bool, _get_working, _set_working)

    def timerEvent(self, e):
        if self.working:
            return
        self.working = True
        self.trigger.emit()
        self.working = False

    def _start(self):
        self._stop()
        self._active = True
        self._timer_id = self.startTimer(self.interval_ms)

    def _stop(self):
        self._active = False
        timer_id = self._timer_id
        self._timer_id = None
        if timer_id is not None:
            self.killTimer(timer_id)

class QObjectThread(QtCore.QObject):
    started = Signal()
    result = Signal(object)
    error = Signal(object)
    complete = Signal()
    shutdown = Signal()
    def __init__(self, parent=None, **kwargs):
        super().__init__(parent)
        self.target = kwargs.get('target')
        self._thread = QtCore.QThread()
        self._thread.started.connect(self._run)
        self._debug_enabled = False
        self.shutdown.connect(self._thread.quit)
    def start(self):
        self.print_debug('start()')
        self.moveToThread(self._thread)
        self._thread.start()
    def stop(self):
        self.shutdown.emit()
        self.join()
    def join(self):
        # self.shutdown.emit()
        self._thread.wait()
    def _run(self):
        self.print_debug('starting')
        self.started.emit()
        try:
            self.print_debug('run()')
            self.run()
        except Exception as exc:
            self.print_debug('Exception...')
            import traceback
            traceback.print_exc()
            self.error.emit(exc)
            self.shutdown.emit()
            return
        self.print_debug('run() finished')
        self.complete.emit()
        self.print_debug('complete')
        self.shutdown.emit()
        self.print_debug('shutdown')
    def run(self):
        result = self.target()
        self.result.emit(result)
    def print_debug(self, msg):
        if not self._debug_enabled:
            return
        t = threading.current_thread()
        logger.debug(f'{self!r} - {msg} - {t}')
    def __repr__(self):
        return f'<QObjectThread: {self}>'
    def __str__(self):
        return f'{self.target} - {self._thread}'
