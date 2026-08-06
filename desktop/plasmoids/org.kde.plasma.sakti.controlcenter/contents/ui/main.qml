import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.plasmoid

// Sakti Control Center — a floating glass panel for quick toggles.
Item {
    id: root

    Layout.minimumWidth: 360
    Layout.minimumHeight: 260

    PlasmaCore.DataSource {
        id: batterySource
        engine: "battery"
        connectedSources: "Battery0"
    }

    PlasmaCore.DataSource {
        id: networkSource
        engine: "network"
        connectedSources: "Interfaces"
    }

    Rectangle {
        anchors.fill: parent
        radius: 22
        color: Qt.rgba(0.086, 0.11, 0.17, 0.88)
        border.color: Qt.rgba(1, 1, 1, 0.12)

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 14

            RowLayout {
                Layout.fillWidth: true
                spacing: 10

                // Brightness
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    PlasmaComponents3.Label {
                        text: Math.round(brightnessSlider.value * 100) + "%"
                        opacity: 0.7
                        font.pixelSize: 12
                    }
                    PlasmaComponents3.Slider {
                        id: brightnessSlider
                        Layout.fillWidth: true
                        value: 0.8
                    }
                }

                // Volume
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 6
                    PlasmaComponents3.Label {
                        text: "Volume"
                        opacity: 0.7
                        font.pixelSize: 12
                    }
                    PlasmaComponents3.Slider {
                        id: volumeSlider
                        Layout.fillWidth: true
                        value: 0.6
                    }
                }
            }

            PlasmaComponents3.Switch {
                id: wifiSwitch
                text: "Wi-Fi"
                checked: true
                Layout.fillWidth: true
            }

            PlasmaComponents3.Switch {
                text: "Bluetooth"
                checked: false
                Layout.fillWidth: true
            }

            PlasmaComponents3.Label {
                text: "Media · Nothing playing"
                opacity: 0.6
                Layout.fillWidth: true
                horizontalAlignment: Qt.AlignHCenter
            }

            RowLayout {
                Layout.fillWidth: true
                Layout.topMargin: 6
                PlasmaComponents3.Button {
                    text: "Lock"
                    onClicked: { }
                }
                PlasmaComponents3.Button {
                    text: "Suspend"
                    onClicked: { }
                }
                PlasmaComponents3.Button {
                    text: "Power"
                    onClicked: { }
                }
            }
        }
    }
}