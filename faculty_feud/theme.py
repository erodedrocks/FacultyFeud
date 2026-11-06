"""Colors, fonts and the stylesheet shared by both windows."""

from PySide6.QtGui import QColor, QFont

# A deepened Carnegie Red with soft cream type and wine-colored blocks, so the board
# reads clearly without glaring. Gold appears only on the dark TILE color.
RED = QColor("#6A0C1D")  # Carnegie Red (#C41230), darkened
GOLD = QColor("#E9B65A")  # Gold Thread, softened
BG = RED
FG = QColor("#F3E9E2")  # cream, 10.5:1 on BG
INK = QColor("#2E0B12")  # dark text on cream
TILE = QColor("#3F0611")  # hidden answers and dark buttons
MUTED = QColor("#D9AEB4")  # secondary text, 6.3:1 on BG
LINE = QColor("#94304A")  # empty slots and dividers
SURFACE = QColor("#541020")  # already-revealed answers in the console
DISABLED = QColor("#A65E6C")

FONT_FAMILIES = ["Helvetica Neue", "Arial"]

RADIUS = 8


def font(px: int = 16, weight: QFont.Weight = QFont.Weight.DemiBold) -> QFont:
    f = QFont()
    f.setFamilies(FONT_FAMILIES)
    f.setPixelSize(max(1, px))
    f.setWeight(weight)
    return f


STYLESHEET = f"""
QWidget {{
    background: {BG.name()};
    color: {FG.name()};
}}
QPushButton {{
    background: transparent;
    color: {FG.name()};
    border: 2px solid {FG.name()};
    border-radius: {RADIUS}px;
    padding: 12px 18px;
    font-size: 15px;
    font-weight: 600;
}}
QPushButton:hover {{ background: {FG.name()}; color: {RED.name()}; }}
QPushButton:pressed, QPushButton:checked {{
    background: {TILE.name()}; border-color: {TILE.name()}; color: {FG.name()};
}}
QPushButton:focus {{ border-color: {GOLD.name()}; }}
QPushButton:disabled {{ color: {DISABLED.name()}; border-color: {DISABLED.name()}; background: transparent; }}

QPushButton[variant="danger"] {{ background: {TILE.name()}; border-color: {TILE.name()}; }}
QPushButton[variant="danger"]:hover {{ background: {FG.name()}; border-color: {FG.name()}; color: {INK.name()}; }}
QPushButton[variant="danger"]:disabled {{ background: transparent; border-color: {DISABLED.name()}; }}

QPushButton[variant="primary"] {{
    background: {FG.name()}; border-color: {FG.name()}; color: {RED.name()};
}}
QPushButton[variant="primary"]:hover {{ background: {TILE.name()}; border-color: {TILE.name()}; color: {FG.name()}; }}
QPushButton[variant="primary"]:disabled {{ background: transparent; color: {DISABLED.name()}; border-color: {DISABLED.name()}; }}

QPushButton[variant="segment"] {{ padding: 10px 0; min-width: 56px; }}

QLabel[role="eyebrow"] {{ color: {MUTED.name()}; font-size: 12px; font-weight: 700; letter-spacing: 2px; }}
QLabel[role="question"] {{ font-size: 22px; font-weight: 700; }}
QLabel[role="stat"] {{ font-size: 15px; font-weight: 600; }}

QMessageBox QLabel {{ font-size: 15px; }}
QToolTip {{ background: {FG.name()}; color: {INK.name()}; border: none; padding: 6px; }}
"""
