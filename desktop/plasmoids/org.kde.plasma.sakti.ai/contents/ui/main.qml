import QtQuick
import QtQuick.Layouts
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.components as PlasmaComponents3

// SaktiAI Sidebar — the AI-first assistant surface.
// Inhabit the edge of the screen, ready to take natural language.
Item {
    id: assistantRoot

    property string aiPrompt: "Hey Sakti… describing actions in natural language"
    property int promptLimit: 4

    PlasmaCore.DataSource {
        id: aiService
        engine: "sakti"
        connectedSources: ["status"]
    }

    Rectangle {
        id: panel
        anchors.fill: parent
        radius: 20
        color: Qt.rgba(0.086, 0.11, 0.17, 0.85) // Deep Space glass
        border.color: Qt.rgba(1, 1, 1, 0.12)

        ColumnLayout {
            anchors.centerIn: parent
            anchors.margins: 16
            spacing: 12
            width: parent.width - 32

            PlasmaComponents3.Label {
                text: "SaktiAI"
                font.bold: true
                font.pixelSize: PlasmaCore.Theme.defaultFont.weight + 4
                Layout.alignment: Qt.AlignHCenter
            }

            PlasmaComponents3.Label {
                text: "Ready. Ask anything."
                opacity: 0.6
                Layout.alignment: Qt.AlignHCenter
            }

            PlasmaComponents3.TextField {
                id: promptField
                Layout.fillWidth: true
                placeholderText: aiPrompt
            }

            PlasmaComponents3.Button {
                text: "Ask Sakti"
                Layout.alignment: Qt.AlignHCenter
                onClicked: {
                    var value = promptField.text.trim()
                    planner_helper(value)
                }
            }
        }
    }

    function planner_helper(input) {
        // Backend wiring arrives in Phase 3 (AI Brain).
        aiData.data = {"input": input, "status": "queued"}
        promptField.clear()
    }
}