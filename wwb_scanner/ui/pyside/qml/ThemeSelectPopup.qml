import QtQuick 2.0
import QtQuick.Layouts 1.11
import QtQuick.Controls 2.12
import Qt.labs.settings 1.0
import QtCharts 2.13


Dialog {
    id: root
    property alias theme: settings.chartTheme

    Settings {
        id: settings
        category: 'User Interface'
        property int chartTheme: ChartView.ChartThemeDark
    }

    ComboBox {
        id: combo
        textRole: 'text'
        model: ListModel {
            ListElement { text:'Light'; value:ChartView.ChartThemeLight }
            ListElement { text:'Cerulean Blue'; value:ChartView.ChartThemeBlueCerulean }
            ListElement { text:'Dark'; value:ChartView.ChartThemeDark }
            ListElement { text:'Brown Sand'; value:ChartView.ChartThemeBrownSand }
            ListElement { text:'Natural (NCS) Blue'; value:ChartView.ChartThemeBlueNcs }
            ListElement { text:'High Contrast'; value:ChartView.ChartThemeHighContrast }
            ListElement { text:'Icy Blue'; value:ChartView.ChartThemeBlueIcy }
            ListElement { text:'Qt'; value:ChartView.ChartThemeQt }
        }

        function getSelectedValue(){
            var idx = combo.currentIndex,
                item;
            if (idx == -1){
                return root.theme;
            }
            item = model.get(idx);
            return item.value;
        }
        function setSelectedValue(value){
            var item;
            for (var i=0;i<model.count;i++){
                item = model.get(i);
                if (item.value == value){
                    combo.currentIndex = i;
                }
            }
        }
    }


    standardButtons: Dialog.Ok | Dialog.Cancel

    onAccepted:{
        root.theme = combo.getSelectedValue();
        root.close();
    }
    onRejected:{
        combo.setSelectedValue(root.theme);
        root.close();
    }

    Component.onCompleted: {
        combo.setSelectedValue(root.theme);
    }
}
