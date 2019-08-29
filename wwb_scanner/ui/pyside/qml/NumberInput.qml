import QtQuick 2.13
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12

Frame {
    id: root
    property bool isFloat: true
    property bool showFrame: false
    property real floatPrecision: 3
    property alias name: lbl.text
    property alias labelFontSize: lbl.font.pointSize
    property alias inputFontSize: txtField.font.pointSize
    property real value: 0
    property string textValue: isFloat ? value.toFixed(root.floatPrecision): parseInt(value).toString()
    signal submit(real value)

    leftPadding: 12
    rightPadding: 12
    topPadding: 6
    bottomPadding: 6

    ColumnLayout {
        anchors.fill: parent
        spacing: 1
        Label {
            id: lbl
            Layout.alignment: Qt.AlignLeft || Qt.AlignBottom
            horizontalAlignment: Text.AlignLeft
            verticalAlignment: Text.AlignBottom
        }

        TextField {
            id: txtField
            Layout.alignment: Qt.AlignLeft || Qt.AlignTop
            Layout.fillWidth: true
            inputMethodHints: Qt.ImhDigitsOnly
            maximumLength: 7
            implicitWidth: txtMetrics.maxWidth + txtField.leftPadding + txtField.rightPadding
            implicitHeight: txtMetrics.height + txtField.topPadding + txtField.bottomPadding
            text: root.textValue
            horizontalAlignment: Text.AlignLeft
            onEditingFinished: {
                if (root.isFloat){
                    root.value = parseFloat(txtField.text);
                } else {
                    root.value = parseInt(txtField.text);
                }
                root.submit(root.value);
            }
        }
    }

    background: Rectangle {
        color: 'transparent'
        border.color: root.palette.mid
        border.width: root.showFrame ? 1 : 0
        radius: 3
    }

    FontMetrics {
        id: txtMetrics
        font: txtField.font
        property real maxWidth: txtMetrics.averageCharacterWidth * txtField.maximumLength
    }
    FontMetrics {
        id: lblMetrics
        font: lbl.font
    }
}
