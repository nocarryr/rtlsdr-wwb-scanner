import os
import sys
from pathlib import Path

from wwb_scanner import log_config
log_config.setup(use_console=True, use_file=True)

import logging
logger = logging.getLogger()

from PySide2 import QtCore, QtQml
from PySide2.QtWidgets import QApplication
from PySide2.QtQuick import QQuickView

from wwb_scanner.ui.pyside import get_resource_filename
from wwb_scanner.ui.pyside import device_config, graph, scanner

QT_MSG_TYPES = {
    v:k.split('Qt')[1].split('Msg')[0] for k,v in QtCore.QtMsgType.values.items()
}

def register_qml_types():
    device_config.register_qml_types()
    graph.register_qml_types()
    scanner.register_qml_types()

QML_PATH = get_resource_filename('qml')

def on_app_quit():
    logger.info('exiting application')

def get_qmsg_levelname(mode):
    if mode == QtCore.QtSystemMsg:
        return None
    name = QT_MSG_TYPES.get(mode)
    if name is not None:
        name = name.upper()
    return name

def qt_message_handler(mode, context, message):
    levelname = get_qmsg_levelname(mode)
    if levelname is None:
        return
    lvl = getattr(logging, levelname, logging.INFO)
    # show_trace = lvl not in [logging.INFO, logging.DEBUG]
    fn = QtCore.QUrl(context.file)
    p = Path(fn.toLocalFile())
    try:
        p = p.relative_to(QML_PATH)
    except ValueError:
        p = p.relative_to(p.parent)
    name = '.'.join(p.parts)
    _logger = logging.getLogger(name)
    _logger.log(lvl, message)

def run(argv=None):
    if argv is None:
        argv = sys.argv
    logger.info('starting application')
    app = QApplication(argv)
    app.setOrganizationName('rtlsdr-wwb-scanner')
    app.setApplicationName('wwb_scanner')
    app.aboutToQuit.connect(on_app_quit)
    QtCore.qInstallMessageHandler(qt_message_handler)
    engine = QtQml.QQmlApplicationEngine()
    engine.setBaseUrl(str(QML_PATH))
    engine.addImportPath(str(QML_PATH))
    register_qml_types()
    qml_main = QML_PATH / 'main.qml'
    engine.load(str(qml_main))
    win = engine.rootObjects()[0]
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
