import time
from PySide2 import QtCore, QtQml
from PySide2.QtCore import QObject, Property, Signal

class GenericQObject(QtCore.QObject):
    def _generic_setter(self, attr, value):
        cur_value = getattr(self, attr)
        if cur_value == value:
            return
        setattr(self, attr, value)
        sig_name = f'_n{attr}'
        sig = getattr(self, sig_name)
        sig.emit()

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
