"""Small custom-painted widgets used by the board and the console."""

from __future__ import annotations

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QFontMetrics, QPainter, QPen
from PySide6.QtWidgets import QSizePolicy, QWidget

from . import theme


def fit_font(base: QFont, text: str, rect: QRect, flags: int, max_px: int) -> QFont:
    """Largest copy of ``base`` (up to ``max_px``) whose ``text`` fits in ``rect``."""
    f = QFont(base)
    lo, hi = 6, max(6, max_px)
    while lo < hi:
        mid = (lo + hi + 1) // 2
        f.setPixelSize(mid)
        r = QFontMetrics(f).boundingRect(rect, flags, text)
        if r.width() <= rect.width() and r.height() <= rect.height():
            lo = mid
        else:
            hi = mid - 1
    f.setPixelSize(lo)
    return f


def draw_fitted(
    p: QPainter,
    rect: QRect,
    text: str,
    color: QColor,
    max_px: int,
    weight: QFont.Weight = QFont.Weight.Bold,
    align: Qt.AlignmentFlag = Qt.AlignmentFlag.AlignCenter,
    wrap: bool = False,
) -> None:
    if not text or rect.width() <= 0 or rect.height() <= 0:
        return
    flags = int(align) | (int(Qt.TextFlag.TextWordWrap) if wrap else 0)
    p.setFont(fit_font(theme.font(weight=weight), text, rect, flags, max_px))
    p.setPen(color)
    p.drawText(rect, flags, text)


class FitLabel(QWidget):
    """Text that scales to fill its box: the sizing behavior of the original board."""

    def __init__(self, text="", color=theme.FG, height_ratio=0.6, wrap=False,
                 weight=QFont.Weight.Bold, align=Qt.AlignmentFlag.AlignCenter, parent=None):
        super().__init__(parent)
        self._text, self._color = text, color
        self._ratio, self._wrap, self._weight, self._align = height_ratio, wrap, weight, align
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(10)

    def setText(self, text: str) -> None:
        if text != self._text:
            self._text = text
            self.update()

    def setColor(self, color: QColor) -> None:
        self._color = color
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        max_px = int(self.height() * self._ratio)
        draw_fitted(p, self.rect(), self._text, self._color, max_px,
                    self._weight, self._align, self._wrap)


class StrikeMarks(QWidget):
    """Three boxes; filled red with an X for each strike."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._count = 0
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumSize(60, 20)

    def setCount(self, n: int) -> None:
        if n != self._count:
            self._count = n
            self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        gap = self.height() * 0.2
        side = min(self.height(), (self.width() - 2 * gap) / 3)
        x0 = (self.width() - 3 * side - 2 * gap) / 2
        y0 = (self.height() - side) / 2
        for i in range(3):
            box = QRectF(x0 + i * (side + gap), y0, side, side)
            active = i < self._count
            p.setPen(QPen(theme.FG if active else theme.LINE, max(2.0, side * 0.06)))
            p.setBrush(theme.FG if active else Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(box.adjusted(1, 1, -1, -1), side * 0.12, side * 0.12)
            if active:
                draw_x(p, box.adjusted(side * 0.26, side * 0.26, -side * 0.26, -side * 0.26),
                       theme.RED, side * 0.12)


def draw_x(p: QPainter, box: QRectF, color: QColor, width: float) -> None:
    pen = QPen(color, width)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    p.drawLine(box.topLeft(), box.bottomRight())
    p.drawLine(box.topRight(), box.bottomLeft())
