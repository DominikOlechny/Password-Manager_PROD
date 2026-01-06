import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    width: 480
    height: 720
    color: "white"

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

    Text {
        id: titleText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: statusText.bottom
        anchors.topMargin: 24
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
        id: loginHeader
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: topLine.bottom
        anchors.topMargin: 32
        text: qsTr("ZALOGUJ")
        font.pixelSize: 20
        font.bold: true
    }

    Column {
        id: loginColumn
        spacing: 16
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: loginHeader.bottom
        anchors.topMargin: 24

        Rectangle {
            width: 230
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1
            TextField {
                id: loginLoginField
                anchors.fill: parent
                anchors.margins: 6
                placeholderText: qsTr("LOGIN")
                font.pixelSize: 12
                background: null
                clip: true
            }
        }

        Rectangle {
            width: 230
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1
            TextField {
                id: loginPasswordField
                anchors.fill: parent
                anchors.margins: 6
                placeholderText: qsTr("HASŁO")
                font.pixelSize: 12
                echoMode: TextInput.Password
                background: null
                clip: true
            }
        }

        Rectangle {
            width: 230
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1
            TextField {
                id: loginMfaField
                anchors.fill: parent
                anchors.margins: 6
                placeholderText: qsTr("KOD AUTHENTICATOR")
                font.pixelSize: 12
                background: null
                clip: true
            }
        }
    }

    Row {
        id: loginButtonsRow
        spacing: 24
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: loginColumn.bottom
        anchors.topMargin: 24

        Button {
            id: forgotPasswordButton
            width: 150
            height: 50
            text: qsTr("NIE PAMIĘTAM\nHASŁA")
            onClicked: backend.showMessage("[!] Reset hasła nie jest jeszcze zaimplementowany.")
        }

        Button {
            id: loginOkButton
            width: 120
            height: 50
            text: qsTr("OK")
            onClicked: backend.loginUser(loginLoginField.text, loginPasswordField.text, loginMfaField.text)
        }
    }

    Rectangle {
        id: middleLine
        width: 230
        height: 2
        color: "black"
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: loginButtonsRow.bottom
        anchors.topMargin: 48
    }

    Text {
        id: registerHeader
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: middleLine.bottom
        anchors.topMargin: 24
        text: qsTr("ZAREJESTRUJ SIĘ")
        font.pixelSize: 20
        font.bold: true
    }

    Column {
        id: registerColumn
        spacing: 16
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: registerHeader.bottom
        anchors.topMargin: 24

        Rectangle {
            width: 230
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1
            TextField {
                id: registerLoginField
                anchors.fill: parent
                anchors.margins: 6
                placeholderText: qsTr("LOGIN")
                font.pixelSize: 12
                background: null
                clip: true
            }
        }

        Rectangle {
            width: 230
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1
            TextField {
                id: registerPasswordField
                anchors.fill: parent
                anchors.margins: 6
                placeholderText: qsTr("HASŁO")
                font.pixelSize: 12
                echoMode: TextInput.Password
                background: null
                clip: true
            }
        }

        Rectangle {
            width: 230
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1
            TextField {
                id: registerConfirmPasswordField
                anchors.fill: parent
                anchors.margins: 6
                placeholderText: qsTr("POTWIERDŹ HASŁO")
                font.pixelSize: 12
                echoMode: TextInput.Password
                background: null
                clip: true
            }
        }
    }

    Row {
        id: registerButtonsRow
        y: 637
        spacing: 24
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: registerColumn.bottom
        anchors.topMargin: 24
        anchors.horizontalCenterOffset: 1

        Button {
            id: registerResetButton
            width: 120
            height: 50
            text: qsTr("RESET")
            onClicked: {
                registerLoginField.text = ""
                registerPasswordField.text = ""
                registerConfirmPasswordField.text = ""
            }
        }

        Button {
            id: registerOkButton
            width: 120
            height: 50
            text: qsTr("OK")
            onClicked: backend.registerUser(registerLoginField.text, registerPasswordField.text, registerConfirmPasswordField.text)
        }
    }

    Button {
        id: basesettingsbutton
        x: 900
        y: 8
        width: 93
        height: 39
        text: qsTr("Baza")
        onClicked: backend.openDatabaseSettings()
    }

    Button {
        id: keysettingsbutton
        x: 8
        y: 8
        width: 93
        height: 39
        text: qsTr("Klucz")
        onClicked: backend.openKeySettings()
    }
}
