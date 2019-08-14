import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import Qt.labs.settings 1.0

ColumnLayout {
    id: root

    property bool isFloat: true
    property real floatPrecision: 3
    property alias name: lbl.text
    property real value: 0
    property string textValue: isFloat ? value.toFixed(root.floatPrecision): parseInt(value).toString()
    signal submit(real value)

    Layout.preferredWidth: txtField.width

    // onValueChanged: {
    //     if (root.isFloat){
    //         // root.textValue = Number.parseFloat(root.value.toFixed(root.floatPrecision));
    //         root.textValue = root.value.toFixed(root.floatPrecision);
    //     } else {
    //         // root.textValue = parseInt(root.value);
    //         // root.textValue = Number.parseInt(root.value).toString();
    //         root.textValue = parseInt(root.value).toString();
    //     }
    // }

    Label {
        id: lbl
    }

    TextField {
        id: txtField
        inputMethodHints: Qt.ImhDigitsOnly
        maximumLength: 7
        text: root.textValue
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
