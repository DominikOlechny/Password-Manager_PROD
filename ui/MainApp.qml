import QtQuick
import QtQuick.Controls

ApplicationWindow {
    id: window
    visible: true
    width: 1000
    height: 720
    minimumWidth: width
    maximumWidth: width
    minimumHeight: height
    maximumHeight: height
    title: qsTr("Menager Haseł")

    Loader {
        id: viewLoader
        anchors.fill: parent
        source: backend.currentView
        onLoaded: {
            if (item && item.hasOwnProperty('statusMessageChanged')) {
                backend.statusMessageChanged.connect(item.statusMessageChanged)
            }
        }
    }
}
