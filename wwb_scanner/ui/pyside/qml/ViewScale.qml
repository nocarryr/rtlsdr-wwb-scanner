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
        queueValueChange();
    }

    function setScale(factor){
        var offsetFactor = factor / root.scaleFactor;
        zoom(offsetFactor);
        queueValueChange();
    }

    function translate(offset){
        var vmin = root.valueMin + offset,
            vmax = root.valueMax + offset;
        root.valueMin = vmin;
        root.valueMax = vmax;
        queueValueChange();
    }

    function translateTo(pos){
        var size = root.valueSize,
            vmin = pos - size/2,
            vmax = pos + size/2;
        root.valueMin = vmin;
        root.valueMax = vmax;
        queueValueChange();
    }

    onValueMinChanged: { queueValueChange() }
    onValueMaxChanged: { queueValueChange() }
    onValueSizeChanged: { queueValueChange() }
    onValueCenterChanged: { queueValueChange() }


    function queueValueChange(){
        Qt.callLater(emitValueChange);
    }

    function emitValueChange(){
        root.valuesChanged(root.valueMin, root.valueMax);
    }

}
