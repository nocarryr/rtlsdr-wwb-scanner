import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import QtQuick.Dialogs 1.0
import GraphUtils 1.0

Item {
    id: root
    property var activeSpectrum
    property int activeIndex: -1
    property var spectrumGraphs: ({})

    signal addItem(var spectrum)
    signal selected(var spectrum, bool state)

    onActiveSpectrumChanged: {
        if (root.activeSpectrum){
            root.activeIndex = root.activeSpectrum.index;
        }
    }

    onAddItem: {
        var index = spectrum.index;
        root.spectrumGraphs[index] = spectrum;
        var data = {
            'index':index,
            'name':spectrum.name,
            'color':spectrum.color,
        };
        listModel.append(data);
        spectrum.onNameChanged.connect(function(){
            listModel.get(index).name = spectrum.name;
        });
        spectrum.onColorChanged.connect(function(){
            listModel.get(index).color = spectrum.color;
        });
    }

    ListModel {
        id: listModel
        dynamicRoles: true
    }

    ListView {
        id: listView
        anchors.fill: parent
        model: listModel

        spacing: 2
        contentWidth: listView.width

        ButtonGroup {
            id: btnGroup

            onClicked: {
                var spectrum = root.spectrumGraphs[button.itemIndex];
                if (spectrum.index == root.activeIndex){
                    return;
                }
                root.selected(spectrum, true);
            }
        }

        delegate: ChartSelectDelegate {
            ButtonGroup.group: btnGroup
            text: name
            itemIndex: index
            itemName: name
            itemColor: color
            checked: root.activeIndex == index
            graphVisible: root.spectrumGraphs[itemIndex].graphVisible
            width: listView.contentWidth
            onColorButtonPressed: {
                var spectrum = root.spectrumGraphs[itemIndex];
                colorDialog.activate(spectrum);
            }
            onVisibleCheckBoxPressed: {
                root.spectrumGraphs[itemIndex].graphVisible = state;
            }
        }
    }

    Loader {
        id: colorDialog
        sourceComponent: Component { ColorDialog {} }
        property var spectrum
        property color color
        active: false

        function activate(spectrum){
            colorDialog.spectrum = spectrum;
            colorDialog.color = spectrum.color;
            colorDialog.active = true;
        }

        function close(){
            var dlg = colorDialog.item;
            if (dlg){
                dlg.close();
            }
            colorDialog.spectrum = null;
            colorDialog.active = false;
        }

        onItemChanged: {
            var dlg = item;
            if (dlg){
                dlg.color = colorDialog.color;
                dlg.open();
            }
        }

        Connections {
            target: colorDialog.item
            onAccepted: {
                var dlg = colorDialog.item;
                colorDialog.spectrum.color = dlg.color;
                dlg.close();
                colorDialog.close();
            }
            onRejected: {
                var dlg = colorDialog.item;
                dlg.close();
                colorDialog.close();
            }
        }
    }
}
