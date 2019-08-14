import QtQuick 2.0

Canvas {
    id: root
    enabled: false
    property color bgColor: Qt.rgba(0, 0, 0, 0)
    property color fgColor: Qt.rgba(0, 0, 1, 1)
    property point dataPos: Qt.point(-1, -1)
    property point dataValue: Qt.point(-1, -1)

    signal setData(point pos, point value)

    onSetData: {
        root.dataPos = pos;
        root.dataValue = value;
        root.requestPaint();
    }

    onPaint: {
        var ctx = getContext('2d'),
            width = root.width,
            height = root.height,
            pos = root.dataPos;

        ctx.clearRect(0, 0, width, height);
        ctx.reset();
        ctx.fillStyle = root.bgColor;
        if (pos.x > 0 && pos.y > 0){
            ctx.lineWidth = 1;
            ctx.strokeStyle = root.fgColor;
            ctx.moveTo(0, pos.y);
            ctx.lineTo(width, pos.y);
            ctx.moveTo(pos.x, 0);
            ctx.lineTo(pos.x, height);
            ctx.stroke();
        }
    }
}
