# Omunchy

Math arcade for grades 2–5. Munch the numbers that match the rule; dodge Troggles. The title screen uses an animated blocky **OMUNCHY** logo (wave, pop-in, color cycle) — no ASCII doodles.

The board starts at **4×5** and grows every two levels up to **6×8**. Each mode+level plays the same way every time: same rule, same board size, same Troggle mix, and the same number layout.

Every three cleared levels you pick a wearable from a short list (hat, crown, cape, glasses, monocle, mustache, cane, or shoes). One item per spot — a new hat replaces the old hat, but you can stack different spots. Gear lasts for the current run.

Open **Troggles** from the title screen or the pause menu to see each type with its sprite and a short description. Troggles unlock slowly and move at a kid-fair pace:

- **Wander** — walks around at random
- **Chase** — follows you (with gaps so you can escape)
- **Fire-breath** — lights the single square in front of it
- **Exploder** — pops if you stand on a side-adjacent square (up/down/left/right; diagonal is safe), after a short warning
- **Hunter** — eats other Troggles; still hurts you on contact

Starts **fullscreen** on a 16:9 logical frame (1280×720) so it fills a typical laptop. Pixel art scales with nearest-neighbor / `SCALED` letterboxing. Press **F11** for a window, **Esc** or **Q** on the title screen to quit.

## Install on Omarchy

**1. Install the tools** (fixes `command not found`):

```bash
sudo pacman -S --needed git python python-pygame
```

**2. Clone and run:**

```bash
git clone https://github.com/hrgrvs/Omunch.git
cd Omunch
python -m omunchy
```

Next time:

```bash
cd ~/Omunch
python -m omunchy
```

(If you cloned somewhere else, `cd` to that folder instead.)

The GitHub repository is still named `Omunch`; the game itself is **Omunchy**.

### Optional: `./play`

```bash
./play
```

Uses system pygame when available, otherwise sets up a venv. Prefer `python -m omunchy` after the pacman install above.

## Controls

- Arrows / WASD / IJKL — move (also pick a wearable)
- Space — munch (or confirm a wearable)
- Esc — pause (quit from the title screen; skip a wearable)
- F11 — toggle fullscreen / window
- M — mute
- T — Troggles page (title / pause)
- Q — quit (title / game over)

## If the window doesn’t open

```bash
SDL_VIDEODRIVER=wayland python -m omunchy
# or
SDL_VIDEODRIVER=x11 python -m omunchy
```

## License

[MIT](LICENSE) — Copyright (c) Damon Hargraves. Full text is in [`LICENSE`](LICENSE).
