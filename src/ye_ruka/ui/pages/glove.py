from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)
from serial.tools import list_ports

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.models import AxisConfig
from ye_ruka.ui.widgets.common import card, subtitle_label, title_label
from ye_ruka.ui.widgets.visualizers import HandTelemetryWidget, SignalVisualizer


BAUDRATES = (9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600, 1000000, 2000000)


class GlovePage(QWidget):
    def __init__(self, controller: ApplicationController) -> None:
        super().__init__()
        self.controller = controller
        self.axes = controller.axes
        self.visualizers: list[SignalVisualizer] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(16)

        header = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(title_label("Рукавиця"))
        text.addWidget(subtitle_label("Живе зчитування датчиків згину та передавання руху на роботизовану кисть"))
        header.addLayout(text)
        header.addStretch(1)
        self.state_badge = QLabel("OFFLINE")
        self.state_badge.setObjectName("StateBadge")
        header.addWidget(self.state_badge)
        root.addLayout(header)

        connection, connection_layout = card(name="GlassStrip")
        connection_layout.setContentsMargins(14, 10, 14, 10)
        row = QHBoxLayout()
        row.setSpacing(9)
        self.port = QComboBox()
        self.port.setMinimumWidth(220)
        self.baud = QComboBox()
        for value in BAUDRATES:
            self.baud.addItem(str(value), value)
        self.format = QComboBox()
        self.format.addItem("Автовизначення", "auto")
        self.format.addItem("Масив [1,2,3]", "array")
        self.format.addItem("CSV 1,2,3", "csv")
        self.format.addItem("Префіксований", "prefixed")
        self.channels = QSpinBox()
        self.channels.setRange(1, 32)
        self.channels.setSuffix(" каналів")
        self.refresh = QPushButton("↻")
        self.refresh.setObjectName("RoundButton")
        self.refresh.setFixedSize(36, 36)
        self.connect_button = QPushButton("Підключити")
        self.connect_button.setProperty("accent", True)
        self.disconnect_button = QPushButton("Відключити")
        self.auto_reconnect = QCheckBox("AUTO")
        self.auto_reconnect.setToolTip("Автоперепідключення рукавиці")
        row.addWidget(QLabel("PORT"))
        row.addWidget(self.port, 2)
        row.addWidget(QLabel("BAUD"))
        row.addWidget(self.baud)
        row.addWidget(QLabel("FORMAT"))
        row.addWidget(self.format)
        row.addWidget(self.channels)
        row.addWidget(self.refresh)
        row.addWidget(self.connect_button)
        row.addWidget(self.disconnect_button)
        row.addWidget(self.auto_reconnect)
        connection_layout.addLayout(row)
        root.addWidget(connection)

        body = QHBoxLayout()
        body.setSpacing(18)
        model_panel, model_layout = card(name="AmbientSurface")
        model_layout.setContentsMargins(8, 8, 8, 8)
        self.hand_model = HandTelemetryWidget()
        model_layout.addWidget(self.hand_model, 1)
        model_panel.setMinimumWidth(360)
        body.addWidget(model_panel, 2)

        signal_panel = QFrame()
        signal_panel.setObjectName("SignalDeck")
        signal_layout = QVBoxLayout(signal_panel)
        signal_layout.setContentsMargins(4, 0, 4, 0)
        signal_layout.setSpacing(8)
        signal_header = QHBoxLayout()
        signal_title = QLabel("SENSOR STREAM")
        signal_title.setObjectName("SectionEyebrow")
        self.rate_label = QLabel("0.0 Hz")
        self.rate_label.setObjectName("MetricValueSmall")
        self.packet_count = QLabel("0 packets")
        self.packet_count.setObjectName("MicroText")
        signal_header.addWidget(signal_title)
        signal_header.addStretch(1)
        signal_header.addWidget(self.rate_label)
        signal_header.addWidget(self.packet_count)
        signal_layout.addLayout(signal_header)
        self.signal_scroll = QScrollArea()
        self.signal_scroll.setWidgetResizable(True)
        self.signal_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.signal_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.signal_container = QWidget()
        self.signal_row = QHBoxLayout(self.signal_container)
        self.signal_row.setContentsMargins(0, 0, 0, 0)
        self.signal_row.setSpacing(6)
        self.signal_scroll.setWidget(self.signal_container)
        signal_layout.addWidget(self.signal_scroll, 1)
        body.addWidget(signal_panel, 5)
        root.addLayout(body, 1)

        footer, footer_layout = card(name="GlassStrip")
        footer_layout.setContentsMargins(14, 9, 14, 9)
        footer_row = QHBoxLayout()
        self.last_packet = QLineEdit()
        self.last_packet.setReadOnly(True)
        self.last_packet.setPlaceholderText("Очікування пакета рукавиці…")
        self.last_packet.setObjectName("PacketField")
        self.error_label = QLabel("0 errors")
        self.error_label.setObjectName("MicroText")
        self.source_note = QLabel("Режим рукавиці активується при відкритті цієї сторінки")
        self.source_note.setObjectName("MicroText")
        footer_row.addWidget(QLabel("RX"))
        footer_row.addWidget(self.last_packet, 1)
        footer_row.addWidget(self.source_note)
        footer_row.addWidget(self.error_label)
        footer_layout.addLayout(footer_row)
        root.addWidget(footer)

        self.refresh.clicked.connect(self.scan_ports)
        self.connect_button.clicked.connect(self.connect_glove)
        self.disconnect_button.clicked.connect(controller.disconnect_glove)
        controller.glove_state_changed.connect(self.set_state)
        controller.glove_values_changed.connect(self.set_values)
        controller.glove_packet_changed.connect(self.last_packet.setText)
        controller.diagnostics_changed.connect(self.update_metrics)
        controller.axes_changed.connect(self.rebuild_visualizers)
        self.load_config()
        self.rebuild_visualizers(self.axes)
        self.scan_ports()

    def showEvent(self, event) -> None:
        self.controller.set_mode("glove")
        super().showEvent(event)

    def load_config(self) -> None:
        cfg = self.controller.data["glove"]
        self.baud.setCurrentIndex(max(0, self.baud.findData(int(cfg.get("baudrate", 115200)))))
        self.format.setCurrentIndex(max(0, self.format.findData(cfg.get("format", "auto"))))
        self.channels.setValue(int(cfg.get("channel_count", len(self.axes))))
        self.auto_reconnect.setChecked(bool(cfg.get("auto_reconnect", True)))

    def scan_ports(self) -> None:
        configured = self.controller.data["glove"].get("port", "")
        self.port.clear()
        ports = list(list_ports.comports())
        if not ports:
            self.port.addItem("COM-порти не знайдено", "")
            return
        robot_port = self.controller.data["serial"].get("port", "")
        for item in ports:
            ids = f"  {item.vid:04X}:{item.pid:04X}" if item.vid is not None and item.pid is not None else ""
            suffix = "  • ROBOT" if item.device == robot_port else ""
            self.port.addItem(f"{item.device}  ·  {item.description}{ids}{suffix}", item.device)
        index = self.port.findData(configured)
        self.port.setCurrentIndex(max(0, index))

    def connect_glove(self) -> None:
        cfg = self.controller.data["glove"]
        cfg.update(
            {
                "port": self.port.currentData() or "",
                "baudrate": int(self.baud.currentData()),
                "format": self.format.currentData(),
                "channel_count": self.channels.value(),
                "auto_reconnect": self.auto_reconnect.isChecked(),
            }
        )
        self.controller.config.save()
        self.controller.update_glove_config()
        self.rebuild_visualizers(self.controller.axes)
        self.controller.connect_glove()

    def rebuild_visualizers(self, axes: list[AxisConfig]) -> None:
        self.axes = axes
        while self.signal_row.count():
            item = self.signal_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.visualizers.clear()
        language = self.controller.data.get("language", "uk")
        count = max(int(self.controller.data["glove"].get("channel_count", len(axes))), len(axes))
        axis_by_channel = {axis.glove_channel: axis for axis in axes if axis.glove_channel >= 0}
        for channel in range(count):
            axis = axis_by_channel.get(channel)
            label = axis.name(language).split(":")[0] if axis else f"Sensor {channel + 1}"
            visualizer = SignalVisualizer(label, channel)
            self.signal_row.addWidget(visualizer)
            self.visualizers.append(visualizer)
        self.signal_row.addStretch(1)

    def set_values(self, raw: list[float], normalized: list[float]) -> None:
        for index, visualizer in enumerate(self.visualizers):
            visualizer.set_value(raw[index] if index < len(raw) else 0.0, normalized[index] if index < len(normalized) else 0.0)
        self.hand_model.set_values(normalized)

    def set_state(self, state: str) -> None:
        labels = {"connected": "LIVE", "disconnected": "OFFLINE", "error": "ERROR"}
        self.state_badge.setText(labels.get(state, state.upper()))
        self.state_badge.setProperty("state", state)
        self.state_badge.style().unpolish(self.state_badge)
        self.state_badge.style().polish(self.state_badge)
        self.connect_button.setEnabled(state != "connected")
        self.disconnect_button.setEnabled(state == "connected")

    def update_metrics(self, snapshot) -> None:
        self.rate_label.setText(f"{snapshot.glove_rate:.1f} Hz")
        self.packet_count.setText(f"{snapshot.glove_packets} packets")
        self.error_label.setText(f"{snapshot.glove_errors} errors")
