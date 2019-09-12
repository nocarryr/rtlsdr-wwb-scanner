import QtQuick 2.0
import QtQuick.Controls 2.12

Item {
    id: root
    property ViewXYScale dataExtents
    property ViewXYScale viewScale
    property real viewSize: .25
    property real viewCenter: 0.5
    property alias bgColor: control.bgColor
    property alias gutterColor: control.gutterColor
    property alias scrolling: control.pressed

    onDataExtentsChanged: {
        handleScaleChanges();
        if (dataExtents){
            dataExtents.valuesChanged.connect(handleScaleChanges);
        }
    }

    onViewScaleChanged: {
        handleScaleChanges();
        if (viewScale){
            viewScale.valuesChanged.connect(handleScaleChanges);
        }
    }

    function handleScaleChanges(){
        Qt.callLater(updateView);
    }

    function updateView(){
        var vSize, vMin, vCenter;
        if (dataExtents && viewScale){
            vMin = dataExtents.valueMin.x;
            vSize = viewScale.valueSize.x / dataExtents.valueSize.x;
            vCenter = (viewScale.valueCenter.x - vMin) / dataExtents.valueSize.x;
            if (Number.isNaN(vSize) || Number.isNaN(vCenter)){
                return;
            }
            if (vSize < 0 || vCenter < 0){
                return;
            }
            root.viewSize = vSize;
            root.viewCenter = vCenter;
        }
    }

    function posToViewScale(xPos){
        var vMin = dataExtents.valueMin.x,
            vSize = dataExtents.valueSize.x,
            dataCenter = xPos * vSize + vMin;
        viewScale.translateToX(dataCenter);
    }

    onViewCenterChanged: {
        if (!control.pressed){
            control.setPosition(root.viewCenter);
        }
    }

    Slider {
        id: control
        anchors.left: parent.left
        anchors.right: parent.right
        orientation: Qt.Horizontal

        property color bgColor: palette.midlight
        property color gutterColor: palette.dark

        onMoved: {
            root.posToViewScale(control.value);
        }

        function setPosition(pos){
            if (!control.pressed){
                control.value = pos;
            }
        }

        background: Rectangle {
            x: control.leftPadding + 0
            y: control.topPadding + (control.availableHeight - height) / 2
            implicitWidth: 200
            implicitHeight: 6
            width: control.availableWidth
            height: implicitHeight
            radius: 3
            color: control.bgColor
            scale: control.horizontal && control.mirrored ? -1 : 1

            property real gutterWidth: (root.viewSize * width) / 2
            property real position: control.position * width

            Rectangle {
                x: parent.position
                y: 0
                width: x < parent.width - parent.gutterWidth ? parent.gutterWidth : parent.width - x
                height: 6
                radius: 3
                color: control.gutterColor
            }

            Rectangle {
                x: parent.position - width
                y: 0
                width: parent.position > parent.gutterWidth ? parent.gutterWidth : parent.position
                height: 6
                radius: 3
                color: control.gutterColor
            }
        }
    }
}
