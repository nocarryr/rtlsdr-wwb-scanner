import QtQuick 2.0
import QtQuick.Dialogs 1.0
import Qt.labs.settings 1.0

FileDialog {
    id: root
    title: "Please choose a file"
    folder: shortcuts.home
    selectMultiple: false
    selectExisting: false
    defaultSuffix: 'csv'
    nameFilters: [
        'Scan Files (*.csv)',
        'Numpy Files (*.npz)',
    ]
    property var graphData

    Item {
        Settings {
            category: 'Folder Preferences'
            property alias exportFolder: root.folder
        }
    }

    onAccepted: {
        root.graphData.save_to_file(root.fileUrl);
        root.close();
    }

    onRejected: {
        root.close();
    }

}
