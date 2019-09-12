import QtQuick 2.0
import Qt.labs.settings 1.0
import ScanTools 1.0

Item {
    id: root

    property ScanConfigData model: model
    property alias startFreq: model.startFreq
    property alias endFreq: model.endFreq
    property alias samplesPerSweep: model.samplesPerSweep
    property alias sweepsPerScan: model.sweepsPerScan
    property alias sweepOverlapRatio: model.sweepOverlapRatio
    property alias windowType: model.windowType
    property alias windowSize: model.windowSize
    property alias smoothingEnabled: model.smoothingEnabled
    property alias smoothingFactor: model.smoothingFactor
    property alias scalingEnabled: model.scalingEnabled
    property alias scalingMinDB: model.scalingMinDB
    property alias scalingMaxDB: model.scalingMaxDB

    signal configUpdate()

    ScanConfigData {
        id: model
        startFreq: 470.
        endFreq: 536.
        samplesPerSweep: 8192
        sweepsPerScan: 20
        sweepOverlapRatio: 0.5
        windowType: 'hann'
        windowSize: 128
        smoothingEnabled: false
        smoothingFactor: 1.0
        scalingEnabled: false
        scalingMinDB: -140
        scalingMaxDB: -55

        onConfigUpdate: {
            root.configUpdate();
        }
    }

    Settings {
        id: settings
        category: 'Scan Config'
        property alias startFreq: model.startFreq
        property alias endFreq: model.endFreq
        property alias samplesPerSweep: model.samplesPerSweep
        property alias sweepsPerScan: model.sweepsPerScan
        property alias sweepOverlapRatio: model.sweepOverlapRatio
        property alias windowType: model.windowType
        property alias windowSize: model.windowSize
        property alias smoothingEnabled: model.smoothingEnabled
        property alias smoothingFactor: model.smoothingFactor
        property alias scalingEnabled: model.scalingEnabled
        property alias scalingMinDB: model.scalingMinDB
        property alias scalingMaxDB: model.scalingMaxDB
    }
}
