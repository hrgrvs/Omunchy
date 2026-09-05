# Omunch

Math arcade for grades 2–5. Munch the numbers that match the rule; dodge Troggles.

## Install on Omarchy

**Option A — simplest (recommended)**

```bash
sudo pacman -S --needed git python python-pygame
git clone https://github.com/hrgrvs/Omunch.git
cd Omunch
python -m omunch
```

**Option B — one script (venv if needed)**

```bash
git clone https://github.com/hrgrvs/Omunch.git
cd Omunch
./play
```

`./play` prints what it’s doing. First run can take a minute while pygame installs.

Later: `cd ~/Omunch && ./play` (or `python -m omunch` if you used Option A).

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
