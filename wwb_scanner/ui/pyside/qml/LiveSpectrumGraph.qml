import QtQuick 2.0
import QtCharts 2.13
import GraphUtils 1.0

Item {
    id: root

    property var mapper: modelMapper
    property var series
    property alias name: graphData.name
    property var model: tblModel
    property alias minValue: graphData.minValue
    property alias maxValue: graphData.maxValue
    property alias spectrum: graphData.spectrum
    property alias scanner: graphData.scanner

    signal axisExtentsUpdate()


    onSeriesChanged: {
        if (series){
            series.name = root.name;
        }
    }

    onNameChanged: {
        if (series){
            root.series.name = root.name;
        }
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

    LiveSpectrumGraphData {
        id: graphData
        model: tblModel
    }

    HXYModelMapper {
        id: modelMapper
        series: root.series
        model: tblModel
        xRow: 0
        yRow: 1
    }
}
