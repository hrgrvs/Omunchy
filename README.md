# Omunch

Math arcade for grades 2–5. Munch the numbers that match the rule; dodge Troggles.

## Install on Omarchy

**1. Install the tools** (fixes `command not found`):

```bash
sudo pacman -S --needed git python python-pygame
```

**2. Clone and run:**

```bash
git clone https://github.com/hrgrvs/Omunch.git
cd Omunch
python -m omunch
```

Next time:

```bash
cd ~/Omunch
python -m omunch
```

(If you cloned somewhere else, `cd` to that folder instead.)

### Optional: `./play`

```bash
./play
```

Uses system pygame when available, otherwise sets up a venv. Prefer `python -m omunch` after the pacman install above.

## Controls

- Arrows / WASD / IJKL — move
- Space — munch
- Esc — pause
- M — mute

## If the window doesn’t open

```bash
SDL_VIDEODRIVER=wayland python -m omunch
# or
SDL_VIDEODRIVER=x11 python -m omunch
```

## License

MIT
