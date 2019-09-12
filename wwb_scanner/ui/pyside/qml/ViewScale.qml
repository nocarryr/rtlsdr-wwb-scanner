import QtQuick 2.0

Item {
    id: root
    property real valueMin: 0
    property real valueMax: 1
    property real valueSize: valueMax - valueMin
    property real valueCenter: valueMin + ((valueMax - valueMin) / 2)
    property real scaleFactor: 1
    property bool isZoomed: scaleFactor == 1 ? false : true

    signal valuesChanged(real min, real max)

    function zoom(factor) {
        var cnt = root.valueCenter,
            size = root.valueSize * factor,
            vmin = cnt - size / 2,
            vmax = cnt + size / 2;
        root.valueMin = vmin;
        root.valueMax = vmax;
        root.scaleFactor *= factor;
    }

    function setScale(factor){
        var offsetFactor = factor / root.scaleFactor;
        zoom(offsetFactor);
    }

    function translate(offset){
        var vmin = root.valueMin + offset,
            vmax = root.valueMax + offset;
        root.valueMin = vmin;
        root.valueMax = vmax;
    }

    function translateTo(pos){
        var size = root.valueSize,
            vmin = pos - size/2,
            vmax = pos + size/2;
        root.valueMin = vmin;
        root.valueMax = vmax;
    }

    onValueMinChanged: Qt.callLater(emitValueChange, valueMin, valueMax)
    onValueMaxChanged: Qt.callLater(emitValueChange, valueMin, valueMax)
    onValueSizeChanged: Qt.callLater(emitValueChange, valueMin, valueMax)
    onValueCenterChanged: Qt.callLater(emitValueChange, valueMin, valueMax)

    function emitValueChange(vmin, vmax){
        if (root.valueMin != vmin || root.valueMax != vmax){
            return;
        }
        root.valuesChanged(vmin, vmax);
    }

}
