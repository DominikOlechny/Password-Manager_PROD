
/* .ui.qml - ekran edycji hasła */
import QtQuick
import QtQuick.Controls

Rectangle {
    id: root
    width: 480
    height: 720
    color: "white"

    Button {
        id: backButton
        text: qsTr("WSTECZ")
        width: 120
        height: 40
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.topMargin: 8
        anchors.leftMargin: 8
        onClicked: backend.backToPasswords()
    }

    Text {
        id: titleText
        text: qsTr("MENAGER HASEŁ")
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: parent.top
        anchors.topMargin: 40
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
        text: qsTr("HASŁO")
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: topLine.bottom
        anchors.topMargin: 32
        font.pixelSize: 20
        font.bold: true
    }

    Column {
        id: formColumn
        spacing: 20
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.top: headerText.bottom
        anchors.topMargin: 40
        width: implicitWidth

        Column {
            spacing: 6
            anchors.horizontalCenter: parent.horizontalCenter

            Text {
                text: qsTr("SERWIS:")
                font.pixelSize: 12
            }

            Rectangle {
                width: 260
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1
                TextField {
                    id: serviceField
                    anchors.fill: parent
                    anchors.margins: 6
                    text: backend.editService
                    placeholderText: qsTr("np. gmail.com")
                    background: null
                    inputMethodHints: Qt.ImhNoAutoUppercase | Qt.ImhPreferLowercase
                    font.pixelSize: 12
                    selectByMouse: true
                    focus: true
                    clip: true
                }
            }
        }

        Column {
            spacing: 6
            anchors.horizontalCenter: parent.horizontalCenter

            Text {
                text: qsTr("LOGIN:")
                font.pixelSize: 12
            }

            Rectangle {
                width: 260
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1
                TextField {
                    id: loginField
                    anchors.fill: parent
                    anchors.margins: 6
                    text: backend.editLogin
                    placeholderText: qsTr("np. user@example.com")
                    background: null
                    inputMethodHints: Qt.ImhEmailCharactersOnly
                    font.pixelSize: 12
                    selectByMouse: true
                    clip: true
                }
            }
        }

        Row {
            spacing: 8
            anchors.horizontalCenter: parent.horizontalCenter

            Rectangle {
                width: 170
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1

                Row {
                    id: passwordRow
                    anchors.fill: parent
                    anchors.margins: 4
                    spacing: 4

                    TextField {
                        id: passwordField
                        width: Math.max(0, passwordRow.width - revealButton.width - copyButton.width - passwordRow.spacing * 2)
                        text: backend.editPassword
                        echoMode: TextInput.Password
                        font.pixelSize: 12
                        anchors.verticalCenter: parent.verticalCenter
                        selectByMouse: true
                        background: null
                        placeholderText: qsTr("hasło")
                        placeholderTextColor: "#66000000"
                        clip: true
                    }

                    Button {
                        id: revealButton
                        width: 32
                        height: 24
                        text: qsTr("👁️")
                        onClicked: passwordField.echoMode = passwordField.echoMode === TextInput.Password ? TextInput.Normal : TextInput.Password
                    }

                    Button {
                        id: copyButton
                        width: 30
                        height: 24
                        text: qsTr("📋")
                        onClicked: backend.copyPlainText(passwordField.text)
                    }
                }
            }

            SpinBox {
                id: passwordLengthSpinBox
                width: 70
                height: 32
                from: 6
                to: 64
                value: 16
                editable: true
                anchors.verticalCenter: parent.verticalCenter
            }

            Button {
                id: generateButton
                width: 90
                height: 32
                text: qsTr("GENERUJ")
                onClicked: passwordField.text = backend.generatePassword(passwordLengthSpinBox.value)
            }
        }

        Row {
            id: strengthRow
            spacing: 8
            anchors.horizontalCenter: parent.horizontalCenter
            property int strengthLevel: calculateStrength(passwordField.text)

            function calculateStrength(password) {
                var level = 0
                if (password.length > 12)
                    level += 1
                if (/[a-z]/.test(password) && /[A-Z]/.test(password))
                    level += 1
                if (/\d/.test(password))
                    level += 1
                if (/[^a-zA-Z0-9]/.test(password))
                    level += 1
                return level
            }

            Text {
                text: qsTr("SIŁA HASŁA:")
                font.pixelSize: 12
            }

            Rectangle {
                width: 30
                height: 10
                color: strengthRow.strengthLevel >= 1 ? "lightgray" : "white"
                border.color: "black"
                border.width: 1
            }
            Rectangle {
                width: 30
                height: 10
                color: strengthRow.strengthLevel >= 2 ? "lightgray" : "white"
                border.color: "black"
                border.width: 1
            }
            Rectangle {
                width: 30
                height: 10
                color: strengthRow.strengthLevel >= 3 ? "lightgray" : "white"
                border.color: "black"
                border.width: 1
            }
            Rectangle {
                width: 30
                height: 10
                color: strengthRow.strengthLevel >= 4 ? "lightgray" : "white"
                border.color: "black"
                border.width: 1
            }
        }

        Row {
            id: expiryRow
            spacing: 8
            anchors.horizontalCenter: parent.horizontalCenter
            property date fallbackDate: new Date()

            function parseDateString(value) {
                var trimmed = value.trim()
                if (!trimmed)
                    return null

                var isoMatch = /^(\d{4})-(\d{2})-(\d{2})$/.exec(trimmed)
                if (isoMatch)
                    return new Date(Number(isoMatch[1]), Number(isoMatch[2]) - 1, Number(isoMatch[3]))

                var shortMatch = /^(\d{2})[/.](\d{2})[/.](\d{4})$/.exec(trimmed)
                if (shortMatch)
                    return new Date(Number(shortMatch[3]), Number(shortMatch[2]) - 1, Number(shortMatch[1]))

                return null
            }

            function daysInMonth(month, year) {
                return new Date(year, month, 0).getDate()
            }

            function applyDateToPickers(date) {
                var chosen = date || new Date()
                yearSpinBox.value = chosen.getFullYear()
                monthSpinBox.value = chosen.getMonth() + 1
                daySpinBox.to = daysInMonth(monthSpinBox.value, yearSpinBox.value)
                daySpinBox.value = Math.min(chosen.getDate(), daySpinBox.to)
            }

            function dateFromPickers() {
                var clampedDay = Math.min(daySpinBox.value, daysInMonth(monthSpinBox.value, yearSpinBox.value))
                return new Date(yearSpinBox.value, monthSpinBox.value - 1, clampedDay)
            }

            function openCalendar() {
                var parsed = parseDateString(expiryField.text)
                fallbackDate = new Date()
                applyDateToPickers(parsed || fallbackDate)
                datePopup.open()
            }

            Text {
                text: qsTr("WAŻNOŚĆ HASŁA:")
                font.pixelSize: 12
            }

            Rectangle {
                width: 140
                height: 32
                color: "transparent"
                border.color: "black"
                border.width: 1

                TextInput {
                    id: expiryField
                    anchors.fill: parent
                    anchors.margins: 6
                    text: backend.editExpire
                    font.pixelSize: 12
                    clip: true
                }
            }

            Button {
                id: calendarButton
                width: 40
                height: 32
                text: qsTr("📅")
                onClicked: expiryRow.openCalendar()
            }
        }
    }

    Popup {
        id: datePopup
        width: 320
        height: 220
        modal: true
        focus: true
        closePolicy: Popup.CloseOnPressOutside | Popup.CloseOnEscape
        anchors.centerIn: parent
        background: Rectangle {
            color: "#f7f7f7"
            border.color: "black"
            border.width: 1
            radius: 4
        }

        onOpened: {
            var parsed = expiryRow.parseDateString(expiryField.text)
            expiryRow.fallbackDate = new Date()
            expiryRow.applyDateToPickers(parsed || expiryRow.fallbackDate)
        }

        Column {
            anchors.fill: parent
            anchors.margins: 12
            spacing: 12

            Text {
                text: qsTr("Wybierz datę ważności")
                font.pixelSize: 14
                font.bold: true
            }

            Row {
                spacing: 12
                anchors.horizontalCenter: parent.horizontalCenter

                Column {
                    spacing: 4
                    Text { text: qsTr("Dzień"); font.pixelSize: 12 }
                    SpinBox {
                        id: daySpinBox
                        from: 1
                        to: 31
                        value: 1
                    }
                }

                Column {
                    spacing: 4
                    Text { text: qsTr("Miesiąc"); font.pixelSize: 12 }
                    SpinBox {
                        id: monthSpinBox
                        from: 1
                        to: 12
                        value: 1
                        onValueChanged: {
                            daySpinBox.to = expiryRow.daysInMonth(value, yearSpinBox.value)
                            daySpinBox.value = Math.min(daySpinBox.value, daySpinBox.to)
                        }
                    }
                }

                Column {
                    spacing: 4
                    Text { text: qsTr("Rok"); font.pixelSize: 12 }
                    SpinBox {
                        id: yearSpinBox
                        from: 1970
                        to: 2100
                        value: new Date().getFullYear()
                        onValueChanged: {
                            daySpinBox.to = expiryRow.daysInMonth(monthSpinBox.value, value)
                            daySpinBox.value = Math.min(daySpinBox.value, daySpinBox.to)
                        }
                    }
                }
            }

            Row {
                spacing: 8
                anchors.horizontalCenter: parent.horizontalCenter

                Button {
                    text: qsTr("DZISIAJ")
                    onClicked: expiryRow.applyDateToPickers(new Date())
                }

                Button {
                    text: qsTr("ANULUJ")
                    onClicked: datePopup.close()
                }

                Button {
                    text: qsTr("USTAW")
                    onClicked: {
                        var selected = expiryRow.dateFromPickers()
                        expiryField.text = Qt.formatDate(selected, "yyyy-MM-dd")
                        datePopup.close()
                    }
                }
            }
        }
    }

    Button {
        id: saveButton
        text: qsTr("ZAPISZ")
        width: 160
        height: 60
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 80
        onClicked: backend.savePassword(serviceField.text, loginField.text, passwordField.text, expiryField.text)
    }
}
