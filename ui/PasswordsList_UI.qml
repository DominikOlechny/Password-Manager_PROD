import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    width: 1000
    height: 650
    color: "white"
    property alias text1: text1

    Text {
        id: statusText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 8
        text: backend.statusMessage
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        width: parent.width - 40
        color: "#333333"
    }

    Button {
        id: logoutButton
        x: 8
        text: qsTr("WYLOGUJ")
        width: 130
        height: 40
        anchors.top: parent.top
        anchors.right: parent.right
        anchors.topMargin: 8
        anchors.rightMargin: 862
    }

    Text {
        id: titleText
        text: qsTr("MENAGER HASEŁ")
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: statusText.bottom
        anchors.topMargin: 24
        font.pixelSize: 24
        font.bold: true
    }

    Rectangle {
        id: topLine
        width: 300
        height: 2
        color: "black"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: titleText.bottom
        anchors.topMargin: 16
    }

    Row {
        id: headersRow
        spacing: 32
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: topLine.bottom
        anchors.topMargin: 32

        Text {
            width: 170
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("SERWIS")
            font.pixelSize: 20
            font.bold: true
        }

        Text {
            width: 170
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("LOGIN")
            font.pixelSize: 20
            font.bold: true
        }

        Text {
            id: text1
            width: 260
            horizontalAlignment: Text.AlignHCenter
            text: qsTr("HASŁO")
            font.pixelSize: 20
            font.bold: true
        }
    }

    Column {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: headersRow.bottom
        anchors.topMargin: 24

        ListView {
            id: passwordList
            width: 760
            height: 355
            spacing: 12
            model: passwordModel
            clip: true
            delegate: Rectangle {
                width: passwordList.width
                height: 32
                color: "transparent"

                Row {
                    anchors.fill: parent
                    spacing: 12

                    Button {
                        width: 32
                        height: 32
                        text: "X"
                        onClicked: backend.deletePassword(entryId)
                    }

                    Rectangle {
                        width: 170
                        height: 32
                        color: "transparent"
                        border.color: expired ? "red" : "black"
                        border.width: 1
                        TextInput {
                            anchors.fill: parent
                            anchors.margins: 6
                            text: service
                            font.pixelSize: 12
                            color: expired ? "red" : "black"
                            readOnly: true
                            clip: true
                        }
                    }

                    Rectangle {
                        width: 170
                        height: 32
                        color: "transparent"
                        border.color: expired ? "red" : "black"
                        border.width: 1
                        TextInput {
                            anchors.fill: parent
                            anchors.margins: 6
                            text: login
                            font.pixelSize: 12
                            color: expired ? "red" : "black"
                            readOnly: true
                            clip: true
                        }
                    }

                    Rectangle {
                        width: 260
                        height: 32
                        color: "transparent"
                        border.color: expired ? "red" : "black"
                        border.width: 1

                        Row {
                            id: passwordRow
                            anchors.fill: parent
                            anchors.margins: 4
                            spacing: 4

                            TextInput {
                                width: Math.max(0, passwordRow.width - revealButton.width - copyButton.width - passwordRow.spacing * 2)
                                text: passwordText
                                echoMode: revealed ? TextInput.Normal : TextInput.Password
                                font.pixelSize: 12
                                color: expired ? "red" : "black"
                                anchors.verticalCenter: parent.verticalCenter
                                readOnly: true
                                clip: true
                            }

                            Button {
                                id: revealButton
                                width: 40
                                height: 24
                                text: revealed ? qsTr("👁️") : qsTr("👁️")
                                onClicked: backend.revealPassword(entryId)
                            }
                            Button {
                                id: copyButton
                                width: 60
                                height: 24
                                text: qsTr("📋")
                                onClicked: backend.copyPassword(entryId)
                            }
                        }
                    }

                    Button {
                        width: 80
                        height: 32
                        text: qsTr("EDYTUJ")
                        onClicked: backend.startEditPassword(entryId)
                    }
                }
            }
        }
    }

    Button {
        id: addButton
        y: 534
        text: qsTr("DODAJ")
        width: 140
        height: 40
        anchors.left: parent.left
        anchors.bottom: parent.bottom
        anchors.leftMargin: 690
        anchors.bottomMargin: 76
        onClicked: backend.startAddPassword()
    }

    Button {
        id: logoutButton1
        x: 862
        width: 130
        height: 40
        text: backend.currentLogin ? qsTr("KONTO: ") + backend.currentLogin : qsTr("KONTO")
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.rightMargin: 8
        anchors.topMargin: 8
        onClicked: backend.startEditUserAccount()
    }

    Connections {
        target: logoutButton
        function onClicked() {
            backend.logout()
        }
    }
}

