# Omunchy

Math arcade for grades 2–5. The **game** is **Omunchy**; the **character** you steer is **Munchy**. Munch the numbers that match the rule; dodge Troggles. The title screen uses an animated blocky **OMUNCHY** logo (wave, pop-in, color cycle) — no ASCII doodles.

The board starts at **4×5** and grows every two levels up to **6×8**. Each mode+level plays the same way every time: same rule, same board size, same Troggle mix, and the same number layout.

Modes (pick one on the title screen):

- **Multiples** — munch multiples of 2 through 20, in order
- **Factors** — munch the factors of a number up to 36
- **Primes** — munch small primes through 29
- **Equals** — munch expressions that equal the target
- **Pairings** — grab one number (Space), carry it, then Space on a partner that **adds up to the level target**. Early levels make **10** (1+9, 2+8, … 5+5), then **100**, then **1000**. A wrong pair drops the number you were carrying and does **not** cost a life (Troggles still do). Clear the board by eating every complementary pair.

Every three cleared levels you pick a wearable from a short list (hat, crown, cape, glasses, monocle, mustache, cane, or shoes). One item per spot — a new hat replaces the old hat, but you can stack different spots. Gear lasts for the current run.

Open **Troggles** from the title screen or the pause menu to see each type with its sprite and a short description. Troggles unlock slowly and move at a kid-fair pace:

- **Wander** — walks around at random; bumps Munchy back instead of costing a life
- **Chase** — follows Munchy (with gaps so you can escape); big eyes track him
- **Fire-breath** — lights the square in front; up to two cells stay burning (oldest goes out first). Standing on fire costs a life
- **Exploder** — pops if Munchy stands on a side-adjacent square (up/down/left/right; diagonal is safe), after a short warning
- **Hunter** — eats other Troggles; still hurts Munchy on contact

Starts **fullscreen** on a 16:9 logical frame (1280×720) so it fills a typical laptop. Pixel art scales with nearest-neighbor / `SCALED` letterboxing. Press **F11** for a window, **Esc** or **Q** on the title screen to quit.

## Install and run

Needs **Python 3.10+**, **git**, and **pygame**. First launch from a git clone will try to **auto-update** (needs git and a working network — see [Updates](#updates)).

### Linux

#### Omarchy / Arch (`pacman`)

```bash
sudo pacman -S --needed git python python-pygame
git clone https://github.com/hrgrvs/Omunchy.git
cd Omunchy
python -m omunchy
```

If `cd Omunchy` fails because [zoxide](https://github.com/ajeetdsouza/zoxide) is wrapping `cd` on Omarchy, use the shell builtin:

```bash
builtin cd Omunchy
```

Next time:

```bash
cd ~/Omunchy
# or: builtin cd ~/Omunchy
python -m omunchy
```

(If you cloned somewhere else, `cd` to that folder instead.)

#### Any Linux (pip + venv)

Install git and Python 3.10+ from your distro, then:

```bash
git clone https://github.com/hrgrvs/Omunchy.git
cd Omunchy
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m omunchy
```

Next time (from the clone, with the venv active):

```bash
cd ~/Omunchy
source .venv/bin/activate
python -m omunchy
```

### macOS

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

Fullscreen, **F11**, and **Esc** work the same as on Linux: the game starts fullscreen, **F11** toggles a window, and **Esc** or **Q** on the title screen quits.

Next time (from the clone, with the venv active):

```bash
cd ~/Omunchy
source .venv/bin/activate
python -m omunchy
```

(If you cloned somewhere else, `cd` to that folder instead.)

### Windows

Install **Git** and **Python 3.10+** (tick **Add python.exe to PATH** on the python.org installer):

- Download [Git](https://git-scm.com/download/win) and [Python](https://www.python.org/downloads/), or
- With [winget](https://learn.microsoft.com/windows/package-manager/winget/):

```powershell
winget install --id Git.Git -e --source winget
winget install --id Python.Python.3.12 -e --source winget
```

Close and reopen the terminal after installing so `git` and `python` are on PATH. Then, in **PowerShell** or **Command Prompt**:

```powershell
git clone https://github.com/hrgrvs/Omunchy.git
cd Omunchy
python -m venv .venv
```

Activate the venv:

```powershell
# PowerShell
.\.venv\Scripts\Activate.ps1
```

```cmd
REM Command Prompt
.venv\Scripts\activate.bat
```

If PowerShell blocks the activate script, either run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or skip activate and call `.venv\Scripts\python.exe` below.

Then:

```powershell
pip install -r requirements.txt
python -m omunchy
```

Next time (from the clone, with the venv active):

```powershell
cd Omunchy
.\.venv\Scripts\Activate.ps1
python -m omunchy
```

### Optional: `./play` (Linux and macOS)

```bash
./play
```

Uses system pygame when available, otherwise sets up a venv. On Omarchy/Arch after the pacman install above, prefer `python -m omunchy`.

## Updates

Each launch from a **git clone** checks `origin` for updates (prefers `main`) and fast-forwards when it can (`git pull --ff-only`). A short **splash** shows Munchy running across a 16:9 screen and a status bar (checking → updating → ready, or offline / couldn't update). If the check finishes quickly the splash still appears for a moment, then the title screen. If files changed, the process restarts itself so the new code is what you play — that second start skips the splash. That needs **git** and a working **network**; the check gives up after about 12 seconds so a hung network cannot freeze startup.

If you are offline, git is missing, this is not a clone, or your local copy has diverged from `origin`, the game still starts with the current code. It never force-pushes or throws away local changes.

First-time install is still a normal `git clone` (see Linux / macOS / Windows above). Zip copies without a `.git` folder skip the check.

To skip (tests, or a locked copy):

```bash
OMUNCHY_SKIP_UPDATE=1 python -m omunchy
```

On Windows Command Prompt: `set OMUNCHY_SKIP_UPDATE=1` then `python -m omunchy`. In PowerShell: `$env:OMUNCHY_SKIP_UPDATE=1; python -m omunchy`.

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
