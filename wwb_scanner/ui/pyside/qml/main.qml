import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import Qt.labs.settings 1.0
import QtCharts 2.13
import GraphUtils 1.0
import ScanTools 1.0

ApplicationWindow {
    id: window
    visible: true

    width: 800
    height: 600

    Settings {
        property alias x: window.x
        property alias y: window.y
        property alias width: window.width
        property alias height: window.height
    }

    menuBar: MenuBar {
        Menu {
            title: qsTr("&File")
            Action {
                text: qsTr("&Import")
                onTriggered: importDialog.open()
            }
            Action {
                text: qsTr("&Export")
                onTriggered: {
                    exportDialog.graphData = chartWrapper.activeSpectrum;
                    exportDialog.open();
                }
            }
            Action {
                text: qsTr("&Device Settings")
                onTriggered: device_config.open()
            }
            Action {
                text: qsTr("S&can Settings")
                onTriggered: scanControlsDialog.open()
            }
            MenuSeparator { }
            Action {
                text: qsTr("&Quit")
                onTriggered: Qt.quit()
            }
        }
        Menu {
            title: qsTr("&View")
            Action {
                text: qsTr("&Theme")
                onTriggered: themeSelect.open()
            }
        }
    }

    header: ToolBar {
        ScanControls {
            id: scanControls
            anchors.fill: parent
            config: scanConfig
            progress: scanner.progress
            onScannerState: {
                if (state) {
                    scanner.start();
                    chartWrapper.newLiveScan(scanner);
                } else {
                    scanner.stop();
                }
            }
        }
    }

    footer: ToolBar {
        RowLayout {
            anchors.fill: parent

            Label {
                text: chartWrapper.mouseDataPoint.x.toFixed(3);
                Layout.preferredWidth: contentWidth
                Layout.leftMargin: 12
                font.pointSize: 9
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Qt.AlignLeft
            }

            Label {
                text: chartWrapper.mouseDataPoint.y.toFixed(3);
                Layout.preferredWidth: contentWidth
                font.pointSize: 9
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Qt.AlignLeft
            }

            Item { Layout.fillWidth: true }

        }
    }

    StackView {
        anchors.fill: parent
        Graph {
            id: chartWrapper
            anchors.fill: parent
            theme: themeSelect.theme
        }
    }

    ImportDialog {
        id: importDialog
        onImportFile: {
            chartWrapper.loadFromFile(fileName);
        }
    }

    ExportDialog {
        id: exportDialog
    }

    DeviceConfigPopup {
        id: device_config
    }

    ScanControlsDialog {
        id: scanControlsDialog
        scanner: scanner
        config: scanConfig
    }

    ThemeSelectPopup {
        id: themeSelect
    }

    ScanConfig {
        id: scanConfig
    }

    ScannerInterface {
        id: scanner
        scanConfig: scanConfig.model
        deviceInfo: device_config.device ? device_config.device: null
        gain: device_config.gain
        sampleRate: device_config.sampleRate
        onScannerRunState: {
            scanControls.scanRunning = scanner.running;
        }
    }
}
