import QtQuick 2.0
import QtCharts 2.13

Item {
    id: root

    property ValueAxis axisX
    property UHFChannels parentChannels

    anchors.top: parent.top
    anchors.bottom: parent.bottom

    property int channel: 14
    property real bandwidth: 6.0
    property real centerFreq: 473.0
    property real centerX: x + width / 2
    property real lowerFreq: centerFreq - bandwidth / 2
    property real upperFreq: centerFreq + bandwidth / 2
    property real maskedX: 0
    property real maskedWidth: 1
    property real parentWidth: 1
    property color bgColor: Qt.rgba(0,0,0,0)
    property color borderColor: '#808080'
    property color textColor: '#f0f0f0'

    signal updatePosition()

    onAxisXChanged: { Qt.callLater(updatePosition) }
    onParentChannelsChanged: { Qt.callLater(updatePosition) }

    Connections {
        target: root.parentChannels
        function onGeometryUpdate() {
            root.parentWidth = root.parentChannels.width;
            Qt.callLater(updatePosition);
        }
        function onRangeUpdate() { Qt.callLater(updatePosition) }
    }

    onUpdatePosition: {
        if (!parentChannels){
            return;
        }
        var minFreq = parentChannels.min, maxFreq = parentChannels.max,
            axisWidth = parentChannels.width,
            axisHeight = parentChannels.height,
            rightEdge, leftEdge;
        leftEdge = (root.lowerFreq - minFreq) / parentChannels.freqRangeSize * axisWidth;
        root.x = leftEdge
        root.width = root.bandwidth / parentChannels.freqRangeSize * axisWidth;
        rightEdge = leftEdge + root.width;
        if (rightEdge <= 0 || leftEdge >= axisWidth){
            root.visible = false;
            return;
        }
        var leftClip = leftEdge < 0,
            rightClip = rightEdge > axisWidth,
            maskedX, maskedWidth;

        if (leftClip && rightClip){
            maskedX = -leftEdge;
            maskedWidth = axisWidth;
        } else if (leftClip){
            maskedX = -leftEdge;
            maskedWidth = root.width - maskedX;
        } else if (rightClip){
            maskedX = 0;
            maskedWidth = root.width - (rightEdge-axisWidth);
        } else {
            maskedX = 0;
            maskedWidth = root.width;
        }
        root.maskedX = maskedX;
        root.maskedWidth = maskedWidth;
        root.visible = true;
    }

    Rectangle {
        id: bgRect
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        x: root.maskedX
        width: root.maskedWidth
        color: root.bgColor
        border.color: root.borderColor
        border.width: 1
    }

    Text {
        id: lbl
        anchors.fill: parent
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        property real contentLeft: root.centerX - lbl.contentWidth/2
        property real contentRight: root.centerX + lbl.contentWidth/2
        visible: lbl.contentLeft >= 0 && lbl.contentRight <= root.parentWidth
        text: root.channel.toString()
        color: root.textColor
        fontSizeMode: Text.Fit
    }
}
