import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3
import org.kde.plasma.plasmoid

// Sakti Spotlight — Raycast-style launcher overlay with AI-ranked results.
Item {
    id: root

    Layout.minimumWidth: 640
    Layout.minimumHeight: 200

    property string query: ""

    PlasmaCore.SortFilterModel {
        id: filteredApps
        sourceModel: root.model.apps
        filterRole: "Name"
        filterPattern: root.query
    }

    Rectangle {
        id: overlay
        anchors.fill: parent
        radius: 26
        color: Qt.rgba(0.055, 0.07, 0.12, 0.92)
        border.color: Qt.rgba(1, 1, 1, 0.14)
        anchors.margins: 24

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 20
            spacing: 12

            PlasmaComponents3.TextField {
                id: searchField
                Layout.fillWidth: true
                placeholderText: "Search apps, files, commands — or ask Sakti…"
                font.pixelSize: 17
                onTextChanged: root.query = text
                focus: true
            }

            ListView {
                id: resultList
                Layout.fillWidth: true
                Layout.fillHeight: true
                clip: true
                model: root.query.length > 0 ? filteredApps : root.model.apps
                delegate: ItemDelegate {
                    width: ListView.view.width
                    height: 44
                    onClicked: root.model.apps.launch(index)
                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 10
                        spacing: 12
                        PlasmaCore.IconItem {
                            source: model.DecorationRole
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 26
                        }
                        PlasmaComponents3.Label {
                            text: model.Name
                            elide: Text.ElideRight
                            Layout.fillWidth: true
                        }
                    }
                }
            }
        }
    }

    Component.onCompleted: searchField.forceActiveFocus()
}