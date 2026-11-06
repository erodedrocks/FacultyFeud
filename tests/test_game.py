from pathlib import Path

import pytest

from faculty_feud.game import Answer, Game, Question, load_csv

DATA = Path(__file__).parent.parent / "faculty_feud" / "data"


def make_game():
    return Game(("A", "B"), [
        Question("Q1", (Answer("x", 30), Answer("y", 20), Answer("z", 10))),
        Question("Q2", (Answer("p", 50),)),
    ])


def test_bundled_files_load():
    for path in DATA.glob("*.csv"):
        teams, questions = load_csv(path)
        assert len(teams) == 2 and questions


def test_csv_ignores_blank_cells_and_whitespace(tmp_path):
    f = tmp_path / "q.csv"
    f.write_text('Red,Blue\n"Name a, thing", TREES ,32,,,\n')
    teams, (q,) = load_csv(f)
    assert teams == ("Red", "Blue")
    assert q.text == "Name a, thing"
    assert q.answers == (Answer("TREES", 32),)


def test_csv_reports_bad_points(tmp_path):
    f = tmp_path / "q.csv"
    f.write_text("A,B\nQ,ans,lots\n")
    with pytest.raises(ValueError, match=":2:"):
        load_csv(f)


def test_reveal_banks_points_and_award_moves_them():
    g = make_game()
    assert g.reveal(0) and not g.reveal(0)
    g.reveal(2)
    assert g.bank == 40
    g.award(1)
    assert g.scores == (0, 40) and g.bank == 0
    g.award(0)  # second award is ignored
    assert g.scores == (0, 40)


def test_no_points_after_three_strikes():
    g = make_game()
    for _ in range(4):
        g.strike()
    assert g.strikes == 3
    g.reveal(0)
    assert g.bank == 0 and g.is_revealed(0)


def test_multiplier_applies_to_bank():
    g = make_game()
    g.set_multiplier(2)
    g.reveal(0)
    assert g.bank == 60
    g.award(0)
    assert g.scores == (60, 0)


def test_next_question_resets_round_and_finishes():
    g = make_game()
    g.reveal(0)
    g.strike()
    g.show_question()
    g.next_question()
    assert (g.round_number, g.strikes, g.bank, g.question_shown) == (2, 0, 0, False)
    assert not g.is_revealed(0)
    g.next_question()
    assert g.finished
    assert g.question.text == "Q2"  # board still has something valid to read


def test_undo_restores_previous_state():
    g = make_game()
    g.reveal(0)
    g.award(0)
    g.undo()
    assert g.scores == (0, 0) and g.bank == 30 and not g.awarded
    g.undo()
    assert not g.is_revealed(0) and not g.can_undo


def test_listeners_fire_on_change():
    g = make_game()
    calls = []
    g.subscribe(lambda: calls.append(1))
    g.reveal(0)
    g.reveal(0)  # no-op, no notification
    assert len(calls) == 1
