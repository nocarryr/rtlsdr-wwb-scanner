import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import GraphUtils 1.0

Item {
    id: root
    property var activeSpectrum
    property int activeIndex: -1
    property var spectrumGraphs: ({})
    property var allSeries: ({})
    property var itemMap: ({})

    signal addItem(var spectrum)
    signal selected(var spectrum, bool state)

    onActiveSpectrumChanged: {
        if (root.activeSpectrum){
            root.activeIndex = root.activeSpectrum.index;
        }
    }

    onAddItem: {
        // var index = root.spectrumGraphs.length;
        var index = spectrum.index;
        root.spectrumGraphs[index] = spectrum;
        root.allSeries[index] = spectrum.series;
        var data = {
            'index':index,
            'name':spectrum.name,
            'color':spectrum.color,
        };
        // if (!data.name){
        //     data.name = 'foo';
        // }
        // console.log('onAddItem: ' + JSON.stringify(data));
        listModel.append(data);
        spectrum.onNameChanged.connect(function(){
            // console.log('spectrum.onNameChanged: ', spectrum.name);
            listModel.get(index).name = spectrum.name;
        });
        spectrum.onColorChanged.connect(function(){
            // console.log('spectrum.onColorChanged: ', spectrum.color);
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

        ButtonGroup {
            id: btnGroup

            // onCheckedButtonChanged: {
            //
            // }
            onClicked: {
                var spectrum = root.spectrumGraphs[button.itemIndex];
                // console.log('btnGroup.onClicked: ', button.itemIndex);
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
        }
    }
}
