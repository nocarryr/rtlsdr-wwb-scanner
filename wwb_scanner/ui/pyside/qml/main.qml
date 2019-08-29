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
            Action { text: qsTr("&Quit") }
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
            // scanReady: !scanner.running
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
                text: chartWrapper.mouseDataPoint.x.toString();
            }
            Label {
                text: chartWrapper.mouseDataPoint.y.toString();
            }
        }
    }
    StackView {
        anchors.fill: parent
        Graph {
            id: chartWrapper
            anchors.fill: parent
            theme: themeSelect.theme
            // property var graph
            // property var spectrum_data

            function addSpectrum(fileName) {
                chartWrapper.loadFromFile(fileName);
                // // chartWrapper.spectrum_data = spectrum_data;
                // var component = Qt.createComponent('Graph.qml'),
                //     graphCtx = {},//{'model':spectrum_data.model},
                //     graph;
                // function onComponentReady(){
                //     if (component.status == Component.Ready){
                //         graph = component.createObject(chartWrapper, graphCtx);
                //         chartWrapper.graph = graph;
                //         graph.loadFromFile(fileName);
                //     } else {
                //         console.error('Error creating object: ', component.errorString());
                //     }
                // }
                // if (component.status == Component.Ready){
                //     graph = component.createObject(chartWrapper, graphCtx);
                //     chartWrapper.graph = graph;
                //     graph.loadFromFile(fileName);
                // } else if (component.status == Component.Error){
                //     console.error('Error creating object: ', component.errorString());
                // } else {
                //     component.statusChanged.connect(onComponentReady);
                // }
            }
        }
        // ChartView {
        //     id: chart
        //     anchors.fill: parent
        //     property var defaultAxes: [null, null]
        //     property var spectra: []
        //
        //     function addSpectrum(spectrum_data) {
        //         var series;
        //         if (false){//chart.defaultAxes[0]){
        //             series = chart.createSeries(
        //                 ChartView.SeriesTypeLine,
        //                 chart.defaultAxes[0],
        //                 chart.defaultAxes[1],
        //             );
        //         } else {
        //             series = chart.createSeries(ChartView.SeriesTypeLine, spectrum_data.name)
        //             // chart.defaultAxes[0] = chart.axisX(series);
        //             // chart.defaultAxes[1] = chart.axisY(series);
        //         }
        //         console.log('series created');
        //         chart.spectra.push(spectrum_data);
        //         console.log('item appended');
        //         spectrum_data.series = series;
        //         console.log('series attached');
        //     }
        // }
    }

    ImportDialog {
        id: importDialog
        onImportFile: {
            console.log(fileName);
            // spectrumLoader.load_from_file(fileName);
            // var spec_data = spectrumLoader.instance;

            chartWrapper.addSpectrum(fileName);
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
    }

    ThemeSelectPopup {
        id: themeSelect
    }

    SpectrumLoader {
        id: spectrumLoader

    }

    ScannerInterface {
        id: scanner
        startFreq: scanControls.startFreq
        endFreq: scanControls.endFreq
        samplesPerSweep: scanControlsDialog.samplesPerSweep
        sweepsPerScan: scanControlsDialog.sweepsPerScan
        sweepOverlapRatio: scanControlsDialog.sweepOverlapRatio
        windowSize: scanControlsDialog.windowSize
        smoothingEnabled: scanControlsDialog.smoothingEnabled
        smoothingFactor: scanControlsDialog.smoothingFactor
        deviceInfo: device_config.device ? device_config.device: null
        gain: device_config.gain
        sampleRate: device_config.sampleRate
    }
}