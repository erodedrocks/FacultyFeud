# Faculty Feud

A Family-Feud-style game show for SCS Day, rebuilt in Python (PySide6) from the
original [Java version](https://github.com/scsday/FacultyFeud).

Two windows open:

- **Board**: the contestant-facing display for the projector. If a second screen
  is connected, it opens there in fullscreen automatically.
- **Moderator console**: the host's controls, with every answer and point value visible.

## Run

```sh
uv run faculty-feud                      # bundled 2022 questions
uv run faculty-feud path/to/questions.csv
uv run faculty-feud --mute
```

(Without uv: `pip install -e .` then `faculty-feud`, or `python -m faculty_feud`.)

## Moderator controls

| Key | Action |
| --- | --- |
| `1`–`8` | Reveal answer (plays the ding, banks points) |
| `Q` | Show the question on the board |
| `X` | Strike (up to 3) |
| `B` | Buzzer only: flash an X without counting a strike |
| `←` / `→` | Award the bank to the left / right team |
| `N` | Next question (asks first if points are still unawarded) |
| `⌘Z` / `Ctrl+Z` | Undo |
| `F` | Toggle board fullscreen (also `F`, `Esc` or double-click on the board) |

The **Points** toggle (1×/2×/3×) sets the multiplier for the round.

After three strikes, revealing answers no longer adds to the bank, the same as the original.

## Question file format

```csv
Team One,Team Two
What is your favorite data structure?,TREES,32,HASH MAP,15,LINKED LISTS,11
"Questions, with commas, need quotes",ANSWER,40,ANOTHER,12
```

Line 1 names the two teams. Each row after that has a question followed by up to
8 `answer,points` pairs. Blank trailing cells are ignored.

## Develop

```sh
uv run pytest
```
