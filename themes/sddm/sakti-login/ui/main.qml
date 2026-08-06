import QtQuick 2.15
import QtQuick.Layouts 1.15
import SddmComponents 2.0

// Sakti Linux AI — Login screen (SDDM QML theme)
Rectangle {
    id: root
    width: 1280
    height: 720
    color: "#0f172a"

    // ------------------------------------------------------ data models
    UserModel { id: userModel }
    SessionModel { id: sessionModel }

    // ------------------------------------------------------ background
    Image {
        id: background
        anchors.fill: parent
        source: config.Background || "wallpaper.svg"
        fillMode: Image.PreserveAspectCrop
        z: -2
    }

    Rectangle {
        anchors.fill: parent
        color: "#0f172a"
        opacity: 0.45
        z: -1
    }

    // ------------------------------------------------------------ card
    Rectangle {
        id: card
        anchors.centerIn: parent
        width: 420
        height: 360
        radius: 24
        color: "#cc1e293b"
        border.color: "#22ffffff"
        border.width: 1

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 16
            width: parent.width - 72

            Image {
                source: "logo.svg"
                Layout.alignment: Qt.AlignHCenter
                Layout.preferredWidth: 84
                Layout.preferredHeight: 84
            }

            Text {
                text: "SaktiLinux AI"
                color: "#f8fafc"
                font.pixelSize: 26
                font.weight: Font.DemiBold
                Layout.alignment: Qt.AlignHCenter
            }

            // Username
            TextBox {
                id: username
                width: parent.width
                text: userModel.lastUser
                font.pixelSize: 15
                color: "#f8fafc"
                onAccepted: password.focus = true
            }

            // Password
            TextBox {
                id: password
                width: parent.width
                font.pixelSize: 15
                color: "#f8fafc"
                echoMode: TextInput.Password
                placeholderText: qsTr("Password")
                focus: true
                Keys.onReturnPressed: loginButton.clicked()
            }

            // Session
            ComboBox {
                id: session
                model: sessionModel
                width: parent.width
                currentIndex: sessionModel.lastIndex
                color: "#f8fafc"
            }

            // Sign in
            Button {
                id: loginButton
                width: parent.width
                height: 44
                radius: 12
                color: "#22d3ee"
                textColor: "#0f172a"
                text: qsTr("Sign in")
                onClicked: {
                    userModel.username = username.text
                    userModel.password = password.text
                    userModel.session = sessionModel.currentIndex
                    userModel.login()
                }
            }
        }
    }

    // ----------------------------------------------------- brand dots
    Row {
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.bottom: parent.bottom
        anchors.bottomMargin: 26
        spacing: 10
        opacity: 0.75

        Rectangle { width: 7; height: 7; radius: 4; color: "#22d3ee" }
        Rectangle { width: 7; height: 7; radius: 4; color: "#818cf8" }
        Rectangle { width: 7; height: 7; radius: 4; color: "#c084fc" }
    }

    Component.onCompleted: password.forceActiveFocus()
}