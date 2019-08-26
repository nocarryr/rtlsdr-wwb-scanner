import QtQuick 2.12
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import GraphUtils 1.0

RadioDelegate {
    id: control
    property string itemName
    property color itemColor: "#8080FF"
    property int itemIndex
    leftPadding: 4
    rightPadding: 4
    font.pointSize: 9

    signal colorButtonPressed(int itemIndex)

    contentItem: Label {
        rightPadding: colorBtn.width + control.spacing
        leftPadding: control.indicator.width + control.spacing
        text: control.itemName
        font: control.font
        color: control.itemColor
        elide: Text.ElideRight
        maximumLineCount: 2
        wrapMode: Text.Wrap
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Qt.AlignRight
    }

    RoundButton {
        id: colorBtn
        property color highlightColor: Qt.lighter(control.itemColor, 1.25)

        x: control.width - width - control.rightPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        radius: 2

        onClicked: {
            control.colorButtonPressed(control.itemIndex);
        }

        background: Rectangle {
            implicitWidth: 20
            implicitHeight: 20
            radius: colorBtn.radius
            color: colorBtn.hovered ? colorBtn.highlightColor : control.itemColor
            border.color: Qt.darker(control.itemColor, 1.5)
            border.width: 1
        }
    }

    indicator: Rectangle {
        implicitWidth: 26
        implicitHeight: 26
        x: control.leftPadding
        y: control.topPadding + (control.availableHeight - height) / 2
        radius: width / 2
        color: control.down ? control.palette.light : control.palette.base
        border.width: 1
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

    background: Rectangle {
        implicitWidth: 100
        implicitHeight: 40
        opacity: control.down ? 1 : .3
        color: control.hovered ? control.palette.midlight : control.palette.light
        border.width: 1
        border.color: control.visualFocus ? control.palette.highlight : control.palette.mid
    }
}
