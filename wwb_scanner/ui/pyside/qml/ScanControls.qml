import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import Qt.labs.settings 1.0

RowLayout {
    id: root
    spacing: 0
    property real startFreq: 470.
    property real endFreq: 536.
    property real samplesPerSweep: 8192
    property real sweepsPerScan: 20
    property bool scanReady: true
    signal scannerState(bool state)

    Settings {
        category: 'Scan Config'
        property alias startFreq: root.startFreq
        property alias endFreq: root.endFreq
        property alias samplesPerSweep: root.samplesPerSweep
        property alias sweepsPerScan: root.sweepsPerScan
    }

    NumberInput {
        id: startFreqInput
        name: 'Start Freq'
        value: root.startFreq
        Layout.rightMargin: 0
        onSubmit: {
            root.startFreq = startFreqInput.value;
        }
    }
    NumberInput {
        id: endFreqInput
        name: 'End Freq'
        value: root.endFreq
        Layout.leftMargin: 0
        onSubmit: {
            root.endFreq = endFreqInput.value;
        }
    }

    NumberInput {
        id: samplesPerSweepInput
        name: 'Samples Per Sweep'
        isFloat: false
        value: root.samplesPerSweep
        onSubmit: {
            root.samplesPerSweep = samplesPerSweepInput.value;
        }
    }
    NumberInput {
        id: sweepsPerScanInput
        name: 'Sweeps Per Scan'
        isFloat: false
        value: root.sweepsPerScan
        onSubmit: {
            root.sweepsPerScan = sweepsPerScanInput.value;
        }
    }

    ToolSeparator { }

    ToolButton {
        id: scanStartBtn
        text: "Start"
        // enabled: root.scanReady
        onClicked: root.scannerState(true)
    }
    ToolButton {
        id: scanStopBtn
        text: "Stop"
        // enabled: !root.scanReady
        onClicked: root.scannerState(false)
    }
}
