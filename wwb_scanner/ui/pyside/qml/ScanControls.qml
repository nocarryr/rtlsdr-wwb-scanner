import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12

RowLayout {
    id: root
    property ScanConfig config
    property alias startFreq: startFreqInput.value
    property alias endFreq: endFreqInput.value
    property bool configReady: false
    property bool scanRunning: false
    property bool scanReady: !root.scanRunning
    property alias progress: progressBar.value

    signal scannerState(bool state)

    onConfigChanged: {
        if (!config){
            return;
        }
        configUpdateCallback();
        root.configReady = true;
        config.configUpdate.connect(configUpdateCallback);
    }

    function configUpdateCallback(){
        if (root.startFreq != config.startFreq){
            root.startFreq = config.startFreq;
        }
        if (root.endFreq != config.endFreq){
            root.endFreq = config.endFreq;
        }
    }

    NumberInput {
        id: startFreqInput
        name: 'Start Freq'
        Layout.leftMargin: 6
        labelFontSize: 10
        onSubmit: {
            root.config.startFreq = startFreqInput.value;
        }
    }
    NumberInput {
        id: endFreqInput
        name: 'End Freq'
        labelFontSize: 10
        onSubmit: {
            root.config.endFreq = endFreqInput.value;
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
