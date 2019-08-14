import QtQuick 2.0
import QtQuick.Dialogs 1.0
import Qt.labs.settings 1.0

FileDialog {
    id: root
    title: "Please choose a file"
    folder: shortcuts.home
    selectMultiple: false
    nameFilters: [
        'Scan Files (*.csv *.sbd2)'
    ]
    signal importFile(var fileName)

    Item {
        Settings {
            category: 'Folder Preferences'
            property alias importFolder: root.folder
        }
    }

    onAccepted: {
        root.importFile(root.fileUrl);
        root.close();
    }

    onRejected: {
        root.close();
    }

}
