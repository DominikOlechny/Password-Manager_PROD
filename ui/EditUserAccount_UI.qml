import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    width: 480
    height: 720
    color: "white"

    property alias oldPasswordInput: oldPasswordField.text
    property alias newPasswordInput: newPasswordField.text
    property alias confirmPasswordInput: confirmPasswordField.text
    property alias mfaInput: mfaField.text
    property alias newLoginInput: newLoginField.text

    signal backRequested()
    signal saveRequested(string oldPassword, string newPassword, string confirmPassword, string mfaCode, string newLogin)
    signal resetRequested()

    Button {
        id: backButton
        text: qsTr("WSTECZ")
        width: 120
        height: 40
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.topMargin: 8
        anchors.leftMargin: 8
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
        text: qsTr("EDYTUJ DANE UŻYTKOWNIKA")
        font.pixelSize: 20
        font.bold: true
    }

    Row {
        id: contentRow
        spacing: 16
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: headerText.bottom
        anchors.topMargin: 32

        Column {
            id: formColumn
            spacing: 16
            width: 230

            Rectangle {
                id: newLoginRect
                width: 230
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1
                TextField {
                    id: newLoginField
                    anchors.fill: parent
                    anchors.margins: 6
                    text: ""
                    placeholderText: qsTr("NOWY LOGIN (OPCJONALNIE)")
                    font.pixelSize: 12
                    background: null
                    clip: true
                }
            }

            Rectangle {
                id: oldPasswordRect
                width: 230
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1
                TextField {
                    id: oldPasswordField
                    anchors.fill: parent
                    anchors.margins: 6
                    text: ""
                    placeholderText: qsTr("STARE HASŁO")
                    font.pixelSize: 12
                    echoMode: TextInput.Password
                    background: null
                    clip: true
                }
            }

            Rectangle {
                id: newPasswordRect
                width: 230
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1
                TextField {
                    id: newPasswordField
                    anchors.fill: parent
                    anchors.margins: 6
                    text: ""
                    placeholderText: qsTr("NOWE HASŁO")
                    font.pixelSize: 12
                    echoMode: TextInput.Password
                    background: null
                    clip: true
                }
            }

            Rectangle {
                id: confirmPasswordRect
                width: 230
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1
                TextField {
                    id: confirmPasswordField
                    anchors.fill: parent
                    anchors.margins: 6
                    text: ""
                    placeholderText: qsTr("POWTÓRZ NOWE HASŁO")
                    font.pixelSize: 12
                    echoMode: TextInput.Password
                    background: null
                    clip: true
                }
            }

            Row {
                id: mfaRow
                spacing: 8
                anchors.horizontalCenter: parent.horizontalCenter

                Rectangle {
                    id: mfaRect
                    width: 230
                    height: 32
                    color: "transparent"
                    border.color: "black"
                    border.width: 1
                    TextField {
                        id: mfaField
                        anchors.fill: parent
                        anchors.margins: 6
                        text: ""
                        placeholderText: qsTr("KOD MFA (OPCJONALNIE)")
                        font.pixelSize: 12
                        background: null
                        clip: true
                    }
                }

                Button {
                    id: generateMfaButton
                    width: 90
                    height: mfaRect.height
                    text: qsTr("GENERUJ")
                    onClicked: backend.generateMfaSetup()
                }
            }
        }

        Item {
            width: 25
            height: 1
        }

        Column {
            id: mfaPreview
            spacing: 6
            width: 170
            visible: backend.mfaProvisioningUri !== ""

            Text {
                text: qsTr("Zeskanuj kod QR lub przepisz sekret.")
                font.pixelSize: 10
                horizontalAlignment: Text.AlignHCenter
                width: 170
                wrapMode: Text.WordWrap
            }

            Image {
                id: mfaQr
                width: 140
                height: 140
                anchors.horizontalCenter: parent.horizontalCenter
                fillMode: Image.PreserveAspectFit
                smooth: true
                source: backend.mfaProvisioningUri !== "" ?
                            "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=" + encodeURIComponent(backend.mfaProvisioningUri) : ""
            }

            Text {
                text: backend.mfaSecret !== "" ? qsTr("Sekret: ") + backend.mfaSecret : ""
                font.pixelSize: 10
                width: 170
                wrapMode: Text.WrapAnywhere
            }

            Text {
                text: backend.mfaProvisioningUri
                font.pixelSize: 8
                width: 170
                wrapMode: Text.WrapAnywhere
            }
        }
    }

    Row {
        id: actionRow
        spacing: 24
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: contentRow.bottom
        anchors.topMargin: 24

        Button {
            id: resetButton
            width: 120
            height: 50
            text: qsTr("RESET")
        }

        Button {
            id: saveButton
            width: 150
            height: 50
            text: qsTr("ZAPISZ ZMIANY")
        }
    }

    Text {
        id: statusText
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: actionRow.bottom
        anchors.topMargin: 16
        width: parent.width - 40
        wrapMode: Text.WordWrap
        horizontalAlignment: Text.AlignHCenter
        color: "#333333"
        text: ""
    }

    Connections {
        target: backButton
        function onClicked() {
            backRequested()
            backend.clearMfaSetup()
            backend.backToPasswords()
        }
    }

    Connections {
        target: resetButton
        function onClicked() {
            oldPasswordField.text = ""
            newPasswordField.text = ""
            confirmPasswordField.text = ""
            mfaField.text = ""
            newLoginField.text = ""
            statusText.text = ""
            backend.clearMfaSetup()
            resetRequested()
        }
    }

    Connections {
        target: saveButton
        function onClicked() {
            saveRequested(oldPasswordField.text, newPasswordField.text, confirmPasswordField.text, mfaField.text, newLoginField.text)
            backend.saveUserAccount(oldPasswordField.text, newPasswordField.text, confirmPasswordField.text, mfaField.text, newLoginField.text)
        }
    }

    Connections {
        target: backend
        function onStatusMessageChanged(message) {
            statusText.text = message
        }

    }

}
