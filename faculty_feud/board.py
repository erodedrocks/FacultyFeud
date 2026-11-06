"""The contestant-facing board, meant for a projector."""

from __future__ import annotations

from PySide6.QtCore import QEasingCurve, QRect, QRectF, Qt, QTimer, QVariantAnimation
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QGridLayout, QHBoxLayout, QSizePolicy, QStackedLayout, QVBoxLayout, QWidget,
)

from . import theme
from .game import MAX_ANSWERS, Game
from .widgets import FitLabel, StrikeMarks, draw_fitted, draw_x

MULTIPLIER_NAMES = {2: "DOUBLE POINTS", 3: "TRIPLE POINTS"}


class Tile(QWidget):
    """One answer slot: empty, hidden (shows its number) or revealed."""

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.answer = None  # Answer | None
        self.revealed = False
        self._flash = 0.0
        self._anim = QVariantAnimation(self, startValue=1.0, endValue=0.0, duration=600)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.valueChanged.connect(self._on_flash)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def _on_flash(self, v):
        self._flash = v
        self.update()

    def set_state(self, answer, revealed: bool) -> None:
        if revealed and not self.revealed and answer is not None:
            self._anim.stop()
            self._anim.start()
        self.answer, self.revealed = answer, revealed
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        h = self.height()
        r = QRectF(self.rect()).adjusted(1.5, 1.5, -1.5, -1.5)
        radius = min(theme.RADIUS * 1.5, h * 0.12)
        stroke = max(2.0, h * 0.03)

        if self.answer is None:
            p.setPen(QPen(theme.LINE, stroke))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(r, radius, radius)
            return

        if not self.revealed:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(theme.TILE)
            p.drawRoundedRect(r, radius, radius)
            draw_fitted(p, self.rect(), str(self.index + 1), theme.FG, int(h * 0.55),
                        QFont.Weight.Black)
            return

        # Revealed: solid white tile, black answer, red points block with white numerals.
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(theme.FG)
        p.drawRoundedRect(r, radius, radius)

        pts_w = int(h * 1.15)
        inset = int(stroke * 2)
        pts_rect = QRect(self.width() - pts_w - inset, inset, pts_w, self.height() - 2 * inset)
        p.setBrush(theme.RED)
        p.drawRoundedRect(QRectF(pts_rect), radius * 0.7, radius * 0.7)
        draw_fitted(p, pts_rect.adjusted(6, 0, -6, 0), str(self.answer.points), theme.FG,
                    int(h * 0.5), QFont.Weight.Black)

        pad = int(h * 0.22)
        text_rect = QRect(pad, 0, pts_rect.left() - 2 * pad, self.height())
        draw_fitted(p, text_rect, self.answer.text.upper(), theme.INK, int(h * 0.42),
                    QFont.Weight.Black, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)

        if self._flash > 0:
            c = QColor(theme.GOLD)
            c.setAlphaF(self._flash)
            p.setBrush(c)
            p.drawRoundedRect(r, radius, radius)


class TeamPanel(QWidget):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        self.name = FitLabel(name.upper(), theme.MUTED, 0.6)
        self.score = FitLabel("0", theme.FG, 0.95, weight=QFont.Weight.Black)
        lay.addWidget(self.name, 2)
        lay.addWidget(self.score, 5)


