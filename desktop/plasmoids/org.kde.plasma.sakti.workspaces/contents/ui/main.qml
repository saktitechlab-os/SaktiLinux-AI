import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.plasmoid

// Sakti Workspace Switcher — glass grid for virtual desktops.
Item {
    id: root

    Layout.minimumWidth: 320
    Layout.minimumHeight: 180

    // Workspaces reflect the current Sakti work mode:
    //  default: 2 workspaces · developer: 4 · designer: 3 · cyber: 3
    property int workspaceCount: 2

    PlasmaCore.DataSource {
        id: workspaceSource
        engine: "org.kde.plasma.sakti.modes"
        connectedSources: ["active"]
        onDataChanged: {
            var mode = data["active"]
            workspaceCount = mode === "developer" ? 4
                          : mode === "designer" ? 3
                          : mode === "cyber" ? 3 : 2
        }
    }

    Rectangle {
        anchors.fill: parent
        radius: 22
        color: Qt.rgba(0.086, 0.11, 0.17, 0.85)
        border.color: Qt.rgba(1, 1, 1, 0.12)

        Grid {
            anchors.centerIn: parent
            columns: 4
            rows: 1
            spacing: 12

            Repeater {
                model: root.workspaceCount
                Rectangle {
                    width: 64
                    height: 90
                    radius: 12
                    color: Qt.rgba(1, 1, 1, index === 0 ? 0.10 : 0.04)
                    border.color: Qt.rgba(1, 1, 1, 0.14)
                    ColumnLayout {
                        anchors.centerIn: parent
                        spacing: 6
                        PlasmaCore.IconItem {
                            source: "view-grid"
                            Layout.alignment: Qt.AlignHCenter
                            Layout.preferredWidth: 22
                            Layout.preferredHeight: 22
                        }
                        PlasmaComponents3.Label {
                            text: "WS " + (index + 1)
                            font.pixelSize: 11
                            opacity: 0.7
                        }
                    }
                }
            }
        }
    }
}