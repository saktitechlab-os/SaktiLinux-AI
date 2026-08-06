import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3

// Sakti Notification Center — smart notifications with grouping.
Item {
    id: root

    Layout.minimumWidth: 380
    Layout.minimumHeight: 200

    ListModel {
        id: sampleModel
        ListElement { app: "SaktiAI"; title: "Welcome to SaktiLinux AI"; body: "The AI native Linux distribution." }
        ListElement { app: "System"; title: "Update available"; body: "A new system update is ready to install." }
    }

    Rectangle {
        anchors.fill: parent
        radius: 22
        color: Qt.rgba(0.086, 0.11, 0.17, 0.88)
        border.color: Qt.rgba(1, 1, 1, 0.12)

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 18
            spacing: 10

            RowLayout {
                Layout.fillWidth: true
                PlasmaComponents3.Label {
                    text: "Notifications"
                    font.bold: true
                    font.pixelSize: 15
                }
                Item { Layout.fillWidth: true }
                PlasmaComponents3.Button {
                    text: "Clear all"
                    onClicked: sampleModel.clear()
                }
            }

            ListView {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 8
                model: sampleModel
                clip: true

                delegate: Rectangle {
                    width: ListView.view.width
                    height: 72
                    radius: 14
                    color: Qt.rgba(0.086, 0.11, 0.17, 0.5)
                    border.color: Qt.rgba(1, 1, 1, 0.08)

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 10

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 2
                            PlasmaComponents3.Label {
                                text: model.app
                                font.pixelSize: 11
                                opacity: 0.6
                            }
                            PlasmaComponents3.Label {
                                text: model.title
                                font.bold: true
                                font.pixelSize: 13
                                elide: Text.ElideRight
                            }
                            PlasmaComponents3.Label {
                                text: model.body
                                font.pixelSize: 12
                                opacity: 0.8
                                elide: Text.ElideRight
                            }
                        }
                    }
                }
            }
        }
    }
}