from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication, QComboBox, QDoubleSpinBox, QScrollArea, QSpinBox

from ye_ruka.core.models import AxisConfig
from ye_ruka.ui.pages.automatic import AutomaticPage
from ye_ruka.ui.pages.settings import FIELD_MIN_HEIGHT, TABLE_ROW_HEIGHT, SettingsPage
from ye_ruka.ui.pages.service import ServicePage
from ye_ruka.ui.widgets.visualizers import SignalVisualizer


class _Config:
    def save(self) -> None:
        return None


class _Controller(QObject):
    frame_changed = Signal(object)
    tracking_changed = Signal(object)
    packet_changed = Signal(str)
    axes_changed = Signal(list)
    camera_state_changed = Signal(str)
    diagnostics_changed = Signal(object)

    def __init__(self) -> None:
        super().__init__()
        self.axes = [
            AxisConfig(
                id=f"axis_{index}",
                name_uk=f"Вісь {index}",
                name_en=f"Axis {index}",
                channel=index,
                servo=index,
                source=f"axis_{index}",
            )
            for index in range(6)
        ]
        self.data = {
            "language": "uk",
            "camera": {
                "index": 0,
                "width": 1280,
                "height": 720,
                "fps": 30,
                "mirror": True,
                "hand_preference": "auto",
            },
            "serial": {
                "port": "",
                "baudrate": 115200,
                "protocol": "extended",
                "send_rate_hz": 60,
                "auto_reconnect": True,
                "ack_enabled": False,
            },
            "glove": {
                "port": "",
                "baudrate": 115200,
                "format": "auto",
                "channel_count": 6,
                "auto_reconnect": True,
                "input_min": 0.0,
                "input_max": 4095.0,
                "smoothing": 0.22,
            },
            "tracking": {
                "lost_hand_policy": "safe",
                "lost_hand_timeout_ms": 700,
                "draw_landmarks": True,
            },
            "safety": {
                "smooth_transition_ms": 800,
                "require_verified_profile": True,
                "serial_timeout_ms": 1000,
            },
        }
        self.config = _Config()

    def stop_camera(self) -> None:
        return None

    def set_mode(self, mode: str) -> None:
        return None

    def start_camera(self) -> None:
        return None

    def update_axes(self, axes: list[AxisConfig]) -> None:
        self.axes = axes

    def update_serial_config(self) -> None:
        return None

    def update_glove_config(self) -> None:
        return None


APP = QApplication.instance() or QApplication([])


def test_compact_visualizer_fits_automatic_output_strip() -> None:
    widget = SignalVisualizer("Вказівний", 2, compact=True)
    assert widget.minimumHeight() <= 150
    assert widget.minimumWidth() <= 100
    widget.resize(110, 150)
    image = QImage(widget.size(), QImage.Format.Format_ARGB32)
    image.fill(0)
    widget.render(image)
    assert not image.isNull()


def test_automatic_page_uses_scrollable_inspector_without_squeezing(monkeypatch) -> None:
    app = APP
    monkeypatch.setattr(AutomaticPage, "scan_cameras", lambda self: None)
    page = AutomaticPage(_Controller())
    page.resize(1420, 711)
    page.show()
    app.processEvents()

    inspector = page.findChild(QScrollArea, "InspectorScroll")
    assert inspector is not None
    assert inspector.widgetResizable()
    assert page.confidence_bar.height() > 0
    assert page.camera_combo.height() > 0
    assert page.hand.height() > 0
    assert len(page.visualizers) == 6
    assert all(item.minimumHeight() <= page.meter_scroll.maximumHeight() for item in page.visualizers.values())
    assert page.page_scroll.verticalScrollBar().maximum() == 0

    page.close()


def test_settings_fields_keep_readable_height(monkeypatch) -> None:
    monkeypatch.setattr("ye_ruka.ui.pages.settings.list_ports.comports", lambda: [])
    page = SettingsPage(_Controller())
    page.resize(1120, 720)
    page.show()
    APP.processEvents()

    fields = []
    for widget_type in (QComboBox, QSpinBox, QDoubleSpinBox):
        fields.extend(page.findChildren(widget_type))
    assert fields
    assert all(field.minimumHeight() >= FIELD_MIN_HEIGHT for field in fields)
    assert all(page.glove_mapping.rowHeight(row) >= TABLE_ROW_HEIGHT for row in range(page.glove_mapping.rowCount()))

    page.close()


def test_service_page_exposes_flash_and_single_servo_controls(monkeypatch) -> None:
    monkeypatch.setattr("ye_ruka.ui.pages.service.list_ports.comports", lambda: [])
    page = ServicePage(_Controller())
    page.resize(1120, 720)
    page.show()
    APP.processEvents()

    assert page.production_button.isVisible()
    assert page.calibration_button.isVisible()
    assert page.servo.count() == 7
    assert page.angle_spin.minimum() == -90
    assert page.angle_spin.maximum() == 90
    assert not page.test_disconnect.isEnabled()
    assert not page.move_button.isEnabled()

    page.shutdown()
    page.close()
