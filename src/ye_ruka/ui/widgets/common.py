from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QMouseEvent, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ye_ruka.core.models import AxisConfig


def card(parent: QWidget | None = None, *, name: str = "Surface") -> tuple[QFrame, QVBoxLayout]:
    frame = QFrame(parent)
    frame.setObjectName(name)
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(18, 16, 18, 16)
    layout.setSpacing(10)
    return frame, layout


def title_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("PageTitle")
    return label


def subtitle_label(text: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName("PageSubtitle")
    label.setWordWrap(True)
    return label


class VideoLabel(QLabel):
    def __init__(self) -> None:
        super().__init__("Камеру не запущено")
        self.setObjectName("VideoFrame")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumSize(480, 320)
        self.setScaledContents(False)
        self._source: QPixmap | None = None

    def set_source_pixmap(self, pixmap: QPixmap) -> None:
        self._source = pixmap
        self._rescale()

    def clear_source(self, text: str = "Камеру не запущено") -> None:
        self._source = None
        self.clear()
        self.setText(text)

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._rescale()

    def _rescale(self) -> None:
        if self._source is None or self._source.isNull():
            return
        self.setPixmap(
            self._source.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )


class AxisRow(QFrame):
    value_changed = Signal(str, int)
    enabled_changed = Signal(str, bool)

    def __init__(self, axis: AxisConfig, language: str = "uk") -> None:
        super().__init__()
        self.axis = axis
        self.setObjectName("AxisRow")
        self.setMinimumHeight(58)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(10)
        self.enabled = QCheckBox()
        self.enabled.setChecked(axis.enabled)
        text = QVBoxLayout()
        text.setSpacing(0)
        self.name = QLabel(axis.name(language))
        self.name.setObjectName("AxisName")
        self.meta = QLabel(f"CH {axis.channel + 1}  •  SERVO {axis.servo + 1}")
        self.meta.setObjectName("MicroText")
        text.addWidget(self.name)
        text.addWidget(self.meta)
        text_widget = QWidget()
        text_widget.setLayout(text)
        text_widget.setMinimumWidth(190)
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setRange(min(axis.min_angle, axis.max_angle), max(axis.min_angle, axis.max_angle))
        self.slider.setValue(axis.neutral_angle)
        self.spin = QSpinBox()
        self.spin.setRange(min(axis.min_angle, axis.max_angle), max(axis.min_angle, axis.max_angle))
        self.spin.setValue(axis.neutral_angle)
        self.spin.setSuffix("°")
        self.spin.setObjectName("AngleSpin")
        self.neutral = QPushButton("N")
        self.neutral.setObjectName("RoundButton")
        self.neutral.setFixedSize(34, 34)
        self.neutral.setToolTip("Нейтральне положення")
        self.inversion = QLabel("↔" if axis.inverted else "→")
        self.inversion.setObjectName("DirectionBadge")
        self.inversion.setToolTip("Інверсія ввімкнена" if axis.inverted else "Звичайний напрямок")
        layout.addWidget(self.enabled)
        layout.addWidget(text_widget)
        layout.addWidget(self.slider, 1)
        layout.addWidget(self.spin)
        layout.addWidget(self.neutral)
        layout.addWidget(self.inversion)
        self.slider.valueChanged.connect(self.spin.setValue)
        self.spin.valueChanged.connect(self.slider.setValue)
        self.slider.valueChanged.connect(lambda value: self.value_changed.emit(axis.id, value))
        self.enabled.toggled.connect(lambda value: self.enabled_changed.emit(axis.id, value))
        self.neutral.clicked.connect(lambda: self.slider.setValue(axis.neutral_angle))

    def set_value(self, value: int) -> None:
        self.slider.blockSignals(True)
        self.spin.blockSignals(True)
        self.slider.setValue(value)
        self.spin.setValue(value)
        self.slider.blockSignals(False)
        self.spin.blockSignals(False)


class TitleBar(QFrame):
    minimize_clicked = Signal()
    maximize_clicked = Signal()
    fullscreen_clicked = Signal()
    close_clicked = Signal()
    double_clicked = Signal()

    def __init__(self, logo: QPixmap | None = None) -> None:
        super().__init__()
        self.setObjectName("TitleBar")
        self.setFixedHeight(58)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 0, 4, 0)
        layout.setSpacing(11)
        self.icon = QLabel()
        self.icon.setObjectName("AppIcon")
        if logo is not None:
            self.icon.setPixmap(
                logo.scaled(32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            )
        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self.title = QLabel("Є-Рука")
        self.title.setObjectName("WindowTitle")
        self.subtitle = QLabel("ROBOTIC HAND CONTROL STUDIO")
        self.subtitle.setObjectName("WindowSubtitle")
        title_box.addWidget(self.title)
        title_box.addWidget(self.subtitle)
        title_widget = QWidget()
        title_widget.setLayout(title_box)
        self.profile = QLabel("DEFAULT PROFILE")
        self.profile.setObjectName("ProfileChip")
        self.min_button = QPushButton("—")
        self.max_button = QPushButton("□")
        self.fullscreen_button = QPushButton("⛶")
        self.close_button = QPushButton("×")
        for button in (self.min_button, self.max_button, self.fullscreen_button, self.close_button):
            button.setObjectName("WindowButton")
            button.setFixedSize(46, 38)
        self.fullscreen_button.setToolTip("Повноекранний режим")
        self.close_button.setObjectName("WindowCloseButton")
        layout.addWidget(self.icon)
        layout.addWidget(title_widget)
        layout.addSpacing(14)
        layout.addWidget(self.profile)
        layout.addStretch(1)
        layout.addWidget(self.min_button)
        layout.addWidget(self.max_button)
        layout.addWidget(self.fullscreen_button)
        layout.addWidget(self.close_button)
        self.min_button.clicked.connect(self.minimize_clicked)
        self.max_button.clicked.connect(self.maximize_clicked)
        self.fullscreen_button.clicked.connect(self.fullscreen_clicked)
        self.close_button.clicked.connect(self.close_clicked)

    def set_profile(self, text: str) -> None:
        self.profile.setText(text.upper())

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            window = self.window().windowHandle()
            if window:
                window.startSystemMove()
        super().mousePressEvent(event)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit()
        super().mouseDoubleClickEvent(event)
