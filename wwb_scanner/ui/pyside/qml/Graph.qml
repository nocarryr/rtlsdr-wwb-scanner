import QtQuick 2.0
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.11
import Qt.labs.settings 1.0
import QtCharts 2.13
import GraphUtils 1.0

Item {
    id: root
    anchors.fill: parent

    property alias mouseDataPoint: crosshair.dataValue
    property var models: []
    property var spectrumGraphs: []
    property var activeSpectrum
    property alias activeSeries: chart.activeSeries
    // property var model
    signal newLiveScan(var scanner)
    signal loadFromFile(url fileName)
    signal updateAxisExtents()

    function setActiveSpectrum(spectrum){
        root.activeSpectrum = spectrum;
        root.activeSeries = spectrum.series;
    }

    onNewLiveScan: {
        var scannerArg = scanner;
        var spectrumGraph
        addModel({'scanner':scannerArg, 'isLive':true});
    }

    // onUpdateAxisExtents: { doUpdateAxisExtents() }

    onUpdateAxisExtents: {
        var spectrum, minValue = null, maxValue = null;
        for (var i=0;i<root.spectrumGraphs.length;i++){
            spectrum = root.spectrumGraphs[i];
            if (spectrum.minValue.x == 0 && spectrum.minValue.y == 0){
                continue;
            }
            if (minValue == null){
                minValue = Qt.point(spectrum.minValue.x, spectrum.minValue.y);
            } else {
                if (spectrum.minValue.x < minValue.x){
                    minValue.x = spectrum.minValue.x;
                }
                if (spectrum.minValue.y < minValue.y){
                    minValue.y = spectrum.minValue.y;
                }
            }
            if (maxValue == null){
                maxValue = Qt.point(spectrum.maxValue.x, spectrum.maxValue.y);
            } else {
                if (spectrum.maxValue.x > maxValue.x){
                    maxValue.x = spectrum.maxValue.x;
                }
                if (spectrum.maxValue.y > maxValue.y){
                    maxValue.y = spectrum.maxValue.y;
                }
            }
        }
        if (minValue == null || maxValue == null){
            return;
        }
        axisX.min = minValue.x;
        axisX.max = maxValue.x;
        axisY.min = minValue.y;
        axisY.max = maxValue.y;
    }

    onLoadFromFile: {
        var spectrum = addModel({}, function(obj){
            obj.load_from_file(fileName);
        })
        // graphData.load_from_file(fileName)
    }

    function callable(obj){
        if (typeof(obj) == 'function'){
            return true;
        }
        return false;
    }

    function buildComponent(prnt, uri, props, callback){
        var component = Qt.createComponent(uri),
            obj;
        function onComponentReady(){
            if (component.status == Component.Ready){
                obj = component.createObject(prnt, props);
                if (callable(callback)){
                    callback(obj);
                }
            } else {
                console.error('Error creating object: ', component.errorString());
            }
        }
        if (component.status == Component.Ready){
            obj = component.createObject(prnt, props);
            if (callable(callback)){
                callback(obj);
            }
        } else if (component.status == Component.Error){
            console.error('Error creating object: ', component.errorString());
        } else {
            component.statusChanged.connect(onComponentReady);
        }
    }

    function addModel(props, callback){
        var series = chart.addMappedSeries(),
            qmlFile = 'SpectrumGraph.qml';

        if (props.isLive){
            qmlFile = 'LiveSpectrumGraph.qml';
        }
        props['series'] = series;
        buildComponent(root, qmlFile, props, function(obj){
            obj.index = root.spectrumGraphs.length;
            root.spectrumGraphs.push(obj);
            // chart.addMappedSeries(obj);
            root.activeSpectrum = obj;
            updateAxisExtents();
            obj.axisExtentsUpdate.connect(updateAxisExtents);
            chartSelect.addItem(obj);
            if (callable(callback)){
                callback(obj);
            }
        });
    }

    RowLayout {
        anchors.fill: parent
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ChartView {
                id: chart
                anchors.fill: parent
                antialiasing: true
                legend.visible: false
                animationOptions: ChartView.AllAnimations
                property var activeSeries
                // enabled: false

                ValueAxis {
                    id: axisX
                    // min: root.activeSpectrum ? root.activeSpectrum.minValue.x: 100
                    // max: root.activeSpectrum ? root.activeSpectrum.maxValue.x: 900
                    min: 100
                    max: 900
                    labelFormat: "%07.3f MHz"
                }
                ValueAxis {
                    id: axisY
                    // min: root.activeSpectrum ? root.activeSpectrum.minValue.y: -160
                    // max: root.activeSpectrum ? root.activeSpectrum.maxValue.y: 0
                    min: -160
                    max: 0
                    // base: 10
                    labelFormat: "%07.2f dB"
                }
                function addMappedSeries(){
                    var series = chart.createSeries(ChartView.SeriesTypeLine, 'foo', axisX, axisY);
                    chart.activeSeries = series;
                    return series;
                }

            //     LineSeries {
            //         name: graphData.name ? graphData.name: ''
            //         // HXYModelMapper {
            //         //     model: graphData.model
            //         //     xRow: 0
            //         //     yRow: 1
            //         // }
            //         id: lineSeries
            //         axisX: axisX
            //         axisY: axisY
            //         HXYModelMapper {
            //             id: modelMapper
            //             series: lineSeries
            //             model: tblModel
            //             xRow: 0
            //             yRow: 1
            //
            //         }
            }

            Crosshair {
                id: crosshair
                anchors.fill: parent

            }


            MouseArea {
                id: mouseArea
                anchors.fill: parent
                hoverEnabled: true

                property point dataPoint: Qt.point(0, 0)
                property point dataPos: Qt.point(0, 0)

                onPositionChanged: {
                    if (!mouseArea.containsMouse){
                        return;
                    }
                    mouse.accepted = true;
                    // var pt = Qt.point(mouse.x, mouse.y);
                    // console.log(pt.x, pt.y);
                    var pt = mouseArea.mapToGlobal(mouse.x, mouse.y);
                    timedMouse.setPoint(pt);
                }

                Timer {
                    id: timedMouse
                    interval: 1
                    repeat: false
                    property var point

                    function setPoint(pt) {
                        timedMouse.stop();
                        timedMouse.point = pt;
                        timedMouse.start();
                    }

                    onTriggered: {
                        var series = chart.activeSeries,
                            spectrum = root.activeSpectrum;
                        if (!series || !spectrum){
                            return;
                        }
                        var pos = chart.mapFromGlobal(timedMouse.point.x, timedMouse.point.y),
                            mouseDataPoint = chart.mapToValue(pos, series),
                            dataPoint = spectrum.get_nearest_by_x(mouseDataPoint.x),
                            dataPos;
                        if (dataPoint.x < 0) {
                            dataPos = dataPoint;
                        } else {
                            dataPos = chart.mapToPosition(dataPoint, series);
                        }
                        crosshair.setData(dataPos, dataPoint);
                        // mouseArea.dataPoint = dataPoint;
                    }
                }
            }
        }
        ChartSelect {
            id: chartSelect
            Layout.minimumWidth: 200
            Layout.fillHeight: true
            activeSpectrum: root.activeSpectrum

            onSelected: {
                setActiveSpectrum(spectrum);
            }
        }
    }
}
