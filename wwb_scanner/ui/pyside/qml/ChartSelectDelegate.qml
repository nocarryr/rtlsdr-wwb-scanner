import QtQuick 2.12
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import GraphUtils 1.0

RadioDelegate {
    id: control
    property string itemName
    property color itemColor: "#8080FF"
    property int itemIndex


    contentItem: Label {
        // rightPadding: control.indicator.width + control.spacing
        rightPadding: 0
        leftPadding: control.indicator.width + control.spacing
        text: control.itemName
        font: control.font
        // opacity: enabled ? 1.0: 0.3
        color: control.itemColor
        elide: Text.ElideRight
        maximumLineCount: 2
        wrapMode: Text.Wrap
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Qt.AlignRight
    }

    indicator: Rectangle {
        implicitWidth: 28
        implicitHeight: 28
        // x: control.width - width - control.rightPadding
        // x: width / 2 + control.leftPadding / 2
        x: control.leftPadding
        // y: parent.height / 2 - height / 2
        y: control.topPadding + (control.availableHeight - height) / 2
        radius: width / 2
        // color: Qt.lighter(control.itemColor, 1.5)
        // color: "#00FF00"
        // border.color: "#00FF00"// control.itemColor

        color: control.down ? control.palette.light : control.palette.base
        border.width: control.visualFocus ? 2 : 1
        border.color: control.visualFocus ? control.palette.highlight : control.palette.mid

        Rectangle {
            x: (parent.width - width) / 2
            y: (parent.height - height) / 2
            width: 20
            height: 20
            radius: width / 2
            color: control.palette.text
            visible: control.checked
        }
    }
}
