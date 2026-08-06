import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3

// Sakti Clock — a premium, glass clock/date widget.
Item {
    id: root

    Layout.minimumWidth: 160
    Layout.minimumHeight: 160

    Timer {
        interval: 1000
        running: true
        repeat: true
        onTriggered: {
            var now = new Date()
            timeLabel.text = now.toLocaleTimeString(Qt.locale(), "hh:mm")
            dateLabel.text = now.toLocaleDateString(Qt.locale(), "dddd, d MMMM")
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: 24
        color: Qt.rgba(0.086, 0.11, 0.17, 0.72)
        border.color: Qt.rgba(1, 1, 1, 0.10)

        ColumnLayout {
            anchors.centerIn: parent
            spacing: 4

            PlasmaComponents3.Label {
                id: timeLabel
                text: "--:--"
                font.pixelSize: 38
                font.weight: Font.DemiBold
                font.family: "Geist"
                Layout.alignment: Qt.AlignHCenter
            }

            PlasmaComponents3.Label {
                id: dateLabel
                text: "—"
                opacity: 0.65
                font.pixelSize: 13
                Layout.alignment: Qt.AlignHCenter
            }
        }
    }
}