class StrikeOverlay(QWidget):
    """Full-board red X flash, shown briefly after a strike."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._count = 1
        self._timer = QTimer(self, singleShot=True, interval=1100, timeout=self.hide)
        self.hide()

    def flash(self, count: int) -> None:
        self._count = max(1, min(3, count))
        self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        self.update()
        self._timer.start()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        shade = QColor(theme.INK)
        shade.setAlpha(210)
        p.fillRect(self.rect(), shade)
        side = min(self.height() * 0.5, self.width() * 0.8 / self._count)
        gap = side * 0.15
        total = self._count * side + (self._count - 1) * gap
        x = (self.width() - total) / 2
        y = (self.height() - side) / 2
        for _ in range(self._count):
            draw_x(p, QRectF(x, y, side, side), theme.FG, side * 0.16)
            x += side + gap


class BoardView(QWidget):
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game
        self.title = FitLabel("FACULTY FEUD", theme.FG, 0.8, weight=QFont.Weight.Black)
        self.question = FitLabel("", theme.FG, 0.42, wrap=True)

        grid = QGridLayout()
        grid.setSpacing(12)
        self.tiles = []
        for i in range(MAX_ANSWERS):
            tile = Tile(i)
            self.tiles.append(tile)
            grid.addWidget(tile, i % 4, i // 4)  # fill down the left column first

        self.teams = [TeamPanel(game.teams[0]), TeamPanel(game.teams[1])]
        self.bank = FitLabel("0", theme.FG, 0.95, weight=QFont.Weight.Black)
        self.strikes = StrikeMarks()
        center = QVBoxLayout()
        center.setSpacing(6)
        center.addWidget(self.bank, 5)
        center.addWidget(self.strikes, 2)

        footer = QHBoxLayout()
        footer.setSpacing(24)
        footer.addWidget(self.teams[0], 1)
        footer.addLayout(center, 1)
        footer.addWidget(self.teams[1], 1)

        self.root = QVBoxLayout(self)
        self.root.addWidget(self.title, 2)
        self.root.addWidget(self.question, 3)
        self.root.addSpacing(8)
        self.root.addLayout(grid, 11)
        self.root.addSpacing(8)
        self.root.addLayout(footer, 4)

    def resizeEvent(self, e):
        m = int(min(self.width(), self.height()) * 0.04)
        self.root.setContentsMargins(m, m // 2, m, m)
        super().resizeEvent(e)

    def refresh(self) -> None:
        g = self.game
        q = g.question
        if g.question_shown:
            self.question.setText(q.text)
            self.question.setColor(theme.FG)
        else:
            label = f"ROUND {g.round_number}"
            if g.multiplier in MULTIPLIER_NAMES:
                label += f"  ·  {MULTIPLIER_NAMES[g.multiplier]}"
            self.question.setText(label)
            self.question.setColor(theme.MUTED)
        for i, tile in enumerate(self.tiles):
            answer = q.answers[i] if i < len(q.answers) else None
            tile.set_state(answer, g.is_revealed(i))
        for panel, score in zip(self.teams, g.scores):
            panel.score.setText(str(score))
        self.bank.setText(str(g.bank))
        self.strikes.setCount(g.strikes)


class FinalView(QWidget):
    def __init__(self, game: Game, parent=None):
        super().__init__(parent)
        self.game = game
        self.headline = FitLabel("", theme.FG, 0.8, weight=QFont.Weight.Black)
        self.scores = FitLabel("", theme.FG, 0.6)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(60, 60, 60, 60)
        lay.addStretch(2)
        lay.addWidget(FitLabel("FINAL SCORE", theme.MUTED, 0.6), 1)
        lay.addWidget(self.headline, 3)
        lay.addWidget(self.scores, 2)
        lay.addStretch(2)

    def refresh(self) -> None:
        g = self.game
        winner = g.winner()
        self.headline.setText(f"{winner.upper()} WINS" if winner else "IT'S A TIE")
        (a, b), (ta, tb) = g.scores, g.teams
        self.scores.setText(f"{ta.upper()}  {a}   —   {b}  {tb.upper()}")


class BoardWindow(QWidget):
    def __init__(self, game: Game):
        super().__init__()
        self.game = game
        self.setWindowTitle("Faculty Feud")
        self.resize(1280, 720)
        self.board = BoardView(game)
        self.final = FinalView(game)
        self.stack = QStackedLayout(self)
        self.stack.addWidget(self.board)
        self.stack.addWidget(self.final)
        self.overlay = StrikeOverlay(self)
        self.refresh()

    def refresh(self) -> None:
        if self.game.finished:
            self.overlay.hide()
            self.final.refresh()
            self.stack.setCurrentWidget(self.final)
        else:
            self.board.refresh()
            self.stack.setCurrentWidget(self.board)

    def show_strike(self, count: int) -> None:
        self.overlay.flash(count)

    def toggle_fullscreen(self) -> None:
        self.showNormal() if self.isFullScreen() else self.showFullScreen()

    def mouseDoubleClickEvent(self, _):
        self.toggle_fullscreen()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_F:
            self.toggle_fullscreen()
        elif e.key() == Qt.Key.Key_Escape and self.isFullScreen():
            self.showNormal()
        else:
            super().keyPressEvent(e)
