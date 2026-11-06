"""Entry point: wires the game to the board, the console and sound."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtWidgets import QApplication, QMessageBox

from . import theme
from .board import BoardWindow
from .console import ConsoleWindow
from .game import MAX_STRIKES, Game

PACKAGE_DIR = Path(__file__).parent
DEFAULT_QUESTIONS = PACKAGE_DIR / "data" / "faculty_feud_2022.csv"
SOUNDS_DIR = PACKAGE_DIR / "sounds"


class Sounds:
    def __init__(self, muted: bool):
        self._effects = {}
        if muted:
            return
        try:
            from PySide6.QtMultimedia import QSoundEffect
        except ImportError:
            print("QtMultimedia unavailable; running without sound", file=sys.stderr)
            return
        for name in ("ding", "strike"):
            fx = QSoundEffect()
            fx.setSource(QUrl.fromLocalFile(str(SOUNDS_DIR / f"{name}.wav")))
            self._effects[name] = fx

    def play(self, name: str) -> None:
        if fx := self._effects.get(name):
            fx.play()


class Controller:
    """Actions that touch more than the game state (sound, board animation)."""

    def __init__(self, game: Game, sounds: Sounds):
        self.game = game
        self.sounds = sounds
        self.board = BoardWindow(game)
        self.console = ConsoleWindow(self)
        game.subscribe(self.board.refresh)
        game.subscribe(self.console.refresh)

    def reveal(self, i: int) -> None:
        if self.game.reveal(i):
            self.sounds.play("ding")

    def strike(self) -> None:
        if self.game.finished or self.game.strikes >= MAX_STRIKES:
            return
        self.board.show_strike(self.game.strike())
        self.sounds.play("strike")

    def buzz(self) -> None:
        if self.game.finished:
            return
        self.board.show_strike(1)
        self.sounds.play("strike")

    def toggle_board_fullscreen(self) -> None:
        self.board.toggle_fullscreen()

    def show(self) -> None:
        screens = QApplication.screens()
        primary = QApplication.primaryScreen()
        # With a projector attached, put the board on it and leave the console on the laptop.
        external = next((s for s in screens if s is not primary), None)
        if external:
            self.board.setScreen(external)
            self.board.move(external.geometry().topLeft())
            self.board.showFullScreen()
        else:
            self.board.show()
        self.console.show()
        self.console.raise_()
        self.console.activateWindow()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="faculty-feud", description=__doc__)
    parser.add_argument("questions", nargs="?", default=DEFAULT_QUESTIONS, type=Path,
                        help="question CSV (default: the 2022 SCS Day set)")
    parser.add_argument("--mute", action="store_true", help="disable sound effects")
    args = parser.parse_args(argv)

    app = QApplication(sys.argv[:1])
    app.setApplicationName("Faculty Feud")
    app.setFont(theme.font(15))
    app.setStyleSheet(theme.STYLESHEET)

    try:
        game = Game.from_csv(args.questions)
    except (OSError, ValueError) as e:
        QMessageBox.critical(None, "Could not load questions", str(e))
        sys.exit(1)

    controller = Controller(game, Sounds(args.mute))
    controller.show()
    sys.exit(app.exec())
