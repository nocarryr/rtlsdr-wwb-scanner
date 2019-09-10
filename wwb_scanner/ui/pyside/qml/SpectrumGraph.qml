import QtQuick 2.0
import QtCharts 2.13
import GraphUtils 1.0

Item {
    id: root

    property var graphParent
    property var mapper: modelMapper
    property alias series: modelMapper.series
    property alias name: graphData.name
    property var model: tblModel
    property alias minValue: graphData.minValue
    property alias maxValue: graphData.maxValue
    property alias spectrum: graphData.spectrum
    property alias graphVisible: graphData.graphVisible
    property int index
    property alias color: graphData.color
    property bool seriesInitialized: false
    property bool selected: true
    property real seriesWidth: selected ? 2 : 1

    signal axisExtentsUpdate()
    signal seriesClicked(int index)

    onSeriesChanged: {
        if (series){
            series.name = root.name;
            series.width = root.seriesWidth;
            if (root.seriesInitialized){
                series.color = root.color;
            } else {
                root.color = series.color;
            }
            root.seriesInitialized = true;
        }
    }

    Connections {
        target: root.graphParent
        onActiveSpectrumChanged: {
            root.selected = root.graphParent.activeSpectrum.index == root.index;
        }
    }

    Connections {
        target: root.series
        onClicked: {
            root.seriesClicked(root.index);
        }
    }

    onNameChanged: {
        if (series){
            root.series.name = root.name;
        }
    }

    onSeriesWidthChanged: {
        if (root.series){
            root.series.width = root.seriesWidth;
        }
    }

    onGraphVisibleChanged: {
        if (!root.series){
            return;
        }
        root.series.visible = root.graphVisible;
    }

    onMinValueChanged: { axisExtentsUpdate() }
    onMaxValueChanged: { axisExtentsUpdate() }

    function load_from_file(fileName){
        graphData.load_from_file(fileName);
    }

    function save_to_file(fileName){
        graphData.save_to_file(fileName);
    }

    function get_nearest_by_x(value){
        return graphData.get_nearest_by_x(value);
    }

    GraphTableModel {
        id: tblModel
    }

    SpectrumGraphData {
        id: graphData
        model: tblModel
        // onMinValueChanged: {
        //     root.series.axisX.min = graphData.minValue.x;
        //     root.series.axisY.min = graphData.minValue.y;
        // }
        // onMaxValueChanged: {
        //     root.series.axisX.max = graphData.maxValue.x;
        //     root.series.axisY.max = graphData.maxValue.y;
        // }
        onColorChanged: {
            if (root.series){
                if (root.series.color != graphData.color){
                    root.series.color = graphData.color;
                }
            }
        }
    }

    HXYModelMapper {
        id: modelMapper
        series: root.series
        model: tblModel
        xRow: 0
        yRow: 1
    }
}
