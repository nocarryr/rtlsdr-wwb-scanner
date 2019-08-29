import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import Qt.labs.settings 1.0

RowLayout {
    id: root
    property alias startFreq: settings.startFreq
    property alias endFreq: settings.endFreq
    property bool scanRunning: false
    property bool scanReady: !root.scanRunning
    property alias progress: progressBar.value

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

    ProgressBar {
        id: progressBar
        visible: root.scanRunning
        Component.onCompleted: {
            contentItem.color = '#17a81a';
            background.color = '#aeaec8';
        }
    }

    ToolSeparator { }

    ToolButton {
        id: scanStartBtn
        text: "Start"
        enabled: root.scanReady
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
