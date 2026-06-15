from __future__ import annotations

from statistics import median

import cv2
from PySide6.QtCore import Qt
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.models import TrackingResult
from ye_ruka.ui.widgets.common import VideoLabel, card, title_label


POSES = [
    ("open", "Повністю розкрита долоня"),
    ("fist", "Повністю стиснутий кулак"),
    ("index", "Уточнити згинання вказівного"),
    ("middle", "Уточнити згинання середнього"),
    ("ring", "Уточнити згинання безіменного"),
    ("little", "Уточнити згинання мізинця"),
    ("thumb_flex", "Зігнути фаланги великого пальця"),
    ("thumb_opposition", "Звести великий палець до вказівного"),
    ("thumb_base_flex", "Зігнути основу великого пальця"),
    ("spread", "Максимально розвести пальці"),
]


class CalibrationPage(QWidget):
    def __init__(self, controller: ApplicationController) -> None:
        super().__init__()
        self.controller = controller
        self.latest_tracking = TrackingResult(False)
        self.pose_capture_key = ""
        self.pose_capture_samples: list[dict[str, float]] = []
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 16, 20, 16)
        root.setSpacing(12)
        root.addWidget(title_label("Калібрування руки"))
        hand_card, hand_layout = card()
        hand_layout.addWidget(QLabel("Калібрування руки користувача"))
        self.video = VideoLabel()
        self.video.setMinimumSize(320, 190)
        hand_layout.addWidget(self.video, 2)
        self.pose_list = QListWidget()
        for key, text in POSES:
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, key)
            self.pose_list.addItem(item)
        self.pose_list.setCurrentRow(0)
        hand_layout.addWidget(self.pose_list, 1)
        self.detected = QLabel("Рука не знайдена")
        self.quality = QLabel("Впевненість: 0%")
        hand_layout.addWidget(self.detected)
        hand_layout.addWidget(self.quality)
        row = QHBoxLayout()
        self.capture = QPushButton("Зафіксувати позу")
        self.capture.setProperty("success", True)
        self.reset = QPushButton("Скинути калібрування")
        row.addWidget(self.capture)
        row.addWidget(self.reset)
        hand_layout.addLayout(row)
        self.summary = QLabel("Збережено поз: 0 / 9")
        hand_layout.addWidget(self.summary)
        root.addWidget(hand_card, 1)
        self.capture.clicked.connect(self.capture_pose)
        self.reset.clicked.connect(self.reset_calibration)
        controller.frame_changed.connect(self.set_frame)
        controller.tracking_changed.connect(self.set_tracking)
        self._update_summary()

    def set_language(self, language: str) -> None:
        del language

    def set_frame(self, frame) -> None:
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        image = QImage(rgb.data, width, height, channels * width, QImage.Format.Format_RGB888).copy()
        self.video.set_source_pixmap(QPixmap.fromImage(image))

    def set_tracking(self, result: TrackingResult) -> None:
        self.latest_tracking = result
        if result.detected:
            self.detected.setText(f"Руку знайдено: {result.handedness}")
            self.quality.setText(f"Впевненість: {result.confidence * 100:.0f}%")
            if self.pose_capture_key:
                values = result.calibration_values or result.raw_values
                self.pose_capture_samples.append(dict(values))
                self.capture.setText(f"Збір {len(self.pose_capture_samples)} / 12")
                if len(self.pose_capture_samples) >= 12:
                    self._finish_pose_capture()
        else:
            self.detected.setText("Рука не знайдена")
            self.quality.setText("Впевненість: 0%")

    def capture_pose(self) -> None:
        item = self.pose_list.currentItem()
        if not item or not self.latest_tracking.detected:
            self.controller.toast.emit("warning", "Спочатку запустіть камеру й утримуйте руку стабільно")
            return
        self.pose_capture_key = item.data(Qt.ItemDataRole.UserRole)
        self.pose_capture_samples = []
        self.capture.setEnabled(False)
        self.capture.setText("Утримуйте руку...")
        self.controller.toast.emit("info", "Утримуйте позу нерухомо")

    def _finish_pose_capture(self) -> None:
        values = self._median_pose_values(self.pose_capture_samples)
        if not self.pose_capture_key or not values:
            self.capture.setEnabled(True)
            self.capture.setText("Зафіксувати позу")
            self.controller.toast.emit("warning", "Не вдалося зібрати стабільну позу")
            return
        calibration = self.controller.data.setdefault("calibration", {}).setdefault("poses", {})
        calibration[self.pose_capture_key] = {
            "values": values,
            "handedness": self.latest_tracking.handedness,
            "confidence": self.latest_tracking.confidence,
        }
        self.controller.config.save()
        current = self.pose_list.currentRow()
        if current + 1 < self.pose_list.count():
            self.pose_list.setCurrentRow(current + 1)
        self._update_summary()
        self.capture.setEnabled(True)
        self.capture.setText("Зафіксувати позу")
        self.pose_capture_key = ""
        self.pose_capture_samples = []
        self.controller.toast.emit("success", "Позу зафіксовано")

    @staticmethod
    def _median_pose_values(samples: list[dict[str, float]]) -> dict[str, float]:
        if not samples:
            return {}
        keys = set().union(*(sample.keys() for sample in samples))
        return {
            key: float(median(sample[key] for sample in samples if key in sample))
            for key in keys
        }

    def reset_calibration(self) -> None:
        self.controller.data["calibration"] = {"poses": {}}
        self.controller.config.save()
        self._update_summary()

    def _update_summary(self) -> None:
        count = len(self.controller.data.get("calibration", {}).get("poses", {}))
        self.summary.setText(f"Збережено поз: {count} / {len(POSES)}")
