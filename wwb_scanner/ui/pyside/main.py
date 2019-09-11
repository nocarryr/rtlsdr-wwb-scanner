import os
import sys
from pathlib import Path

from PySide2 import QtCore, QtQml
from PySide2.QtWidgets import QApplication
from PySide2.QtQuick import QQuickView

from . import get_resource_filename
from wwb_scanner.ui.pyside import device_config, graph, scanner

def register_qml_types():
    device_config.register_qml_types()
    graph.register_qml_types()
    scanner.register_qml_types()

QML_PATH = get_resource_filename('qml')

def run(argv=None):
    if argv is None:
        argv = sys.argv
    app = QApplication(argv)
    app.setOrganizationName('rtlsdr-wwb-scanner')
    app.setApplicationName('wwb_scanner')
    engine = QtQml.QQmlApplicationEngine()
    engine.setBaseUrl(str(QML_PATH))
    engine.addImportPath(str(QML_PATH))
    register_qml_types()
    qml_main = QML_PATH / 'main.qml'
    engine.load(str(qml_main))
    # view = QQuickView()
    # view.setSource(MAIN)
    # view.show()
    win = engine.rootObjects()[0]
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    run()
