from __future__ import annotations

import math
from collections import deque

from PySide6.QtCore import QPointF, QRectF, QTimer, Qt
from PySide6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QWidget


class SignalVisualizer(QWidget):
    def __init__(self, label: str, channel: int, *, compact: bool = False) -> None:
        super().__init__()
        self.label = label
        self.channel = channel
        self.compact = compact
        self.value = 0.0
        self.raw = 0.0
        history_size = 28 if compact else 36
        self.history: deque[float] = deque([0.0] * history_size, maxlen=history_size)
        if compact:
            self.setMinimumSize(96, 142)
            self.setMaximumWidth(150)
        else:
            self.setMinimumSize(86, 250)

    def set_value(self, raw: float, normalized: float) -> None:
        self.raw = raw
        self.value = max(0.0, min(1.0, normalized))
        self.history.append(self.value)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        inset = 5 if self.compact else 7
        rect = QRectF(self.rect()).adjusted(inset, inset, -inset, -inset)
        if rect.width() <= 0 or rect.height() <= 0:
            return

        text = self.palette().text().color()
        muted = self.palette().placeholderText().color()
        accent = self.palette().highlight().color()
        link = self.palette().link().color()

        channel_height = 15 if self.compact else 18
        value_top = rect.top() + channel_height
        value_height = 25 if self.compact else 30
        label_height = 18
        spark_height = 15 if self.compact else 24
        spark_gap = 5
        meter_top = value_top + value_height + (5 if self.compact else 8)
        label_top = rect.bottom() - label_height
        spark_top = label_top - spark_gap - spark_height
        meter_bottom = spark_top - (6 if self.compact else 9)
        meter_margin = max(12.0, rect.width() * (0.24 if self.compact else 0.20))
        meter = QRectF(
            rect.left() + meter_margin,
            meter_top,
            max(8.0, rect.width() - meter_margin * 2),
            max(20.0, meter_bottom - meter_top),
        )

        painter.setPen(muted)
        font = self.font()
        font.setPointSizeF(7.2 if self.compact else 7.8)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(
            QRectF(rect.left(), rect.top(), rect.width(), channel_height),
            Qt.AlignmentFlag.AlignCenter,
            f"CH {self.channel}",
        )

        value_font = self.font()
        value_font.setPointSizeF(12.5 if self.compact else 14)
        value_font.setWeight(QFont.Weight.Bold)
        painter.setFont(value_font)
        painter.setPen(text)
        painter.drawText(
            QRectF(rect.left(), value_top, rect.width(), value_height),
            Qt.AlignmentFlag.AlignCenter,
            f"{self.value * 100:02.0f}%",
        )

        segments = 12 if self.compact else 18
        gap = 2.0 if self.compact else 3.0
        segment_h = max(1.4, (meter.height() - gap * (segments - 1)) / segments)
        active = int(round(self.value * segments))
        for index in range(segments):
            y = meter.bottom() - (index + 1) * segment_h - index * gap
            segment = QRectF(meter.left(), y, meter.width(), segment_h)
            if index < active:
                t = index / max(1, segments - 1)
                color = QColor(
                    int(accent.red() * (1 - t) + link.red() * t),
                    int(accent.green() * (1 - t) + link.green() * t),
                    int(accent.blue() * (1 - t) + link.blue() * t),
                )
                painter.setBrush(color)
            else:
                off = QColor(text)
                off.setAlpha(18)
                painter.setBrush(off)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(segment, 2.4, 2.4)

        spark = QRectF(rect.left() + 2, spark_top, rect.width() - 4, spark_height)
        path = QPainterPath()
        values = list(self.history)
        for index, value in enumerate(values):
            x = spark.left() + index * spark.width() / max(1, len(values) - 1)
            y = spark.bottom() - value * spark.height()
            if index == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        painter.setPen(QPen(link, 1.2 if self.compact else 1.4))
        painter.drawPath(path)

        label_font = self.font()
        label_font.setPointSizeF(7.6 if self.compact else 8.2)
        label_font.setWeight(QFont.Weight.Medium)
        painter.setFont(label_font)
        painter.setPen(text)
        painter.drawText(
            QRectF(rect.left() - 3, label_top, rect.width() + 6, label_height),
            Qt.AlignmentFlag.AlignCenter,
            self.label,
        )


class HandTelemetryWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.values = [0.0] * 6
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(32)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self.setMinimumSize(320, 360)

    def set_values(self, values: list[float]) -> None:
        self.values = list(values[:6]) + [0.0] * max(0, 6 - len(values))
        self.update()

    def _tick(self) -> None:
        self.phase = (self.phase + 0.035) % (math.pi * 2)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(24, 20, -24, -20)
        accent = self.palette().highlight().color()
        link = self.palette().link().color()
        text = self.palette().text().color()
        glow = QColor(accent)
        glow.setAlpha(18 + int(8 * (1 + math.sin(self.phase))))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(rect.center(), min(rect.width(), rect.height()) * 0.42, min(rect.width(), rect.height()) * 0.42)
        center = QPointF(rect.center().x(), rect.bottom() - 76)
        palm_w = min(126.0, rect.width() * 0.38)
        palm_h = min(142.0, rect.height() * 0.38)
        palm = QRectF(center.x() - palm_w / 2, center.y() - palm_h, palm_w, palm_h)
        surface = QColor(text)
        surface.setAlpha(12)
        painter.setBrush(surface)
        edge = QColor(accent)
        edge.setAlpha(150)
        painter.setPen(QPen(edge, 2.0))
        painter.drawRoundedRect(palm, 34, 34)
        finger_bases = [
            QPointF(palm.left() + 18, palm.top() + 13),
            QPointF(palm.left() + 43, palm.top() + 2),
            QPointF(palm.center().x(), palm.top() - 2),
            QPointF(palm.right() - 43, palm.top() + 3),
            QPointF(palm.right() - 18, palm.top() + 16),
        ]
        lengths = [74, 98, 108, 94, 72]
        channel_map = [2, 3, 3, 4, 5]
        for index, base in enumerate(finger_bases):
            value = self.values[channel_map[index]]
            self._draw_finger(painter, base, lengths[index], value, accent, link)
        thumb_value = self.values[0]
        opp = self.values[1]
        thumb_base = QPointF(palm.left() + 7, palm.top() + palm_h * 0.55)
        base_angle = math.radians(205 - opp * 44)
        self._draw_chain(painter, thumb_base, [40, 34], base_angle, thumb_value, accent, link, 9)
        painter.setPen(text)
        font = self.font()
        font.setPointSizeF(10)
        font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(font)
        painter.drawText(QRectF(rect.left(), rect.bottom() - 24, rect.width(), 20), Qt.AlignmentFlag.AlignCenter, "LIVE HAND MODEL")

    def _draw_finger(self, painter: QPainter, base: QPointF, length: float, value: float, accent: QColor, link: QColor) -> None:
        self._draw_chain(painter, base, [length * 0.40, length * 0.34, length * 0.26], -math.pi / 2, value, accent, link, 8)

    @staticmethod
    def _draw_chain(
        painter: QPainter,
        base: QPointF,
        lengths: list[float],
        initial_angle: float,
        value: float,
        accent: QColor,
        link: QColor,
        width: float,
    ) -> None:
        current = base
        angle = initial_angle
        bend = value * 0.82
        for index, length in enumerate(lengths):
            angle += bend * (0.45 + index * 0.30)
            end = QPointF(current.x() + math.cos(angle) * length, current.y() + math.sin(angle) * length)
            t = index / max(1, len(lengths) - 1)
            color = QColor(
                int(accent.red() * (1 - t) + link.red() * t),
                int(accent.green() * (1 - t) + link.green() * t),
                int(accent.blue() * (1 - t) + link.blue() * t),
            )
            painter.setPen(QPen(color, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(current, end)
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(current, width * 0.58, width * 0.58)
            current = end
        painter.drawEllipse(current, width * 0.5, width * 0.5)


class SystemFlowWidget(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.camera_on = False
        self.glove_on = False
        self.robot_on = False
        self.tx_on = False
        self.phase = 0.0
        self.timer = QTimer(self)
        self.timer.setInterval(30)
        self.timer.timeout.connect(self._tick)
        self.timer.start()
        self.setMinimumHeight(250)

    def set_states(self, camera: bool, glove: bool, robot: bool, tx: bool) -> None:
        self.camera_on, self.glove_on, self.robot_on, self.tx_on = camera, glove, robot, tx
        self.update()

    def _tick(self) -> None:
        self.phase = (self.phase + 0.008) % 1.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(18, 14, -18, -14)
        accent = self.palette().highlight().color()
        link = self.palette().link().color()
        text = self.palette().text().color()
        muted = self.palette().placeholderText().color()
        y = rect.center().y()
        camera = QPointF(rect.left() + rect.width() * 0.12, y - 56)
        glove = QPointF(rect.left() + rect.width() * 0.12, y + 56)
        core = QPointF(rect.center().x(), y)
        robot = QPointF(rect.right() - rect.width() * 0.12, y)
        for source, state in ((camera, self.camera_on), (glove, self.glove_on)):
            self._line(painter, source, core, state, accent, link)
        self._line(painter, core, robot, self.robot_on and self.tx_on, accent, link)
        self._node(painter, camera, "CAMERA", self.camera_on, accent, text, muted, 54)
        self._node(painter, glove, "GLOVE", self.glove_on, accent, text, muted, 54)
        self._node(painter, core, "Є-РУКА CORE", True, link, text, muted, 68)
        self._node(painter, robot, "ROBOT HAND", self.robot_on, accent, text, muted, 60)

    def _line(self, painter: QPainter, a: QPointF, b: QPointF, active: bool, accent: QColor, link: QColor) -> None:
        muted = QColor(self.palette().text().color())
        muted.setAlpha(30)
        painter.setPen(QPen(link if active else muted, 2.0))
        painter.drawLine(a, b)
        if active:
            point = QPointF(a.x() + (b.x() - a.x()) * self.phase, a.y() + (b.y() - a.y()) * self.phase)
            glow = QColor(accent)
            glow.setAlpha(70)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(glow)
            painter.drawEllipse(point, 9, 9)
            painter.setBrush(link)
            painter.drawEllipse(point, 3.6, 3.6)

    @staticmethod
    def _node(
        painter: QPainter,
        center: QPointF,
        label: str,
        active: bool,
        accent: QColor,
        text: QColor,
        muted: QColor,
        radius: float,
    ) -> None:
        fill = QColor(accent if active else muted)
        fill.setAlpha(30 if active else 12)
        painter.setPen(QPen(accent if active else muted, 1.8))
        painter.setBrush(fill)
        painter.drawEllipse(center, radius, radius)
        painter.setPen(text if active else muted)
        font = painter.font()
        font.setPointSizeF(9.2)
        font.setWeight(QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(QRectF(center.x() - radius, center.y() - 10, radius * 2, 20), Qt.AlignmentFlag.AlignCenter, label)
