# Omunch

A math arcade for elementary grades 2–5. Pixel-art muncher, number grid, a rule at the top, and wandering Troggles.

Native Linux (Python 3 + pygame). No network after install. Built for Arch / Omarchy (Hyprland / Wayland).

## Play

Munch every cell that matches the rule (Multiples, Factors, Primes, Equals). Wrong munches and Troggle bumps cost a life. Clear the correct answers to advance.

Modes on the title screen: **Multiples**, **Factors**, **Primes**, **Equals**, **Mixed**. Difficulty ramps slowly. Every 3 levels a short celebration plays (Space/Enter to skip).

## Controls

- Arrow keys or WASD — move
- Space — munch
- Esc — pause
- M — mute / unmute
- Enter / Space — confirm / skip celebration

## Install on Omarchy / Arch from Git

```bash
git clone https://github.com/hrgrvs/Omunch.git
cd Omunch
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m omunch
```

Or with system packages:

```bash
sudo pacman -S python python-pip python-pygame
git clone https://github.com/hrgrvs/Omunch.git
cd Omunch
python -m omunch
```

If the window fails to open on Wayland, try:

```bash
SDL_VIDEODRIVER=wayland python -m omunch
# or
SDL_VIDEODRIVER=x11 python -m omunch
```

## Sounds

WAV assets ship in `omunch/assets/sounds/` (correct/wrong munch, Troggle hit, level clear, game over, title, celebration). Mute with **M**. The game still runs if audio init fails.

Regenerate assets:

```bash
python scripts/generate_sounds.py
```

## License

MIT
