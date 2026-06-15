from __future__ import annotations

import cv2
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.models import AxisConfig, TrackingResult
from ye_ruka.ui.widgets.common import VideoLabel, card, subtitle_label, title_label
from ye_ruka.ui.widgets.visualizers import SignalVisualizer
from ye_ruka.vision.camera_worker import CameraScanThread


class AutomaticPage(QWidget):
    def __init__(self, controller: ApplicationController) -> None:
        super().__init__()
        self.controller = controller
        self.language = controller.data.get("language", "uk")
        self.scan_thread: CameraScanThread | None = None
        self.axes = controller.axes
        self.visualizers: dict[str, SignalVisualizer] = {}
        self.camera_running = False

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.page_scroll = QScrollArea()
        self.page_scroll.setObjectName("PageScroll")
        self.page_scroll.setWidgetResizable(True)
        self.page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.page_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        outer.addWidget(self.page_scroll)

        content = QWidget()
        content.setObjectName("AutomaticContent")
        root = QVBoxLayout(content)
        root.setContentsMargins(28, 16, 28, 16)
        root.setSpacing(10)
        self.page_scroll.setWidget(content)

        header = QHBoxLayout()
        header.setSpacing(12)
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(title_label("Камера"))
        text.addWidget(
            subtitle_label(
                "MediaPipe відстежує кисть, а Є-Рука перетворює анатомічні кути на серво-команди"
            )
        )
        header.addLayout(text, 1)
        self.start_button = QPushButton("Запустити камеру")
        self.start_button.setProperty("accent", True)
        header.addWidget(self.start_button, 0, Qt.AlignmentFlag.AlignTop)
        root.addLayout(header)

        self.body_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.body_splitter.setObjectName("CameraWorkspaceSplitter")
        self.body_splitter.setChildrenCollapsible(False)
        self.body_splitter.setHandleWidth(7)
        self.body_splitter.setMinimumHeight(330)

        video_wrap, video_layout = card(name="AmbientSurface")
        video_layout.setContentsMargins(7, 7, 7, 7)
        self.video = VideoLabel()
        self.video.setMinimumSize(430, 270)
        video_layout.addWidget(self.video, 1)
        self.body_splitter.addWidget(video_wrap)

        control = self._create_inspector()
        self.body_splitter.addWidget(control)
        self.body_splitter.setStretchFactor(0, 5)
        self.body_splitter.setStretchFactor(1, 2)
        self.body_splitter.setSizes([820, 360])
        root.addWidget(self.body_splitter, 1)

        signal_deck = QFrame()
        signal_deck.setObjectName("SignalDeck")
        signal_layout = QVBoxLayout(signal_deck)
        signal_layout.setContentsMargins(0, 0, 0, 0)
        signal_layout.setSpacing(9)

        output_header = QHBoxLayout()
        output_header.setSpacing(10)
        output_title = QLabel("VISION OUTPUT")
        output_title.setObjectName("SectionEyebrow")
        packet_label = QLabel("TX PACKET")
        packet_label.setObjectName("MicroText")
        self.packet = QLineEdit()
        self.packet.setReadOnly(True)
        self.packet.setPlaceholderText("Serial-пакет")
        self.packet.setObjectName("PacketField")
        self.packet.setMinimumWidth(300)
        output_header.addWidget(output_title)
        output_header.addStretch(1)
        output_header.addWidget(packet_label)
        output_header.addWidget(self.packet, 1)
        signal_layout.addLayout(output_header)

        self.meter_scroll = QScrollArea()
        self.meter_scroll.setObjectName("MeterScroll")
        self.meter_scroll.setWidgetResizable(True)
        self.meter_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.meter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.meter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.meter_scroll.setMinimumHeight(150)
        self.meter_scroll.setMaximumHeight(178)
        self.meter_container = QWidget()
        self.meter_container.setObjectName("MeterContainer")
        self.meter_row = QHBoxLayout(self.meter_container)
        self.meter_row.setContentsMargins(0, 0, 0, 0)
        self.meter_row.setSpacing(8)
        self.meter_scroll.setWidget(self.meter_container)
        signal_layout.addWidget(self.meter_scroll)
        root.addWidget(signal_deck)

        self.start_button.clicked.connect(self._toggle_camera)
        self.refresh_cameras.clicked.connect(self.scan_cameras)
        controller.frame_changed.connect(self.set_frame)
        controller.tracking_changed.connect(self.set_tracking)
        controller.packet_changed.connect(self.packet.setText)
        controller.axes_changed.connect(self.set_axes)
        controller.camera_state_changed.connect(self._camera_state_changed)
        controller.diagnostics_changed.connect(self._metrics)
        self.set_axes(self.axes)
        self.scan_cameras()
        QTimer.singleShot(0, self._sync_body_height)

    def _create_inspector(self) -> QFrame:
        control, control_layout = card(name="ControlColumn")
        control.setMinimumWidth(330)
        control.setMaximumWidth(440)
        control.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        control_layout.setContentsMargins(16, 15, 10, 15)
        control_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setObjectName("InspectorScroll")
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        panel = QWidget()
        panel.setObjectName("InspectorContent")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(2, 0, 6, 0)
        layout.setSpacing(10)

        eyebrow = QLabel("VISION INPUT")
        eyebrow.setObjectName("SectionEyebrow")
        layout.addWidget(eyebrow)

        self.camera_combo = QComboBox()
        self.camera_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.camera_combo.setMinimumContentsLength(18)
        self.refresh_cameras = QPushButton("Оновити список камер")
        self.refresh_cameras.setObjectName("SoftButton")

        self.resolution = QComboBox()
        self.resolution.addItems(["640×480", "1280×720", "1920×1080"])
        current = self.controller.data["camera"]
        self.resolution.setCurrentText(f"{current.get('width', 1280)}×{current.get('height', 720)}")

        self.fps = QSpinBox()
        self.fps.setRange(5, 120)
        self.fps.setValue(int(current.get("fps", 30)))
        self.fps.setSuffix(" FPS")

        self.hand = QComboBox()
        self.hand.addItem("Автоматично", "auto")
        self.hand.addItem("Ліва", "left")
        self.hand.addItem("Права", "right")
        self.hand.setCurrentIndex(max(0, self.hand.findData(current.get("hand_preference", "auto"))))

        self.mirror = QCheckBox("Дзеркальне відображення")
        self.mirror.setChecked(bool(current.get("mirror", True)))

        layout.addWidget(self._field("Камера", self.camera_combo))
        pair = QHBoxLayout()
        pair.setSpacing(9)
        pair.addWidget(self._field("Роздільна здатність", self.resolution), 1)
        pair.addWidget(self._field("Частота", self.fps), 1)
        layout.addLayout(pair)

        hand_row = QHBoxLayout()
        hand_row.setSpacing(9)
        hand_row.addWidget(self._field("Рука", self.hand), 1)
        mirror_wrap = QWidget()
        mirror_layout = QVBoxLayout(mirror_wrap)
        mirror_layout.setContentsMargins(0, 17, 0, 0)
        mirror_layout.addWidget(self.mirror)
        hand_row.addWidget(mirror_wrap, 1)
        layout.addLayout(hand_row)
        layout.addWidget(self.refresh_cameras)

        separator = QFrame()
        separator.setObjectName("InspectorDivider")
        separator.setFixedHeight(1)
        layout.addSpacing(2)
        layout.addWidget(separator)
        layout.addSpacing(2)

        tracking_header = QHBoxLayout()
        tracking_title = QLabel("TRACKING")
        tracking_title.setObjectName("SectionEyebrow")
        self.state_label = QLabel("WAITING")
        self.state_label.setObjectName("TrackingState")
        self.state_label.setProperty("tracking", "idle")
        tracking_header.addWidget(tracking_title)
        tracking_header.addStretch(1)
        tracking_header.addWidget(self.state_label)
        layout.addLayout(tracking_header)

        metrics = QGridLayout()
        metrics.setContentsMargins(0, 0, 0, 0)
        metrics.setHorizontalSpacing(14)
        metrics.setVerticalSpacing(4)
        self.hand_caption = QLabel("РУКА")
        self.fps_caption = QLabel("FPS")
        self.processing_caption = QLabel("ОБРОБКА")
        for column, caption in enumerate((self.hand_caption, self.fps_caption, self.processing_caption)):
            caption.setObjectName("MicroText")
            metrics.addWidget(caption, 0, column)

        self.hand_label = QLabel("—")
        self.hand_label.setObjectName("MetricValueSmall")
        self.fps_label = QLabel("0.0")
        self.fps_label.setObjectName("MetricValueSmall")
        self.processing_label = QLabel("0.0 мс")
        self.processing_label.setObjectName("MetricValueSmall")
        metrics.addWidget(self.hand_label, 1, 0)
        metrics.addWidget(self.fps_label, 1, 1)
        metrics.addWidget(self.processing_label, 1, 2)
        metrics.setColumnStretch(0, 1)
        metrics.setColumnStretch(1, 1)
        metrics.setColumnStretch(2, 1)
        layout.addLayout(metrics)

        confidence_row = QHBoxLayout()
        self.confidence_caption = QLabel("ВПЕВНЕНІСТЬ")
        self.confidence_caption.setObjectName("MicroText")
        self.confidence_label = QLabel("0%")
        self.confidence_label.setObjectName("MetricValueSmall")
        confidence_row.addWidget(self.confidence_caption)
        confidence_row.addStretch(1)
        confidence_row.addWidget(self.confidence_label)
        layout.addLayout(confidence_row)

        self.confidence_bar = QProgressBar()
        self.confidence_bar.setObjectName("ConfidenceBar")
        self.confidence_bar.setRange(0, 100)
        self.confidence_bar.setValue(0)
        self.confidence_bar.setTextVisible(False)
        self.confidence_bar.setFixedHeight(7)
        layout.addWidget(self.confidence_bar)
        layout.addStretch(1)

        scroll.setWidget(panel)
        control_layout.addWidget(scroll)
        return control

    @staticmethod
    def _field(caption: str, widget: QWidget) -> QWidget:
        wrapper = QWidget()
        wrapper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        field_layout = QVBoxLayout(wrapper)
        field_layout.setContentsMargins(0, 0, 0, 0)
        field_layout.setSpacing(4)
        label = QLabel(caption.upper())
        label.setObjectName("MicroText")
        field_layout.addWidget(label)
        field_layout.addWidget(widget)
        return wrapper

    def scan_cameras(self) -> None:
        if self.scan_thread and self.scan_thread.isRunning():
            return
        self.refresh_cameras.setEnabled(False)
        self.camera_combo.clear()
        self.camera_combo.addItem("Сканування…", 0)
        self.scan_thread = CameraScanThread()
        self.scan_thread.completed.connect(self._cameras_found)
        self.scan_thread.finished.connect(lambda: self.refresh_cameras.setEnabled(True))
        self.scan_thread.start()

    def _cameras_found(self, cameras: list[dict[str, object]]) -> None:
        self.camera_combo.clear()
        if not cameras:
            self.camera_combo.addItem("Камери не знайдено", 0)
            return
        configured = int(self.controller.data["camera"].get("index", 0))
        for camera in cameras:
            self.camera_combo.addItem(
                f"{camera['index']}  ·  {camera['name']}  ·  {camera['resolution']}", camera["index"]
            )
        index = self.camera_combo.findData(configured)
        self.camera_combo.setCurrentIndex(max(0, index))

    def _start(self) -> None:
        width, height = [int(part) for part in self.resolution.currentText().split("×")]
        camera = self.controller.data["camera"]
        camera.update(
            {
                "index": int(self.camera_combo.currentData() or 0),
                "width": width,
                "height": height,
                "fps": self.fps.value(),
                "mirror": self.mirror.isChecked(),
                "hand_preference": self.hand.currentData(),
            }
        )
        self.controller.config.save()
        self.controller.set_mode("automatic")
        self.controller.start_camera()

    def _toggle_camera(self) -> None:
        if self.camera_running:
            self.controller.stop_camera()
            return
        self._set_camera_running(True)
        self._start()

    def _camera_state_changed(self, state: str) -> None:
        self._set_camera_running(state == "running")

    def _set_camera_running(self, running: bool) -> None:
        self.camera_running = running
        self.start_button.setText(self._camera_button_text())
        self.start_button.setProperty("accent", not running)
        self.start_button.style().unpolish(self.start_button)
        self.start_button.style().polish(self.start_button)

    def _camera_button_text(self) -> str:
        if self.language == "en":
            return "Stop camera" if self.camera_running else "Start camera"
        return "Зупинити камеру" if self.camera_running else "Запустити камеру"

    def set_frame(self, frame) -> None:
        if frame is None:
            return
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = rgb.shape
        image = QImage(rgb.data, width, height, channels * width, QImage.Format.Format_RGB888).copy()
        self.video.set_source_pixmap(QPixmap.fromImage(image))

    def set_tracking(self, result: TrackingResult) -> None:
        if not result.detected:
            self._set_tracking_state("LOST", "lost")
            self.hand_label.setText("Не знайдено" if self.language == "uk" else "Not found")
            self.confidence_label.setText("0%")
            self.confidence_bar.setValue(0)
            for meter in self.visualizers.values():
                meter.set_value(0.0, 0.0)
            return

        self._set_tracking_state("TRACKING", "active")
        names_uk = {"left": "Ліва", "right": "Права"}
        names_en = {"left": "Left", "right": "Right"}
        names = names_en if self.language == "en" else names_uk
        self.hand_label.setText(names.get(result.handedness, result.handedness))
        confidence = round(result.confidence * 100)
        self.confidence_label.setText(f"{confidence}%")
        self.confidence_bar.setValue(confidence)
        for axis in self.axes:
            normalized = result.raw_values.get(axis.source, 0.0)
            meter = self.visualizers.get(axis.id)
            if meter:
                meter.set_value(normalized, normalized)

    def _set_tracking_state(self, text: str, state: str) -> None:
        self.state_label.setText(text)
        self.state_label.setProperty("tracking", state)
        self.state_label.style().unpolish(self.state_label)
        self.state_label.style().polish(self.state_label)

    def set_axes(self, axes: list[AxisConfig]) -> None:
        self.axes = axes
        while self.meter_row.count():
            item = self.meter_row.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.visualizers.clear()
        language = self.controller.data.get("language", "uk")
        for axis in axes:
            meter = SignalVisualizer(axis.name(language).split(":")[0], axis.channel, compact=True)
            self.meter_row.addWidget(meter, 1)
            self.visualizers[axis.id] = meter
        self.meter_row.addStretch(1)

    def set_language(self, language: str) -> None:
        self.language = language
        self.start_button.setText(self._camera_button_text())
        self.hand_caption.setText("HAND" if language == "en" else "РУКА")
        self.fps_caption.setText("FPS")
        self.processing_caption.setText("PROCESSING" if language == "en" else "ОБРОБКА")
        self.confidence_caption.setText("CONFIDENCE" if language == "en" else "ВПЕВНЕНІСТЬ")
        for axis in self.axes:
            meter = self.visualizers.get(axis.id)
            if meter:
                meter.label = axis.name(language).split(":")[0]
                meter.update()

    def _metrics(self, snapshot) -> None:
        self.fps_label.setText(f"{snapshot.camera_fps:.1f}")
        suffix = " ms" if self.language == "en" else " мс"
        self.processing_label.setText(f"{snapshot.processing_ms:.1f}{suffix}")

    def _sync_body_height(self) -> None:
        body_height = max(330, min(540, self.height() - 311))
        self.body_splitter.setMaximumHeight(body_height)
        self.body_splitter.updateGeometry()

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._sync_body_height()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        QTimer.singleShot(0, self._sync_body_height)

    def shutdown(self) -> None:
        if self.scan_thread and self.scan_thread.isRunning():
            self.scan_thread.stop()
