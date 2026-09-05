# Omunch

Math arcade for grades 2–5. Munch the numbers that match the rule; dodge Troggles.

## Install (Omarchy)

```bash
git clone https://github.com/hrgrvs/Omunch.git
cd Omunch
./play
```

That’s it. `./play` creates a venv, installs pygame once, and launches the game. Run `./play` again anytime.

## Controls

- Arrows / WASD / IJKL — move
- Space — munch
- Esc — pause
- M — mute

## Wayland note

If the window doesn’t open:

```bash
SDL_VIDEODRIVER=wayland ./play
# or
SDL_VIDEODRIVER=x11 ./play
```

## License

MIT
