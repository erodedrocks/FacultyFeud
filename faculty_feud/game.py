"""Game state for Faculty Feud. Pure Python so it can be tested without Qt."""

from __future__ import annotations

import copy
import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

MAX_ANSWERS = 8
MAX_STRIKES = 3


@dataclass(frozen=True)
class Answer:
    text: str
    points: int


@dataclass(frozen=True)
class Question:
    text: str
    answers: tuple[Answer, ...]


def load_csv(path: str | Path) -> tuple[tuple[str, str], list[Question]]:
    """Read a question file.

    Line 1: ``team one,team two``
    Each following line: ``question,answer,points,answer,points,...``
    Blank trailing cells are ignored; quoted cells may contain commas.
    """
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = [[cell.strip() for cell in row] for row in csv.reader(f)]
    rows = [row for row in rows if any(row)]
    if not rows:
        raise ValueError(f"{path}: file is empty")

    header = [cell for cell in rows[0] if cell]
    if len(header) < 2:
        raise ValueError(f"{path}: first line must name two teams")
    teams = (header[0], header[1])

    questions = []
    for line_no, row in enumerate(rows[1:], start=2):
        text, cells = row[0], row[1:]
        answers = []
        for i in range(0, len(cells) - 1, 2):
            answer, points = cells[i], cells[i + 1]
            if not answer and not points:
                continue
            try:
                answers.append(Answer(answer, int(points)))
            except ValueError:
                raise ValueError(
                    f"{path}:{line_no}: points for {answer!r} must be a number, got {points!r}"
                ) from None
        if not text or not answers:
            raise ValueError(f"{path}:{line_no}: needs a question and at least one answer")
        if len(answers) > MAX_ANSWERS:
            raise ValueError(f"{path}:{line_no}: at most {MAX_ANSWERS} answers per question")
        questions.append(Question(text, tuple(answers)))

    if not questions:
        raise ValueError(f"{path}: no questions found")
    return teams, questions


@dataclass
class _RoundState:
    index: int = 0
    scores: list[int] = field(default_factory=lambda: [0, 0])
    revealed: set[int] = field(default_factory=set)
    strikes: int = 0
    bank: int = 0
    multiplier: int = 1
    awarded: bool = False
    question_shown: bool = False
    finished: bool = False


class Game:
    """Holds the game and notifies listeners whenever anything changes."""

    def __init__(self, teams: tuple[str, str], questions: list[Question]):
        self.teams = teams
        self.questions = questions
        self._s = _RoundState()
        self._history: list[_RoundState] = []
        self._listeners: list[Callable[[], None]] = []

    @classmethod
    def from_csv(cls, path: str | Path) -> Game:
        return cls(*load_csv(path))

    # -- observation -------------------------------------------------------

    def subscribe(self, fn: Callable[[], None]) -> None:
        self._listeners.append(fn)

    def _changed(self) -> None:
        for fn in self._listeners:
            fn()

    def _checkpoint(self) -> None:
        self._history.append(copy.deepcopy(self._s))

    # -- read-only state ---------------------------------------------------

    @property
    def question(self) -> Question:
        return self.questions[self._s.index]

    @property
    def round_number(self) -> int:
        return self._s.index + 1

    @property
    def scores(self) -> tuple[int, int]:
        return tuple(self._s.scores)

    @property
    def strikes(self) -> int:
        return self._s.strikes

    @property
    def multiplier(self) -> int:
        return self._s.multiplier

    @property
    def bank(self) -> int:
        """Points currently on the board, with the multiplier applied."""
        return self._s.bank * self._s.multiplier

    @property
    def awarded(self) -> bool:
        return self._s.awarded

    @property
    def question_shown(self) -> bool:
        return self._s.question_shown

    @property
    def finished(self) -> bool:
        return self._s.finished

    @property
    def is_last_question(self) -> bool:
        return self._s.index == len(self.questions) - 1

    @property
    def can_undo(self) -> bool:
        return bool(self._history)

    def is_revealed(self, i: int) -> bool:
        return i in self._s.revealed

    def winner(self) -> str | None:
        a, b = self._s.scores
        if a == b:
            return None
        return self.teams[0] if a > b else self.teams[1]

    # -- actions -----------------------------------------------------------

    def show_question(self) -> None:
        if self._s.question_shown:
            return
        self._checkpoint()
        self._s.question_shown = True
        self._changed()

    def reveal(self, i: int) -> bool:
        """Flip answer ``i``. Returns True if it was newly revealed.

        Points only go into the bank while the round is live (not yet awarded
        and fewer than three strikes), matching the original game.
        """
        if self._s.finished or i in self._s.revealed or not 0 <= i < len(self.question.answers):
            return False
        self._checkpoint()
        self._s.revealed.add(i)
        if not self._s.awarded and self._s.strikes < MAX_STRIKES:
            self._s.bank += self.question.answers[i].points
        self._changed()
        return True

    def strike(self) -> int:
        """Add a strike (capped at three). Returns the new strike count."""
        if self._s.strikes < MAX_STRIKES:
            self._checkpoint()
            self._s.strikes += 1
            self._changed()
        return self._s.strikes

    def set_multiplier(self, m: int) -> None:
        if m == self._s.multiplier:
            return
        self._checkpoint()
        self._s.multiplier = m
        self._changed()

    def award(self, team: int) -> None:
        if self._s.awarded or self._s.finished:
            return
        self._checkpoint()
        self._s.scores[team] += self.bank
        self._s.bank = 0
        self._s.awarded = True
        self._changed()

    def next_question(self) -> None:
        if self._s.finished:
            return
        self._checkpoint()
        s = self._s
        if self.is_last_question:
            s.finished = True
        else:
            self._s = _RoundState(index=s.index + 1, scores=s.scores, multiplier=s.multiplier)
        self._changed()

    def undo(self) -> None:
        if self._history:
            self._s = self._history.pop()
            self._changed()
