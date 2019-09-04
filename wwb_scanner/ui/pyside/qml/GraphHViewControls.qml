import QtQuick 2.0
import QtQuick.Controls 2.12
import QtQuick.Layouts 1.11

RowLayout {
    id: root
    property GraphViewController controller

    RoundButton {
        Layout.leftMargin: 6
        text: "\u2190"
        onClicked: { controller.scrollLeft() }
    }
    XScrollBar {
        Layout.fillWidth: true
        Layout.fillHeight: true
        dataExtents: controller.dataExtents
        viewScale: controller.viewScale
    }
    RoundButton {
        text: "\u2192"
        onClicked: { controller.scrollRight() }
    }
    Item {
        Layout.preferredWidth: 20
    }
    RoundButton {
        text: '+'
        onClicked: { controller.viewScale.zoomX(1-controller.defaultZoomIncr) }
    }
    RoundButton {
        text: '-'
        onClicked: { controller.viewScale.zoomX(controller.defaultZoomIncr+1) }
    }
    Button {
        Layout.rightMargin: 6
        text: 'Reset'
        onClicked: { controller.reset() }
    }
}
