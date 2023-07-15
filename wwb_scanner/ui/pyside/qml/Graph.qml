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
    property alias theme: chart.theme
    property var spectrumGraphs: []
    property var activeSpectrum
    property alias activeSeries: chart.activeSeries
    signal newLiveScan(var scanner)
    signal loadFromFile(url fileName)
    signal updateAxisExtents()
    signal seriesClicked(int index)

    function setActiveSpectrum(spectrum){
        root.activeSpectrum = spectrum;
        root.activeSeries = spectrum.series;
    }

    onNewLiveScan: {
        var scannerArg = scanner;
        var spectrumGraph
        addModel({'scanner':scannerArg, 'isLive':true});
    }

    onSeriesClicked: {
        var spectrumGraph = root.spectrumGraphs[index];
        setActiveSpectrum(spectrumGraph);
    }

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
        viewController.setDataExtents(minValue, maxValue);
    }

    onLoadFromFile: {
        var spectrum = addModel({}, function(obj){
            obj.load_from_file(fileName);
        });
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
        props['graphParent'] = root;
        buildComponent(root, qmlFile, props, function(obj){
            obj.index = root.spectrumGraphs.length;
            root.spectrumGraphs.push(obj);
            root.activeSpectrum = obj;
            updateAxisExtents();
            obj.axisExtentsUpdate.connect(updateAxisExtents);
            obj.seriesClicked.connect(root.seriesClicked);
            chartSelect.addItem(obj);
            if (callable(callback)){
                callback(obj);
            }
        });
    }

    GraphViewController {
        id: viewController
        axisX: axisX
        axisY: axisY
    }

    GraphHViewControls {
        id: hViewControls
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        height: parent.height * .1
        controller: viewController
    }

    RowLayout {
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: hViewControls.bottom
        anchors.bottom: parent.bottom
        spacing: 1
        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true
            ChartView {
                id: chart
                anchors.fill: parent
                antialiasing: true
                legend.visible: false
                animationOptions: ChartView.SeriesAnimations
                property var activeSeries

                ValueAxis {
                    id: axisX
                    min: 100
                    max: 900
                    labelFormat: "%07.3f MHz"
                }
                ValueAxis {
                    id: axisY
                    min: -160
                    max: 0
                    labelFormat: "%07.2f dB"
                }

                function addMappedSeries(){
                    var series = chart.createSeries(ChartView.SeriesTypeLine, 'foo', axisX, axisY);
                    chart.activeSeries = series;
                    return series;
                }

                states: [
                    State {
                        name: 'NORMAL'
                        when: !hViewControls.scrolling
                        PropertyChanges { target:chart; animationOptions:ChartView.SeriesAnimations }
                    },
                    State {
                        name: 'SCROLLING'
                        when: hViewControls.scrolling
                        PropertyChanges { target:chart; animationOptions:ChartView.NoAnimation }
                    }
                ]
            }

            UHFChannels {
                id: channelLabels
                axisX: axisX
                chart: chart
                x: chart.plotArea.x
                y: chart.plotArea.y
                width: chart.plotArea.width
                height: 30
            }

            Crosshair {
                id: crosshair
                x: chart.plotArea.x
                y: chart.plotArea.y
                width: chart.plotArea.width
                height: chart.plotArea.height
                enabled: false
            }


            MouseArea {
                id: mouseArea
                anchors.fill: parent
                hoverEnabled: true
                propagateComposedEvents: true

                onPositionChanged: {
                    mouse.accepted = false;
                    if (!mouseArea.containsMouse){
                        return;
                    }
                    var pt = mouseArea.mapToGlobal(mouse.x, mouse.y);
                    timedMouse.setPoint(pt);
                }

                onClicked: { mouse.accepted = false }
                onPressed: { mouse.accepted = false }
                onReleased: { mouse.accepted = false }

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
                        const series = chart.activeSeries;
                        const spectrum = root.activeSpectrum;
                        if (!series || !spectrum){
                            return;
                        }
                        const curPt = timedMouse.point;
                        const pos = chart.mapFromGlobal(curPt.x, curPt.y);
                        const mouseDataPoint = chart.mapToValue(pos, series);
                        const dataPoint = spectrum.get_nearest_by_x(mouseDataPoint.x);
                        let dataPos;
                        if (dataPoint.x < 0) {
                            dataPos = dataPoint;
                        } else {
                            dataPos = chart.mapToPosition(dataPoint, series);
                            dataPos = chart.mapToItem(crosshair, dataPos.x, dataPos.y);
                        }
                        crosshair.setData(dataPos, dataPoint);
                    }
                }
            }
        }

        ChartSelect {
            id: chartSelect
            Layout.minimumWidth: 200
            Layout.fillHeight: true
            Layout.leftMargin: 0
            Layout.rightMargin: 5
            Layout.topMargin: 5
            activeSpectrum: root.activeSpectrum

            onSelected: {
                setActiveSpectrum(spectrum);
            }
        }
    }
}
