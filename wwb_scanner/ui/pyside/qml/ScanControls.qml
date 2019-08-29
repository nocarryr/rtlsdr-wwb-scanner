import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import Qt.labs.settings 1.0

RowLayout {
    id: root
    property alias startFreq: settings.startFreq
    property alias endFreq: settings.endFreq
    property bool scanReady: true
    signal scannerState(bool state)

    Settings {
        id: settings
        category: 'Scan Config'
        property real startFreq: 470.
        property real endFreq: 536.
    }

    NumberInput {
        id: startFreqInput
        name: 'Start Freq'
        Layout.leftMargin: 6
        labelFontSize: 10
        value: root.startFreq
        onSubmit: {
            root.startFreq = startFreqInput.value;
        }
    }
    NumberInput {
        id: endFreqInput
        name: 'End Freq'
        labelFontSize: 10
        value: root.endFreq
        onSubmit: {
            root.endFreq = endFreqInput.value;
        }
    }

    ToolSeparator { }

    Item {
        Layout.fillWidth: true
        Layout.fillHeight: true
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
        Layout.rightMargin: 6
        // enabled: !root.scanReady
        onClicked: root.scannerState(false)
    }
}
