import QtQuick 2.0
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.11

Item {
    id: root

    property var axisX
    property var axisY
    property var chart

    property ViewXYScale dataExtents: dataExtents
    property ViewXYScale viewScale: viewScale
    property alias dataMin: dataExtents.valueMin
    property alias dataMax: dataExtents.valueMax
    property point origDataMin: Qt.point(0, 1)
    property point origDataMax: Qt.point(0, 1)
    property alias dataCenter: dataExtents.valueCenter
    property alias dataZoomFactor: dataExtents.scaleFactor
    property alias viewMin: viewScale.valueMin
    property alias viewMax: viewScale.valueMax
    property alias viewCenter: viewScale.valueCenter
    property alias viewZoomFactor: viewScale.scaleFactor
    property real defaultZoomIncr: 0.125
    property real scrollIncrFactor: 0.125
    property point scrollIncr: Qt.point(1, 1)
    property alias isZoomed: viewScale.isZoomed
    property bool isScrolled: false
    property bool isDefault: root.isZoomed || root.isScrolled ? false : true

    function setDataExtents(vmin, vmax){
        root.origDataMin = vmin;
        root.origDataMax = vmax;
        dataExtents.setValueExtents(vmin, vmax);
    }

    onAxisXChanged: {
        if (!root.axisX){
            return;
        }
        if (root.dataMin.x == 0 && root.dataMax.x == 1){
            dataExtents.setXExtents(root.axisX.min, root.axisX.max);
        }
    }

    onAxisYChanged: {
        if (!root.axisY){
            return;
        }
        if (root.dataMin.y == 0 && root.dataMax.y == 1){
            dataExtents.setYExtents(root.axisY.min, root.axisY.max);
        }
    }

    onDataMinChanged: {
        if (root.isDefault){
            viewScale.setValueMin(root.dataMin);
            updateAxes();
        }
    }

    onDataMaxChanged: {
        if (root.isDefault){
            viewScale.setValueMax(root.dataMax);
            updateAxes();
        }
    }

    function updateScrollIncr(){
        var size = viewScale.valueSize;
        root.scrollIncr.x = size.x * root.scrollIncrFactor;
        root.scrollIncr.y = size.y * root.scrollIncrFactor;
    }

    function updateAxes(){
        if (root.axisX && root.axisY){
            root.axisX.min = root.viewMin.x;
            root.axisX.max = root.viewMax.x;
            root.axisY.min = root.viewMin.y;
            root.axisY.max = root.viewMax.y;
        }
    }

    function scrollLeft(){
        var curPos = root.viewCenter.x,
            newPos = curPos - root.scrollIncr.x;
        viewScale.translateToX(newPos);
        if (root.viewMin.x < root.dataMin.x){
            viewScale.translateToX(curPos);
            // dataExtents.setValueMin(Qt.point(root.viewMin.x, root.dataMin.y));
        }
        root.isScrolled = true;
    }

    function scrollRight(){
        var curPos = root.viewCenter.x,
            newPos = curPos + root.scrollIncr.x;
        viewScale.translateToX(newPos);
        if (root.viewMax.x > root.dataMax.x){
            viewScale.translateToX(curPos);
            // dataExtents.setValueMax(Qt.point(root.viewMax.x, root.dataMax.y));
        }
        root.isScrolled = true;
    }

    function reset(){
        dataExtents.setValueExtents(root.origDataMin, root.origDataMax);
        viewScale.translateTo(root.dataCenter.x, root.dataCenter.y);
        viewScale.setScale(1, 1);
        root.isScrolled = false;
    }

    ViewXYScale {
        id: dataExtents
        onValuesChanged: {
            if (root.isDefault){
                viewScale.setValueExtents(min, max);
            }
        }
    }
    ViewXYScale {
        id: viewScale
        onValuesChanged: {
            root.updateAxes();
        }
        onValueSizeChanged: {
            root.updateScrollIncr();
        }
    }
}
