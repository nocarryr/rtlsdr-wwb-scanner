import QtQuick 2.0

Item {
    id: root

    property point valueMin: Qt.point(0,1)
    property point valueMax: Qt.point(0,1)
    property point valueSize: Qt.point(0,1)
    property point valueCenter: Qt.point(0,1)
    property point scaleFactor: Qt.point(1,1)
    property bool isZoomed: xScale.isZoomed || yScale.isZoomed

    signal valuesChanged(point min, point max)

    function setValueMin(vmin){
        xScale.valueMin = vmin.x;
        yScale.valueMin = vmin.y;
        queueValueChange();
    }

    function setValueMax(vmax){
        xScale.valueMax = vmax.x;
        yScale.valueMax = vmax.y;
        queueValueChange();
    }

    function setValueExtents(vmin, vmax){
        setValueMin(vmin);
        setValueMax(vmax);
        queueValueChange();
    }

    function setXExtents(xmin, xmax){
        xScale.valueMin = xmin;
        xScale.valueMax = xmax;
        queueValueChange();
    }

    function setYExtents(ymin, ymax){
        yScale.valueMin = ymin;
        yScale.valueMax = ymax;
        queueValueChange();
    }

    function zoomX(factor){
        xScale.zoom(factor);
        queueValueChange();
    }

    function zoomY(factor){
        yScale.zoom(factor);
        queueValueChange();
    }

    function zoom(xFactor, yFactor){
        xScale.zoom(xFactor);
        yScale.zoom(yFactor);
        queueValueChange();
    }

    function setScale(xFactor, yFactor){
        xScale.setScale(xFactor);
        yScale.setScale(yFactor);
        queueValueChange();
    }

    function translateX(offset){
        xScale.translate(offset);
        queueValueChange();
    }

    function translateY(offset){
        yScale.translate(offset);
        queueValueChange();
    }

    function translateToX(pos){
        xScale.translateTo(pos);
        queueValueChange();
    }

    function translateToY(pos){
        yScale.translateTo(pos);
        queueValueChange();
    }

    function translateTo(xPos, yPos){
        xScale.translateTo(xPos);
        yScale.translateTo(yPos);
        queueValueChange();
    }


    ViewScale {
        id: xScale

        onValueMinChanged: { root.valueMin.x = xScale.valueMin }
        onValueMaxChanged: { root.valueMax.x = xScale.valueMax }
        onValueSizeChanged: { root.valueSize.x = xScale.valueSize }
        onValueCenterChanged: { root.valueCenter.x = xScale.valueCenter }
        onScaleFactorChanged: { root.scaleFactor.x = xScale.scaleFactor }
        onValuesChanged: { queueValueChange() }
    }

    ViewScale {
        id: yScale

        onValueMinChanged: { root.valueMin.y = yScale.valueMin }
        onValueMaxChanged: { root.valueMax.y = yScale.valueMax }
        onValueSizeChanged: { root.valueSize.y = yScale.valueSize }
        onValueCenterChanged: { root.valueCenter.y = yScale.valueCenter }
        onScaleFactorChanged: { root.scaleFactor.y = yScale.scaleFactor }
        onValuesChanged: { queueValueChange() }
    }

    function queueValueChange(){
        Qt.callLater(emitValueChange);
    }

    function emitValueChange(){
        root.valuesChanged(root.valueMin, root.valueMax);
    }
}
