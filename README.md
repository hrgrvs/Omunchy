# Omunchy

Math arcade for grades 2–5. Munch the numbers that match the rule; dodge Troggles.

The board starts small (3×4) and grows every two levels up to 6×8. Troggles unlock slowly and move at a kid-fair pace:

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

- Arrows / WASD / IJKL — move
- Space — munch
- Esc — pause (quit from the title screen)
- F11 — toggle fullscreen / window
- M — mute
- Q — quit (title / game over)

## If the window doesn’t open

```bash
SDL_VIDEODRIVER=wayland python -m omunchy
# or
SDL_VIDEODRIVER=x11 python -m omunchy
```

## License

MIT
