import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    width: 480
    height: 720
    color: "white"

    property alias driverInput: driverField.text
    property alias serverInput: serverField.text
    property alias databaseInput: databaseField.text
    property alias usernameInput: usernameField.text
    property alias passwordInput: passwordField.text

    signal backRequested
    signal testConnectionRequested(string driver, string server, string database, string username, string password)
    signal saveConfigRequested(string driver, string server, string database, string username, string password)

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
        text: qsTr("KONFIGURACJA BAZY")
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
            width: 300
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1

            TextInput {
                id: driverField
                anchors.fill: parent
                anchors.margins: 6
                text: backend.dbDriver || qsTr("DRIVER (np. ODBC Driver 17 for SQL Server)")
                font.pixelSize: 12
                clip: true
            }
        }

        Rectangle {
            width: 300
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1

            TextInput {
                id: serverField
                anchors.fill: parent
                anchors.margins: 6
                text: backend.dbServer || qsTr("ADRES SERWERA (np. 127.0.0.1,1433)")
                font.pixelSize: 12
                clip: true
            }
        }

        Rectangle {
            width: 300
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1

            TextInput {
                id: databaseField
                anchors.fill: parent
                anchors.margins: 6
                text: backend.dbDatabase || qsTr("NAZWA BAZY DANYCH")
                font.pixelSize: 12
                clip: true
            }
        }

        Rectangle {
            width: 300
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1

            TextInput {
                id: usernameField
                anchors.fill: parent
                anchors.margins: 6
                text: backend.dbUsername || qsTr("UŻYTKOWNIK")
                font.pixelSize: 12
                clip: true
            }
        }

        Rectangle {
            width: 300
            height: 32
            color: "transparent"
            border.color: "black"
            border.width: 1

            TextInput {
                id: passwordField
                anchors.fill: parent
                anchors.margins: 6
                text: backend.dbPassword
                echoMode: TextInput.Password
                font.pixelSize: 12
                clip: true
            }
        }

        Row {
            spacing: 12
            anchors.horizontalCenter: parent.horizontalCenter

            Button {
                id: testConnectionButton
                width: 140
                height: 40
                text: qsTr("TEST POŁĄCZENIA")
                onClicked: backend.testDatabaseConnection(driverField.text, serverField.text, databaseField.text, usernameField.text, passwordField.text)
            }

            Button {
                id: saveConfigButton
                width: 120
                height: 40
                text: qsTr("ZAPISZ")
                onClicked: backend.saveDatabaseConfig(driverField.text, serverField.text, databaseField.text, usernameField.text, passwordField.text)
            }
        }
    }

    Text {
        id: statusText
        anchors.horizontalCenter: parent.horizontalCenter
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
            driverField.text = backend.dbDriver || driverField.text
            serverField.text = backend.dbServer || serverField.text
            databaseField.text = backend.dbDatabase || databaseField.text
            usernameField.text = backend.dbUsername || usernameField.text
            passwordField.text = backend.dbPassword || passwordField.text
        }
    }
}
