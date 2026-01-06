import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    width: 480
    height: 720
    color: "white"

    property alias keyFilePath: key.text

    signal backRequested
    signal loadKeyRequested(string path)
    signal saveKeyRequested(string path, string content)
    signal generateKeyRequested

    Button {
        id: backButton
        text: qsTr("WSTECZ")
        width: 120
        height: 40
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.topMargin: 8
        anchors.leftMargin: 8
        onClicked: backend.backToLogin()
    }

    Text {
        id: titleText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 40
        text: qsTr("MENAGER HASEŁ")
        font.pixelSize: 24
        font.bold: true
    }

    Rectangle {
        id: topLine
        width: 230
        height: 2
        color: "black"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: titleText.bottom
        anchors.topMargin: 16
    }

    Text {
        id: headerText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: topLine.bottom
        anchors.topMargin: 32
        text: qsTr("Dane Klucza")
        font.pixelSize: 20
        font.bold: true
    }

    Column {
        id: formColumn
        spacing: 18
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: headerText.bottom
        anchors.topMargin: 32

        Rectangle {
            width: 320
            height: 34
            color: "transparent"
            border.color: "black"
            border.width: 1

            TextInput {
                id: key
                anchors.fill: parent
                anchors.margins: 6
                text: qsTr("Klucz")
                font.pixelSize: 12
                clip: true
            }
        }

        Row {
            spacing: 12
            anchors.horizontalCenter: parent.horizontalCenter

            Button {
                id: saveKeyButton
                width: 100
                height: 40
                text: qsTr("ZAPISZ")
                onClicked: backend.saveKey(key.text)
            }

            Button {
                id: generateKeyButton
                width: 150
                height: 40
                text: qsTr("GENERUJ NOWY")
                onClicked: backend.generateKey()
            }
        }
    }

    Text {
        id: statusText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: formColumn.bottom
        anchors.topMargin: 8
        width: parent.width - 40
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        text: ""
        color: "#333333"
    }

    Connections {
        target: backend
        function onStatusMessageChanged(message) {
            statusText.text = message
        }
        function onEditContextChanged() {
            key.text = backend.currentKey
        }
    }
}
