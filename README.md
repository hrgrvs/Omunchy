# Omunchy

Math arcade for grades 2–5. Munch the numbers that match the rule; dodge Troggles. The title screen uses an animated blocky **OMUNCHY** logo (wave, pop-in, color cycle) — no ASCII doodles.

The board starts at **4×5** and grows every two levels up to **6×8**. Each mode+level plays the same way every time: same rule, same board size, same Troggle mix, and the same number layout.

Modes (pick one on the title screen):

- **Multiples** — munch multiples of 2 through 20, in order
- **Factors** — munch the factors of a number up to 36
- **Primes** — munch small primes through 29
- **Equals** — munch expressions that equal the target
- **Pairings** — grab one number (Space), carry it, then Space on a partner that **adds up to the level target**. Early levels make **10** (1+9, 2+8, … 5+5), then **100**, then **1000**. A wrong pair drops the number you were carrying and does **not** cost a life (Troggles still do). Clear the board by eating every complementary pair.

Every three cleared levels you pick a wearable from a short list (hat, crown, cape, glasses, monocle, mustache, cane, or shoes). One item per spot — a new hat replaces the old hat, but you can stack different spots. Gear lasts for the current run.

Open **Troggles** from the title screen or the pause menu to see each type with its sprite and a short description. Troggles unlock slowly and move at a kid-fair pace:

- **Wander** — walks around at random
- **Chase** — follows you (with gaps so you can escape)
- **Fire-breath** — lights the single square in front of it
- **Exploder** — pops if you stand on a side-adjacent square (up/down/left/right; diagonal is safe), after a short warning
- **Hunter** — eats other Troggles; still hurts you on contact

Starts **fullscreen** on a 16:9 logical frame (1280×720) so it fills a typical laptop. Pixel art scales with nearest-neighbor / `SCALED` letterboxing. Press **F11** for a window, **Esc** or **Q** on the title screen to quit. Same on Mac and Omarchy.

## Install on Mac

Needs **Python 3.10+** and **pygame** from pip. Homebrew Python or a [python.org](https://www.python.org/downloads/) installer is fine. If `python3` is missing:

```bash
brew install python
```

Then:

```bash
git clone https://github.com/hrgrvs/Omunchy.git
cd Omunchy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m omunchy
```

Fullscreen, **F11**, and **Esc** work the same as on Omarchy: the game starts fullscreen, **F11** toggles a window, and **Esc** or **Q** on the title screen quits.

Next time (from the clone, with the venv active):

```bash
cd ~/Omunchy
source .venv/bin/activate
python -m omunchy
```

(If you cloned somewhere else, `cd` to that folder instead.)

### Optional: `./play`

```bash
./play
```

Uses system pygame when available, otherwise sets up a venv.

## Install on Omarchy

**1. Install the tools** (fixes `command not found`):

```bash
sudo pacman -S --needed git python python-pygame
```

**2. Clone and run:**

```bash
git clone https://github.com/hrgrvs/Omunchy.git
cd Omunchy
python -m omunchy
```

Next time:

```bash
cd ~/Omunchy
python -m omunchy
```

(If you cloned somewhere else, `cd` to that folder instead.)

### Optional: `./play`

```bash
./play
```

Uses system pygame when available, otherwise sets up a venv. Prefer `python -m omunchy` after the pacman install above.

## Controls

- Arrows / WASD / IJKL — tap to move one cell (also pick a wearable). Every tap steps immediately; holding does not walk.
- Space — munch (in Pairings: grab, then eat a pair; or confirm a wearable / skip get-ready, level-clear, and celebration)
- Esc — leave or unstick the current screen (quit on the title screen; pause while playing; skip a wearable / celebration / level-clear; close Troggles)
- F11 — toggle fullscreen / window
- M — mute
- T — Troggles page (title / pause)
- Q — quit (title / game over / pause → title)

## If the window doesn’t open

```bash
SDL_VIDEODRIVER=wayland python -m omunchy
# or
SDL_VIDEODRIVER=x11 python -m omunchy
```

## License

[MIT](LICENSE) — Copyright (c) Damon Hargraves. Full text is in [`LICENSE`](LICENSE).
