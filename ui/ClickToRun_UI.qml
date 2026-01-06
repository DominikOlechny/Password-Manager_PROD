import QtQuick
import QtQuick.Controls

Rectangle {
    anchors.fill: parent
    color: "white"

    Column {
        anchors.centerIn: parent
        spacing: 24

        Text {
            id: titleText
            text: qsTr("MENAGER HASEŁ")
            font.pixelSize: 24
            font.bold: true
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Rectangle {
            id: topLine
            width: 230
            height: 2
            color: "#000000"
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Button {
            id: button_cliktorunaplication
            width: 230
            height: 32
            text: qsTr("URUCHOM")
            anchors.horizontalCenter: parent.horizontalCenter

            background: Rectangle {
                color: "#d3d3d3"
                radius: 4
            }

            onClicked: backend.startApplication()
        }
    }
}
