import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import ScanTools 1.0

Dialog {
    id: root
    property ScanConfig config
    property ScannerInterface scanner
    property real sampleRate
    property alias samplesPerSweep: samplesPerSweepInput.value
    property alias sweepsPerScan: sweepsPerScanInput.value
    property alias sweepOverlapRatio: sweepOverlapRatioInput.value
    property alias windowType: windowCombo.textValue
    property alias windowSize: windowSizeInput.value
    property alias smoothingEnabled: smoothingSwitch.checked
    property alias smoothingFactor: smoothingFactorInput.value
    property alias scalingEnabled: scalingSwitch.checked
    property alias scalingMinDB: scalingMinDBInput.value
    property alias scalingMaxDB: scalingMaxDBInput.value

    onWindowTypeChanged: {
        if (!root.windowType){
            return;
        }
        windowCombo.setFromString(root.windowType);
    }

    function getFreqResolution(){
        if (!root.scanner){
            return -1;
        }
        // if (!root.scanner.deviceInfo){
        //     return -1;
        // }
        var fs = root.sampleRate,
            nfft = root.windowSize;
        if (!fs || !nfft){
            return -1;
        }
        var r = root.scanner.getFreqResolution(nfft, fs);
        freqResolutionLbl.value = r;
    }

    onScannerChanged: {
        root.sampleRate = Qt.binding(function(){ return root.scanner.sampleRate });
        getFreqResolution();
    }

    onSampleRateChanged: { getFreqResolution() }
    onWindowSizeChanged: { getFreqResolution() }

    ColumnLayout {
        anchors.fill: parent

        GroupBox {
            title: 'Sweep Parameters'

            RowLayout {
                anchors.fill: parent
                NumberInput {
                    id: samplesPerSweepInput
                    name: 'Samples Per Sweep'
                    isFloat: false
                    showFrame: true
                }
                NumberInput {
                    id: sweepsPerScanInput
                    name: 'Sweeps Per Scan'
                    isFloat: false
                    showFrame: true
                }
                NumberInput {
                    id: sweepOverlapRatioInput
                    name: 'Sweep Overlap Ratio'
                    showFrame: true
                }
            }
        }

        GroupBox {
            title: 'Window Parameters'

            RowLayout {
                anchors.fill: parent

                ComboBox {
                    id: windowCombo
                    property string textValue
                    model: [
                        'barthann', 'bartlett', 'blackman', 'blackmanharris',
                        'bohman', 'boxcar', 'cosine', 'flattop', 'general_cosine',
                        'general_hamming', 'hamming', 'hann', 'hanning',
                        'nuttall', 'parzen', 'triang',
                    ]
                    onTextValueChanged: { windowCombo.setFromString(windowCombo.textValue) }
                    function setFromString(wname){
                        var idx = windowCombo.find(wname);
                        windowCombo.currentIndex = idx;
                        return idx;
                    }
                }

                NumberInput {
                    id: windowSizeInput
                    name: 'Window Size'
                    isFloat: false
                    showFrame: true
                }
                Label {
                    id: freqResolutionLbl
                    property real value
                    property bool isEvenFreq: freqResolutionLbl.value*1e6 == parseInt(freqResolutionLbl.value*1e6)
                    text: "Resolution: \n" + freqResolutionLbl.value.toString() + " MHz"
                    font.pointSize: 9
                    states: [
                        State {
                            name: 'normal'
                            when: freqResolutionLbl.isEvenFreq
                            PropertyChanges { target: freqResolutionLbl; color: '#008000' }
                        },
                        State {
                            name: 'critical'
                            when: !freqResolutionLbl.isEvenFreq
                            PropertyChanges { target: freqResolutionLbl; color: '#800000'}
                        }
                    ]
                }
            }
        }

        GroupBox {
            title: 'Smoothing'

            RowLayout {
                anchors.fill: parent
                Switch {
                    id: smoothingSwitch
                    text: 'Enabled'
                }
                NumberInput {
                    id: smoothingFactorInput
                    name: 'Factor'
                    showFrame: true
                }
            }
        }

        GroupBox {
            title: 'Scaling'

            RowLayout {
                anchors.fill: parent
                Switch {
                    id: scalingSwitch
                    text: 'Enabled'
                }
                NumberInput {
                    id: scalingMinDBInput
                    name: 'Minimum (dB)'
                    showFrame: true
                }
                NumberInput {
                    id: scalingMaxDBInput
                    name: 'Maximum (dB)'
                    showFrame: true
                }
            }
        }
    }

    standardButtons: Dialog.Ok | Dialog.Cancel

    function commitSettings(){
        config.samplesPerSweep = root.samplesPerSweep;
        config.sweepsPerScan = root.sweepsPerScan;
        config.sweepOverlapRatio = root.sweepOverlapRatio;
        config.windowType = root.windowType;
        config.windowSize = root.windowSize;
        config.smoothingEnabled = root.smoothingEnabled;
        config.smoothingFactor = root.smoothingFactor;
        config.scalingEnabled = root.scalingEnabled;
        config.scalingMinDB = root.scalingMinDB;
        config.scalingMaxDB = root.scalingMaxDB;
    }

    function reloadSettings(){
        if (!config){
            return;
        }
        root.samplesPerSweep = config.samplesPerSweep;
        root.sweepsPerScan = config.sweepsPerScan;
        root.sweepOverlapRatio = config.sweepOverlapRatio;
        root.windowType = config.windowType;
        root.windowSize = config.windowSize;
        root.smoothingEnabled = config.smoothingEnabled;
        root.smoothingFactor = config.smoothingFactor;
        root.scalingEnabled = config.scalingEnabled;
        root.scalingMinDB = config.scalingMinDB;
        root.scalingMaxDB = config.scalingMaxDB;
    }

    onAccepted: {
        commitSettings();
        root.close();
    }

    onRejected: {
        reloadSettings();
        root.close();
    }
    onAboutToShow: {
        reloadSettings();
    }
    Component.onCompleted: {
        reloadSettings();
    }
}
