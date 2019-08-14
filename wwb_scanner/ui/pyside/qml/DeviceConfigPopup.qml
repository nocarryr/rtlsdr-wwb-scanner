import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import Qt.labs.settings 1.0
import DeviceConfig 1.0

Dialog {
    id: root
    property var device
    property real deviceIndex
    property string deviceSerial
    property real sampleRate: 2048
    property real gain

    onDeviceChanged:{
        var device = device_list.device;
        gainSelect.updateChoices();
        if (device) {
            root.deviceIndex = device.device_index;
            root.deviceSerial = device.device_serial;
        }
    }

    Settings {
        category: 'Device Config'
        property alias deviceIndex: root.deviceIndex
        property alias deviceSerial: root.deviceSerial
        property alias sampleRate: root.sampleRate
        property alias gain: root.gain
    }

    DeviceInfoList {
        id: device_list
        onDevicesChanged: {
            console.log('onDevicesChanged');
            updateDeviceList();
        }
    }
    function updateDeviceList(){
        var devices = device_list.devices,
            // indices = Object.keys(devices),
            device,
            data;
        // indices.sort();
        console.log('updateDeviceList');
        // console.log(indices.length);
        device_model.clear();
        for (var i=0;i<devices.length;i++){
            device = devices[i];
            data = {
                'index':i,
                'device_index':device.device_index,
                'device_serial':device.device_serial,
                'text':device.text,
            };
            // if (i == 0 || i >= device_model.count){
            //     device_model.append(data);
            // } else {
            //     device_model.set(i, data);
            // }
            device_model.append(data);
            console.log('model item: ' + JSON.stringify(device_model.get(i)));
            // device_model.sync();
        }
        if (root.device){
            device_select.currentIndex = root.device.device_index;
        }
    }
    ColumnLayout {
        anchors.fill: parent
        GroupBox {
            title: 'Device Select'
            ComboBox {
                id: device_select
                editable: false
                textRole: 'text'
                anchors.fill: parent

                model: ListModel{
                    id: device_model
                }
                onActivated: {
                    var idx = device_select.currentIndex,
                        item;
                    if (idx == -1){
                        // root.deviceIndex = -1
                        return;
                    } else {
                        item = device_model.get(idx);
                        root.device = device_list.devices[item.device_index];
                    }
                }
            }
        }
        GroupBox {
            title: "Sample Rate (Msps)"
            TextField {
                id: sampleRateField

                inputMethodHints: Qt.ImhDigitsOnly
                maximumLength: 4
                text: root.sampleRate.toString()
                onEditingFinished: {
                    root.sampleRate = parseInt(sampleRateField.text);
                }
            }
        }

        GroupBox {
            title: "Gain"
            SpinBox {
                id: gainSelect
                signal updateChoices()
                property var items: [0]
                from: 0
                to: items.length-1

                onUpdateChoices:{
                    if (root.device){
                        gainSelect.items = root.device.gains;
                        // gainSelect.to = root.device.gains.length;
                        for (var i=0;i<gainSelect.items.length;i++){
                            if (gainSelect.items[i] == root.gain){
                                gainSelect.value = i;
                            }
                        }
                    }
                }

                textFromValue: function(value) {
                    return items[value].toString();
                }
                valueFromText: function(text) {
                    var items = gainSelect.items;
                    for (var i=0;i<items.length;i++){
                        if (items[i].toString() == text){
                            return i;
                        }
                    }
                    return gainSelect.value;
                }
                onValueModified: {
                    root.gain = gainSelect.items[gainSelect.value];
                }
            }
        }
    }
    standardButtons: Dialog.Ok | Dialog.Cancel

    onAccepted:{
        root.close();
    }
    onRejected:{
        root.close();
    }

    onOpened:{
        device_list.update_devices();
    }

    // Component.onCompleted: {
    //     device_list.update_devices();
    // }
}
