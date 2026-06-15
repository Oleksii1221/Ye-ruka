from __future__ import annotations

import json
from datetime import datetime

from PySide6.QtWidgets import (
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ye_ruka.core.models import DiagnosticsSnapshot
from ye_ruka.ui.widgets.common import card, subtitle_label, title_label


class DiagnosticsPage(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.snapshot = DiagnosticsSnapshot()
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(14)
        header = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(title_label("Діагностика"))
        text.addWidget(subtitle_label("Стан джерел, частоти, пакети та журнали в реальному часі"))
        header.addLayout(text)
        header.addStretch(1)
        export = QPushButton("Експорт журналу")
        clear = QPushButton("Очистити")
        header.addWidget(export)
        header.addWidget(clear)
        root.addLayout(header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(8)
        grid.setVerticalSpacing(8)
        self.labels: dict[str, QLabel] = {}
        fields = [
            ("camera", "CAMERA"),
            ("fps", "VISION FPS"),
            ("processing", "FRAME TIME"),
            ("glove", "GLOVE LINK"),
            ("glove_rate", "GLOVE RATE"),
            ("glove_packets", "GLOVE PACKETS"),
            ("serial", "ROBOT LINK"),
            ("packets", "TX PACKETS"),
            ("errors", "TOTAL ERRORS"),
            ("channels", "ACTIVE CHANNELS"),
        ]
        for index, (key, name) in enumerate(fields):
            frame, layout = card(name="MetricTile")
            caption = QLabel(name)
            caption.setObjectName("SectionEyebrow")
            value = QLabel("—")
            value.setObjectName("MetricValueSmall")
            layout.addWidget(caption)
            layout.addWidget(value)
            self.labels[key] = value
            grid.addWidget(frame, index // 5, index % 5)
        root.addLayout(grid)

        splitter = QSplitter()
        values_card, values_layout = card(name="SettingsSurface")
        values_title = QLabel("DATA PIPELINE")
        values_title.setObjectName("SectionEyebrow")
        values_layout.addWidget(values_title)
        self.values = QPlainTextEdit()
        self.values.setReadOnly(True)
        values_layout.addWidget(self.values)
        log_card, log_layout = card(name="SettingsSurface")
        log_title = QLabel("EVENT LOG")
        log_title.setObjectName("SectionEyebrow")
        log_layout.addWidget(log_title)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        log_layout.addWidget(self.log)
        splitter.addWidget(values_card)
        splitter.addWidget(log_card)
        splitter.setSizes([560, 560])
        root.addWidget(splitter, 1)
        export.clicked.connect(self.export_log)
        clear.clicked.connect(self.log.clear)

    def append_log(self, text: str) -> None:
        self.log.appendPlainText(f"[{datetime.now():%H:%M:%S}] {text}")

    def update_snapshot(self, snapshot: DiagnosticsSnapshot) -> None:
        self.snapshot = snapshot
        self.labels["camera"].setText(snapshot.camera_state.upper())
        self.labels["fps"].setText(f"{snapshot.camera_fps:.1f}")
        self.labels["processing"].setText(f"{snapshot.processing_ms:.1f} ms")
        self.labels["glove"].setText(snapshot.glove_state.upper())
        self.labels["glove_rate"].setText(f"{snapshot.glove_rate:.1f} Hz")
        self.labels["glove_packets"].setText(str(snapshot.glove_packets))
        self.labels["serial"].setText(snapshot.serial_state.upper())
        self.labels["packets"].setText(str(snapshot.packets_sent))
        self.labels["errors"].setText(str(snapshot.serial_errors + snapshot.glove_errors))
        self.labels["channels"].setText(str(len(snapshot.servo_values)))
        payload = {
            "vision_raw": snapshot.raw_values,
            "glove_raw": snapshot.glove_raw_values,
            "glove_normalized": snapshot.glove_normalized_values,
            "filtered": snapshot.filtered_values,
            "servo": snapshot.servo_values,
            "robot_packet": snapshot.last_packet,
            "glove_packet": snapshot.glove_last_packet,
        }
        self.values.setPlainText(json.dumps(payload, ensure_ascii=False, indent=2))

    def export_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Експорт журналу",
            f"ye-ruka-log-{datetime.now():%Y%m%d-%H%M%S}.txt",
            "Text (*.txt)",
        )
        if not path:
            return
        content = self.log.toPlainText() + "\n\n" + self.values.toPlainText()
        with open(path, "w", encoding="utf-8") as file:
            file.write(content)
