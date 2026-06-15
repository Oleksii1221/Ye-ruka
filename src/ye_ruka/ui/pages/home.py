from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from ye_ruka.core.models import DiagnosticsSnapshot
from ye_ruka.ui.widgets.common import subtitle_label, title_label
from ye_ruka.ui.widgets.visualizers import SystemFlowWidget


class HomePage(QWidget):
    navigate = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 25, 30, 28)
        root.setSpacing(18)

        hero = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(5)
        eyebrow = QLabel("YE-RUKA  /  MOTION BRIDGE")
        eyebrow.setObjectName("SectionEyebrow")
        left.addWidget(eyebrow)
        left.addWidget(title_label("Рух людини — у механіку кисті"))
        left.addWidget(
            subtitle_label(
                "Камера або сенсорна рукавиця формують єдиний потік керування. "
                "Є-Рука згладжує, калібрує та безпечно передає його на ESP32."
            )
        )
        hero.addLayout(left, 1)
        quick = QHBoxLayout()
        self.auto_button = QPushButton("Відкрити камеру")
        self.auto_button.setProperty("accent", True)
        self.glove_button = QPushButton("Підключити рукавицю")
        self.manual_button = QPushButton("Ручний режим")
        quick.addWidget(self.auto_button)
        quick.addWidget(self.glove_button)
        quick.addWidget(self.manual_button)
        hero.addLayout(quick)
        root.addLayout(hero)

        self.flow = SystemFlowWidget()
        root.addWidget(self.flow, 1)

        metrics = QFrame()
        metrics.setObjectName("MetricStrip")
        row = QHBoxLayout(metrics)
        row.setContentsMargins(22, 14, 22, 14)
        row.setSpacing(28)
        self.camera_value = self._metric(row, "CAMERA", "OFF")
        self.glove_value = self._metric(row, "GLOVE", "OFF")
        self.serial_value = self._metric(row, "ROBOT LINK", "OFF")
        self.fps_value = self._metric(row, "VISION FPS", "0.0")
        self.glove_rate_value = self._metric(row, "GLOVE RATE", "0.0 Hz")
        self.tx_value = self._metric(row, "PACKETS", "0")
        root.addWidget(metrics)

        safety = QHBoxLayout()
        note = QLabel("Передавання не запускається автоматично. Кути DS3225 обмежуються у застосунку та на ESP32.")
        note.setObjectName("MicroText")
        calibrate = QPushButton("Калібрування руки")
        safety.addWidget(note)
        safety.addStretch(1)
        safety.addWidget(calibrate)
        root.addLayout(safety)

        self.auto_button.clicked.connect(lambda: self.navigate.emit("automatic"))
        self.glove_button.clicked.connect(lambda: self.navigate.emit("glove"))
        self.manual_button.clicked.connect(lambda: self.navigate.emit("manual"))
        calibrate.clicked.connect(lambda: self.navigate.emit("calibration"))

    @staticmethod
    def _metric(layout: QHBoxLayout, label: str, value: str) -> QLabel:
        box = QVBoxLayout()
        box.setSpacing(1)
        title = QLabel(label)
        title.setObjectName("SectionEyebrow")
        result = QLabel(value)
        result.setObjectName("MetricValue")
        box.addWidget(title)
        box.addWidget(result)
        widget = QWidget()
        widget.setLayout(box)
        layout.addWidget(widget)
        return result

    def update_diagnostics(self, snapshot: DiagnosticsSnapshot) -> None:
        camera_live = snapshot.camera_state == "running"
        glove_live = snapshot.glove_state == "connected"
        serial_live = snapshot.serial_state == "connected"
        self.camera_value.setText("LIVE" if camera_live else "OFF")
        self.glove_value.setText("LIVE" if glove_live else "OFF")
        self.serial_value.setText("LIVE" if serial_live else "OFF")
        self.fps_value.setText(f"{snapshot.camera_fps:.1f}")
        self.glove_rate_value.setText(f"{snapshot.glove_rate:.1f} Hz")
        self.tx_value.setText(str(snapshot.packets_sent))
        self.flow.set_states(camera_live, glove_live, serial_live, snapshot.packets_sent > 0)
