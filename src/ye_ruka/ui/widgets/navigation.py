from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen, QPolygonF
from PySide6.QtWidgets import QAbstractButton, QSizePolicy


class NavigationButton(QAbstractButton):
    def __init__(self, icon_name: str, text: str) -> None:
        super().__init__()
        self.icon_name = icon_name
        self.setText(text)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(52)

    def sizeHint(self) -> QSize:
        return QSize(198, 52)

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = QRectF(self.rect()).adjusted(4, 3, -4, -3)
        accent = self.palette().highlight().color()
        text_color = self.palette().text().color()
        muted = self.palette().placeholderText().color()
        if self.isChecked():
            bg = QColor(accent)
            bg.setAlpha(36)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(bg)
            painter.drawRoundedRect(rect, 15, 15)
            painter.setBrush(accent)
            painter.drawRoundedRect(QRectF(rect.left(), rect.top() + 10, 3, rect.height() - 20), 2, 2)
            color = accent
        elif self.underMouse():
            hover = QColor(text_color)
            hover.setAlpha(12)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(hover)
            painter.drawRoundedRect(rect, 15, 15)
            color = text_color
        else:
            color = muted
        icon_rect = QRectF(rect.left() + 18, rect.center().y() - 11, 22, 22)
        self._draw_icon(painter, icon_rect, color)
        painter.setPen(color if self.isChecked() else text_color)
        font = self.font()
        font.setPointSizeF(10.2)
        font.setWeight(QFont.Weight.DemiBold if self.isChecked() else QFont.Weight.Medium)
        painter.setFont(font)
        painter.drawText(
            QRectF(icon_rect.right() + 16, rect.top(), rect.width() - 62, rect.height()),
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            self.text(),
        )

    def _draw_icon(self, painter: QPainter, rect: QRectF, color: QColor) -> None:
        pen = QPen(color, 1.8, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
        if self.icon_name == "home":
            path = QPainterPath(QPointF(x + 2, y + 10))
            path.lineTo(x + w / 2, y + 2)
            path.lineTo(x + w - 2, y + 10)
            path.moveTo(x + 5, y + 9)
            path.lineTo(x + 5, y + h - 3)
            path.lineTo(x + w - 5, y + h - 3)
            path.lineTo(x + w - 5, y + 9)
            painter.drawPath(path)
        elif self.icon_name == "camera":
            painter.drawRoundedRect(QRectF(x + 1, y + 5, w - 2, h - 9), 4, 4)
            painter.drawEllipse(QPointF(x + w / 2, y + h / 2 + 1), 4.3, 4.3)
            painter.drawLine(QPointF(x + 7, y + 5), QPointF(x + 9, y + 2))
            painter.drawLine(QPointF(x + 9, y + 2), QPointF(x + 14, y + 2))
            painter.drawLine(QPointF(x + 14, y + 2), QPointF(x + 16, y + 5))
        elif self.icon_name == "glove":
            path = QPainterPath(QPointF(x + 6, y + h - 2))
            path.lineTo(x + 4, y + 11)
            path.cubicTo(x + 3, y + 7, x + 6, y + 6, x + 8, y + 9)
            path.lineTo(x + 8, y + 4)
            path.cubicTo(x + 8, y + 1, x + 11, y + 1, x + 11, y + 4)
            path.lineTo(x + 11, y + 2)
            path.cubicTo(x + 11, y, x + 14, y, x + 14, y + 3)
            path.lineTo(x + 14, y + 4)
            path.cubicTo(x + 14, y + 1, x + 17, y + 2, x + 17, y + 5)
            path.lineTo(x + 17, y + 7)
            path.cubicTo(x + 18, y + 4, x + 21, y + 6, x + 20, y + 9)
            path.lineTo(x + 19, y + 15)
            path.cubicTo(x + 18, y + 20, x + 14, y + 21, x + 10, y + 21)
            path.cubicTo(x + 8, y + 21, x + 7, y + 20, x + 6, y + h - 2)
            painter.drawPath(path)
        elif self.icon_name == "manual":
            for offset, knob in ((4, 8), (11, 14), (18, 6)):
                painter.drawLine(QPointF(x + offset, y + 2), QPointF(x + offset, y + h - 2))
                painter.drawEllipse(QPointF(x + offset, y + knob), 2.8, 2.8)
        elif self.icon_name == "calibration":
            painter.drawEllipse(rect.adjusted(3, 3, -3, -3))
            painter.drawLine(QPointF(x + w / 2, y), QPointF(x + w / 2, y + 6))
            painter.drawLine(QPointF(x + w / 2, y + h - 6), QPointF(x + w / 2, y + h))
            painter.drawLine(QPointF(x, y + h / 2), QPointF(x + 6, y + h / 2))
            painter.drawLine(QPointF(x + w - 6, y + h / 2), QPointF(x + w, y + h / 2))
            painter.drawEllipse(QPointF(x + w / 2, y + h / 2), 2.5, 2.5)
        elif self.icon_name == "diagnostics":
            points = [
                QPointF(x + 1, y + 16), QPointF(x + 5, y + 16), QPointF(x + 8, y + 7),
                QPointF(x + 12, y + 20), QPointF(x + 16, y + 10), QPointF(x + 20, y + 10),
            ]
            painter.drawPolyline(QPolygonF(points))
        elif self.icon_name == "service":
            painter.drawLine(QPointF(x + 4, y + h - 4), QPointF(x + w - 5, y + 5))
            painter.drawEllipse(QPointF(x + 6, y + h - 6), 4, 4)
            painter.drawArc(QRectF(x + w - 10, y + 1, 10, 10), 35 * 16, 245 * 16)
            painter.drawLine(QPointF(x + w - 3, y + 2), QPointF(x + w - 8, y + 7))
        elif self.icon_name == "settings":
            painter.drawEllipse(QPointF(x + w / 2, y + h / 2), 7.5, 7.5)
            painter.drawEllipse(QPointF(x + w / 2, y + h / 2), 2.5, 2.5)
            for angle in range(0, 360, 45):
                import math
                a = math.radians(angle)
                p1 = QPointF(x + w / 2 + math.cos(a) * 9, y + h / 2 + math.sin(a) * 9)
                p2 = QPointF(x + w / 2 + math.cos(a) * 11, y + h / 2 + math.sin(a) * 11)
                painter.drawLine(p1, p2)
