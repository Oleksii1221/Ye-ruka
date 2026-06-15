from __future__ import annotations

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListView,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ye_ruka.core.controller import ApplicationController
from ye_ruka.core.models import AxisConfig, Gesture
from ye_ruka.ui.widgets.common import AxisRow, card, subtitle_label, title_label


class ManualPage(QWidget):
    def __init__(self, controller: ApplicationController) -> None:
        super().__init__()
        self.controller = controller
        self.rows: dict[str, AxisRow] = {}
        self.gestures: list[Gesture] = []
        self.shortcuts: list[QShortcut] = []
        self.language = "uk"
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(15)

        header = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(2)
        text.addWidget(title_label("Ручне керування"))
        text.addWidget(subtitle_label("Точне керування кожною віссю та швидкий запуск жестів"))
        header.addLayout(text)
        header.addStretch(1)
        self.live_value = QLabel("0°")
        self.live_value.setObjectName("HeroNumber")
        header.addWidget(self.live_value)
        root.addLayout(header)

        grip, grip_layout = card(name="GlassStrip")
        grip_layout.setContentsMargins(18, 12, 18, 12)
        grip_row = QHBoxLayout()
        grip_text = QVBoxLayout()
        grip_text.setSpacing(0)
        grip_title = QLabel("MASTER GRIP")
        grip_title.setObjectName("SectionEyebrow")
        grip_hint = QLabel("Одночасне стискання всіх осей, включених у загальний хват")
        grip_hint.setObjectName("MicroText")
        grip_text.addWidget(grip_title)
        grip_text.addWidget(grip_hint)
        self.grip = QSlider(Qt.Orientation.Horizontal)
        self.grip.setRange(0, 100)
        self.grip.setMinimumWidth(360)
        self.grip_value = QLabel("0%")
        self.grip_value.setObjectName("MetricValueSmall")
        grip_row.addLayout(grip_text)
        grip_row.addSpacing(24)
        grip_row.addWidget(self.grip, 1)
        grip_row.addWidget(self.grip_value)
        grip_layout.addLayout(grip_row)
        root.addWidget(grip)

        axis_header = QHBoxLayout()
        axis_label = QLabel("AXIS CONTROL")
        axis_label.setObjectName("SectionEyebrow")
        axis_note = QLabel("Зміни передаються через спільний безпечний pipeline")
        axis_note.setObjectName("MicroText")
        axis_header.addWidget(axis_label)
        axis_header.addStretch(1)
        axis_header.addWidget(axis_note)
        root.addLayout(axis_header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setObjectName("AxisScroll")
        self.axis_container = QWidget()
        self.axis_layout = QVBoxLayout(self.axis_container)
        self.axis_layout.setContentsMargins(0, 0, 0, 0)
        self.axis_layout.setSpacing(4)
        self.axis_layout.addStretch(1)
        self.scroll.setWidget(self.axis_container)
        root.addWidget(self.scroll, 1)

        gesture_deck = QWidget()
        gesture_layout = QVBoxLayout(gesture_deck)
        gesture_layout.setContentsMargins(0, 0, 0, 0)
        gesture_layout.setSpacing(8)
        gesture_header = QHBoxLayout()
        gesture_title = QLabel("GESTURES")
        gesture_title.setObjectName("SectionEyebrow")
        self.apply_button = QPushButton("Застосувати")
        self.apply_button.setProperty("accent", True)
        self.rename_button = QPushButton("Перейменувати")
        self.delete_button = QPushButton("Видалити")
        gesture_header.addWidget(gesture_title)
        gesture_header.addStretch(1)
        gesture_header.addWidget(self.apply_button)
        gesture_header.addWidget(self.rename_button)
        gesture_header.addWidget(self.delete_button)
        gesture_layout.addLayout(gesture_header)
        self.gesture_list = QListWidget()
        self.gesture_list.setObjectName("GestureRibbon")
        self.gesture_list.setFlow(QListView.Flow.LeftToRight)
        self.gesture_list.setWrapping(False)
        self.gesture_list.setResizeMode(QListView.ResizeMode.Adjust)
        self.gesture_list.setMovement(QListView.Movement.Static)
        self.gesture_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.gesture_list.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.gesture_list.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.gesture_list.setFixedHeight(76)
        gesture_layout.addWidget(self.gesture_list)

        create, create_layout = card(name="GlassStrip")
        create_layout.setContentsMargins(12, 9, 12, 9)
        create_row = QHBoxLayout()
        self.name = QLineEdit()
        self.name.setPlaceholderText("Назва нового жесту")
        self.duration = QSpinBox()
        self.duration.setRange(50, 10000)
        self.duration.setValue(700)
        self.duration.setSuffix(" мс")
        self.hotkey = QLineEdit()
        self.hotkey.setPlaceholderText("Ctrl+1")
        self.save_button = QPushButton("Зберегти поточне положення")
        create_row.addWidget(self.name, 2)
        create_row.addWidget(QLabel("Перехід"))
        create_row.addWidget(self.duration)
        create_row.addWidget(QLabel("Hotkey"))
        create_row.addWidget(self.hotkey)
        create_row.addWidget(self.save_button)
        create_layout.addLayout(create_row)
        gesture_layout.addWidget(create)
        root.addWidget(gesture_deck)

        self.grip.valueChanged.connect(self._grip_changed)
        self.apply_button.clicked.connect(self._apply)
        self.save_button.clicked.connect(self._save)
        self.delete_button.clicked.connect(self._delete)
        self.rename_button.clicked.connect(self._rename)
        self.gesture_list.itemDoubleClicked.connect(lambda _: self._apply())
        controller.axes_changed.connect(self.rebuild_axes)
        controller.values_changed.connect(self.set_values)
        controller.gestures_changed.connect(self.set_gestures)
        self.rebuild_axes(controller.axes)
        self.set_gestures(controller.all_gestures())

    def showEvent(self, event) -> None:
        self.controller.set_mode("manual")
        super().showEvent(event)

    def rebuild_axes(self, axes: list[AxisConfig]) -> None:
        while self.axis_layout.count() > 1:
            item = self.axis_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        self.rows.clear()
        for axis in axes:
            if not axis.enabled:
                continue
            row = AxisRow(axis, self.language)
            row.value_changed.connect(self.controller.set_manual_value)
            row.enabled_changed.connect(self._enabled_changed)
            self.axis_layout.insertWidget(self.axis_layout.count() - 1, row)
            self.rows[axis.id] = row

    def set_values(self, values: dict[str, int]) -> None:
        for axis_id, value in values.items():
            row = self.rows.get(axis_id)
            if row:
                row.set_value(value)
        if values:
            self.live_value.setText(f"{sum(values.values()) / len(values):.0f}° AVG")

    def set_gestures(self, gestures: list[Gesture]) -> None:
        self.gestures = gestures
        for shortcut in self.shortcuts:
            shortcut.deleteLater()
        self.shortcuts.clear()
        self.gesture_list.clear()
        names_en = {
            "Розжим": "Open hand",
            "Зжим": "Fist",
            "Нейтраль": "Neutral",
            "Щипкове захоплення": "Pinch grip",
            "OK": "OK",
            "Вказівний жест": "Pointing",
            "V": "V sign",
            "Лайк": "Thumbs up",
            "Коза": "Horns",
            "Шака": "Shaka",
        }
        for index, gesture in enumerate(gestures):
            name = names_en.get(gesture.name, gesture.name) if self.language == "en" else gesture.name
            item = QListWidgetItem(name)
            item.setSizeHint(QSize(max(118, len(name) * 9 + 38), 50))
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setToolTip(("Built-in" if self.language == "en" else "Вбудований") if gesture.builtin else gesture.hotkey)
            self.gesture_list.addItem(item)
            if gesture.hotkey:
                shortcut = QShortcut(QKeySequence(gesture.hotkey), self)
                shortcut.activated.connect(lambda selected=gesture: self.controller.apply_gesture(selected))
                self.shortcuts.append(shortcut)
        if self.gesture_list.count():
            self.gesture_list.setCurrentRow(0)

    def set_language(self, language: str) -> None:
        self.language = language
        for axis in self.controller.axes:
            row = self.rows.get(axis.id)
            if row:
                row.name.setText(axis.name(language))
        self.set_gestures(self.gestures)

    def _selected(self) -> Gesture | None:
        item = self.gesture_list.currentItem()
        if not item:
            return None
        index = item.data(Qt.ItemDataRole.UserRole)
        return self.gestures[index] if isinstance(index, int) and 0 <= index < len(self.gestures) else None

    def _grip_changed(self, value: int) -> None:
        self.grip_value.setText(f"{value}%")
        self.controller.set_grip(value)

    def _apply(self) -> None:
        gesture = self._selected()
        if gesture:
            self.controller.apply_gesture(gesture)

    def _save(self) -> None:
        name = self.name.text().strip()
        if not name:
            return
        self.controller.save_gesture(name, self.duration.value(), self.hotkey.text().strip())
        self.name.clear()

    def _delete(self) -> None:
        gesture = self._selected()
        if gesture and not gesture.builtin:
            self.controller.delete_gesture(gesture.name)

    def _rename(self) -> None:
        gesture = self._selected()
        if not gesture or gesture.builtin:
            return
        new_name, ok = QInputDialog.getText(self, "Перейменування", "Нова назва", text=gesture.name)
        if ok and new_name.strip():
            self.controller.rename_gesture(gesture.name, new_name.strip())

    def _enabled_changed(self, axis_id: str, enabled: bool) -> None:
        axes = self.controller.axes
        for axis in axes:
            if axis.id == axis_id:
                axis.enabled = enabled
        self.controller.update_axes(axes)
