"""The moderator's control window."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QKeySequence, QPainter, QPen, QShortcut
from PySide6.QtWidgets import (
    QAbstractButton, QButtonGroup, QGridLayout, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)

from . import theme
from .game import MAX_ANSWERS
from .widgets import StrikeMarks, draw_fitted

if TYPE_CHECKING:
    from .app import Controller


class AnswerButton(QAbstractButton):
    """Shows the moderator an answer and its points; clicking reveals it on the board."""

    def __init__(self, index: int, parent=None):
        super().__init__(parent)
        self.index = index
        self.answer = None
        self.revealed = False
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.setMinimumHeight(56)

    def set_state(self, answer, revealed: bool) -> None:
        self.answer, self.revealed = answer, revealed
        self.setEnabled(answer is not None and not revealed)
        self.setToolTip("" if answer is None else f"Reveal on board  ({self.index + 1})")
        self.update()

    def enterEvent(self, e):
        self.update()
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.update()
        super().leaveEvent(e)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        rad = theme.RADIUS

        if self.answer is None:
            p.setPen(QPen(theme.LINE, 2, Qt.PenStyle.DashLine))
            p.drawRoundedRect(r, rad, rad)
            return

        if self.revealed:
            bg, fg, border, num = theme.SURFACE, theme.MUTED, theme.SURFACE, theme.MUTED
        elif self.isDown():
            bg, fg, border, num = theme.FG, theme.RED, theme.FG, theme.RED
        elif self.underMouse():
            bg, fg, border, num = theme.FG, theme.INK, theme.FG, theme.RED
        else:
            bg, fg, border, num = theme.TILE, theme.FG, theme.TILE, theme.GOLD
        if self.hasFocus() and not self.revealed:
            border = theme.FG

        p.setPen(QPen(border, 2))
        p.setBrush(bg)
        p.drawRoundedRect(r, rad, rad)

        h = self.height()
        pad = 16
        num_rect = QRect(pad, 0, 28, h)
        pts_rect = QRect(self.width() - pad - 56, 0, 56, h)
        text_rect = QRect(num_rect.right() + 12, 0, pts_rect.left() - num_rect.right() - 24, h)
        left = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        right = Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight

        draw_fitted(p, num_rect, str(self.index + 1), num, 20, QFont.Weight.Black, left)
        draw_fitted(p, text_rect, self.answer.text, fg, 19, QFont.Weight.Bold, left)
        if self.revealed:
            width = min(text_rect.width(), p.fontMetrics().horizontalAdvance(self.answer.text))
            p.setPen(QPen(theme.MUTED, 2))
            p.drawLine(text_rect.left(), h // 2, text_rect.left() + width, h // 2)
        draw_fitted(p, pts_rect, str(self.answer.points), fg, 20, QFont.Weight.Black, right)


class KeyButton(QPushButton):
    """A flat button that shows its keyboard shortcut on the right."""

    def __init__(self, text: str, key: str = "", variant: str = "", parent=None):
        super().__init__(text, parent)
        self.key = key
        if variant:
            self.setProperty("variant", variant)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("text-align: left;")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def paintEvent(self, e):
        super().paintEvent(e)
        if not self.key:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        variant = self.property("variant")
        hover = self.underMouse() and not self.isDown()
        if not self.isEnabled():
            c = QColor(theme.DISABLED)
        elif self.isDown() or self.isChecked():
            c = QColor(theme.MUTED)
        elif hover:
            c = QColor(theme.FG if variant == "primary" else theme.RED)
        elif variant == "primary":
            c = QColor(theme.RED)
        elif variant == "danger":
            c = QColor(theme.GOLD)
        else:
            c = QColor(theme.MUTED)
        p.setPen(c)
        p.setFont(theme.font(13, QFont.Weight.Bold))
        p.drawText(self.rect().adjusted(0, 0, -18, 0),
                   Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, self.key)


def eyebrow(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setProperty("role", "eyebrow")
    return lbl


class Stat(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self.title = eyebrow(title)
        self.value = QLabel("0")
        self.value.setFont(theme.font(30, QFont.Weight.Black))
        lay.addWidget(self.title)
        lay.addWidget(self.value)


class ConsoleWindow(QWidget):
    def __init__(self, controller: Controller):
        super().__init__()
        self.c = controller
        self.game = controller.game
        g = self.game
        self.setWindowTitle("Faculty Feud — Moderator")
        self.resize(980, 760)

        # Header
        self.round_lbl = eyebrow("")
        self.status_lbl = eyebrow("")
        head = QHBoxLayout()
        head.addWidget(eyebrow("Faculty Feud · Moderator"))
        head.addStretch()
        head.addWidget(self.round_lbl)
        head.addSpacing(16)
        head.addWidget(self.status_lbl)

        self.question = QLabel()
        self.question.setProperty("role", "question")
        self.question.setWordWrap(True)
        self.question.setMinimumHeight(64)
        self.question.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # Answers
        grid = QGridLayout()
        grid.setSpacing(10)
        self.answers = []
        for i in range(MAX_ANSWERS):
            b = AnswerButton(i)
            b.clicked.connect(lambda _=False, i=i: self.c.reveal(i))
            self.answers.append(b)
            grid.addWidget(b, i % 4, i // 4)

        # Scoreboard
        self.team_stats = [Stat(g.teams[0]), Stat(g.teams[1])]
        self.bank_stat = Stat("On the board")
        self.strikes = StrikeMarks()
        self.strikes.setFixedSize(132, 36)
        strike_box = QVBoxLayout()
        strike_box.setSpacing(4)
        strike_box.addWidget(eyebrow("Strikes"))
        strike_box.addWidget(self.strikes)
        stats = QHBoxLayout()
        stats.setSpacing(32)
        stats.addWidget(self.team_stats[0])
        stats.addWidget(self.bank_stat)
        stats.addLayout(strike_box)
        stats.addStretch()
        stats.addWidget(self.team_stats[1])
        self.team_stats[1].title.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.team_stats[1].value.setAlignment(Qt.AlignmentFlag.AlignRight)

        # Controls
        self.show_q = KeyButton("Show question", "Q")
        self.strike_btn = KeyButton("Strike", "X", "danger")
        self.buzz_btn = KeyButton("Buzzer only", "B", "danger")
        self.buzz_btn.setToolTip("Flash an X and play the buzzer without adding a strike")
        self.award_btns = [KeyButton(f"Award {g.teams[0]}", "←"),
                           KeyButton(f"Award {g.teams[1]}", "→")]
        self.undo_btn = KeyButton("Undo", "⌘Z" if sys.platform == "darwin" else "Ctrl+Z")
        self.full_btn = KeyButton("Board fullscreen", "F")
        self.next_btn = KeyButton("Next question", "N", "primary")

        self.show_q.clicked.connect(g.show_question)
        self.strike_btn.clicked.connect(self.c.strike)
        self.buzz_btn.clicked.connect(self.c.buzz)
        self.award_btns[0].clicked.connect(lambda: g.award(0))
        self.award_btns[1].clicked.connect(lambda: g.award(1))
        self.undo_btn.clicked.connect(g.undo)
        self.full_btn.clicked.connect(self.c.toggle_board_fullscreen)
        self.next_btn.clicked.connect(self.next_question)

        self.mult_group = QButtonGroup(self)
        mult_row = QHBoxLayout()
        mult_row.setSpacing(6)
        for m in (1, 2, 3):
            b = QPushButton(f"{m}×")
            b.setCheckable(True)
            b.setProperty("variant", "segment")
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setToolTip("Points multiplier for this question")
            self.mult_group.addButton(b, m)
            mult_row.addWidget(b)
        self.mult_group.idClicked.connect(g.set_multiplier)
        mult_box = QHBoxLayout()
        mult_box.addWidget(eyebrow("Points"))
        mult_box.addSpacing(6)
        mult_box.addLayout(mult_row)

        row1 = QHBoxLayout()
        row1.setSpacing(10)
        for b in (self.show_q, self.strike_btn, self.buzz_btn):
            row1.addWidget(b)
        row2 = QHBoxLayout()
        row2.setSpacing(10)
        row2.addWidget(self.award_btns[0])
        row2.addWidget(self.award_btns[1])
        row2.addSpacing(10)
        row2.addLayout(mult_box)
        row3 = QHBoxLayout()
        row3.setSpacing(10)
        row3.addWidget(self.undo_btn)
        row3.addWidget(self.full_btn)
        row3.addWidget(self.next_btn)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 22, 28, 24)
        root.setSpacing(14)
        root.addLayout(head)
        root.addWidget(self.question)
        root.addLayout(grid, 1)
        root.addSpacing(6)
        root.addLayout(stats)
        root.addSpacing(6)
        root.addLayout(row1)
        root.addLayout(row2)
        root.addLayout(row3)

        self._shortcuts()
        self.refresh()

    def _shortcuts(self) -> None:
        def bind(seq, fn):
            QShortcut(QKeySequence(seq), self, activated=fn)

        g = self.game
        for i in range(MAX_ANSWERS):
            bind(str(i + 1), lambda i=i: self.c.reveal(i))
        bind("Q", g.show_question)
        bind("X", self.c.strike)
        bind("B", self.c.buzz)
        bind("Left", lambda: g.award(0))
        bind("Right", lambda: g.award(1))
        bind(QKeySequence.StandardKey.Undo, g.undo)
        bind("F", self.c.toggle_board_fullscreen)
        bind("N", self.next_question)

    def next_question(self) -> None:
        g = self.game
        if g.finished:
            return
        if g.bank and not g.awarded:
            box = QMessageBox(self)
            box.setWindowTitle("Points not awarded")
            box.setText(f"{g.bank} points are still on the board.\nMove on without awarding them?")
            move_on = box.addButton("Move on", QMessageBox.ButtonRole.AcceptRole)
            box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
            box.exec()
            if box.clickedButton() is not move_on:
                return
        g.next_question()

    def refresh(self) -> None:
        g = self.game
        q = g.question
        live = not g.finished

        self.round_lbl.setText(f"ROUND {g.round_number} OF {len(g.questions)}")
        if g.finished:
            self.status_lbl.setText("GAME OVER")
            self.status_lbl.setStyleSheet(f"color: {theme.FG.name()};")
        elif g.question_shown:
            self.status_lbl.setText("● QUESTION ON BOARD")
            self.status_lbl.setStyleSheet(f"color: {theme.FG.name()};")
        else:
            self.status_lbl.setText("○ QUESTION HIDDEN")
            self.status_lbl.setStyleSheet("")
        self.question.setText(q.text)

        for i, b in enumerate(self.answers):
            b.set_state(q.answers[i] if i < len(q.answers) else None, g.is_revealed(i))
            if not live:
                b.setEnabled(False)

        for stat, score in zip(self.team_stats, g.scores):
            stat.value.setText(str(score))
        self.bank_stat.title.setText(
            "ON THE BOARD" + (f" (×{g.multiplier})" if g.multiplier > 1 else ""))
        self.bank_stat.value.setText(str(g.bank))
        self.strikes.setCount(g.strikes)

        self.show_q.setEnabled(live and not g.question_shown)
        self.strike_btn.setEnabled(live and g.strikes < 3)
        self.buzz_btn.setEnabled(live)
        for b in self.award_btns:
            b.setEnabled(live and not g.awarded and g.bank > 0)
        self.undo_btn.setEnabled(g.can_undo)
        self.next_btn.setEnabled(live)
        self.next_btn.setText("Finish game" if g.is_last_question else "Next question")
        self.mult_group.button(g.multiplier).setChecked(True)
        for b in self.mult_group.buttons():
            b.setEnabled(live)

