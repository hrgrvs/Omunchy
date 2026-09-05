#!/usr/bin/env python3
"""Generate committed WAV assets for Omunchy (no runtime downloads)."""

from __future__ import annotations

import math
import random
import struct
import wave
from pathlib import Path

SAMPLE_RATE = 22050
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "omunchy" / "assets" / "sounds"


def clamp(value: float, lo: float = -1.0, hi: float = 1.0) -> float:
    return lo if value < lo else hi if value > hi else value


def midi_freq(note: float) -> float:
    return 440.0 * (2.0 ** ((note - 69.0) / 12.0))


def envelope(index: int, length: int, attack: float = 0.01, release: float = 0.08) -> float:
    if length <= 0:
        return 0.0
    t = index / SAMPLE_RATE
    dur = length / SAMPLE_RATE
    if t < attack:
        return t / attack if attack > 0 else 1.0
    if t > dur - release and release > 0:
        return max(0.0, (dur - t) / release)
    return 1.0


def sine(phase: float) -> float:
    return math.sin(phase)


def square(phase: float) -> float:
    return 1.0 if math.sin(phase) >= 0 else -1.0


def triangle(phase: float) -> float:
    return 2.0 * abs(2.0 * ((phase / (2 * math.pi)) % 1.0) - 1.0) - 1.0


def noise(rng: random.Random) -> float:
    return rng.uniform(-1.0, 1.0)


def mix_to_samples(frames: list[float]) -> list[float]:
    peak = max((abs(s) for s in frames), default=1.0)
    if peak < 1e-6:
        return frames
    gain = 0.92 / peak if peak > 0.92 else 1.0
    return [clamp(s * gain) for s in frames]


def write_wav(path: Path, frames: list[float]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = mix_to_samples(frames)
    with wave.open(str(path), "w") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(b"".join(struct.pack("<h", int(s * 32767)) for s in samples))


def tone(
    freq: float,
    duration: float,
    *,
    wave_fn=sine,
    volume: float = 0.5,
    attack: float = 0.012,
    release: float = 0.06,
    slide: float = 0.0,
) -> list[float]:
    length = int(duration * SAMPLE_RATE)
    frames: list[float] = []
    phase = 0.0
    for i in range(length):
        t = i / max(1, length - 1)
        f = freq * (1.0 + slide * t)
        phase += 2 * math.pi * f / SAMPLE_RATE
        frames.append(wave_fn(phase) * volume * envelope(i, length, attack, release))
    return frames


def rest(duration: float) -> list[float]:
    return [0.0] * int(duration * SAMPLE_RATE)


def concat(*parts: list[float]) -> list[float]:
    out: list[float] = []
    for part in parts:
        out.extend(part)
    return out


def overlay(*layers: list[float]) -> list[float]:
    length = max((len(layer) for layer in layers), default=0)
    out = [0.0] * length
    for layer in layers:
        for i, sample in enumerate(layer):
            out[i] += sample
    return out


def crunch(duration: float = 0.07, volume: float = 0.55) -> list[float]:
    rng = random.Random(11)
    length = int(duration * SAMPLE_RATE)
    frames: list[float] = []
    for i in range(length):
        n = noise(rng)
        # Cheap band-limit: mix previous-ish by attenuating highs via running average.
        env = envelope(i, length, 0.004, 0.03)
        frames.append(n * volume * env)
    # Soft low-pass
    filtered = [0.0] * length
    acc = 0.0
    for i, sample in enumerate(frames):
        acc = acc * 0.55 + sample * 0.45
        filtered[i] = acc
    return filtered


def make_correct() -> list[float]:
    chomp = overlay(
        crunch(0.08, 0.7),
        tone(140, 0.09, wave_fn=triangle, volume=0.28, attack=0.002, release=0.05, slide=-0.35),
    )
    ding = overlay(
        tone(midi_freq(76), 0.11, volume=0.42, attack=0.005, release=0.08),  # E5
        tone(midi_freq(79), 0.16, volume=0.38, attack=0.008, release=0.1),  # G5
    )
    sparkle = tone(midi_freq(88), 0.12, volume=0.16, attack=0.002, release=0.1)
    return concat(chomp, rest(0.02), overlay(ding, concat(rest(0.03), sparkle)))


def make_wrong() -> list[float]:
    buzz = overlay(
        tone(180, 0.28, wave_fn=square, volume=0.28, attack=0.004, release=0.08, slide=-0.08),
        tone(191, 0.28, wave_fn=square, volume=0.22, attack=0.004, release=0.08, slide=-0.05),
        tone(90, 0.22, wave_fn=triangle, volume=0.2, attack=0.006, release=0.1),
    )
    return buzz


def make_hit() -> list[float]:
    """Longer, louder 'gotcha' when a Troggle/fire eats Munchy — cartoon, not scary."""
    impact = overlay(
        crunch(0.24, 0.88),
        tone(68, 0.40, wave_fn=sine, volume=0.74, attack=0.002, release=0.24, slide=-0.58),
        tone(132, 0.26, wave_fn=triangle, volume=0.42, attack=0.002, release=0.16, slide=-0.62),
        tone(210, 0.12, wave_fn=square, volume=0.16, attack=0.002, release=0.08, slide=-0.4),
    )
    oof = overlay(
        tone(196, 0.22, wave_fn=square, volume=0.20, attack=0.012, release=0.14, slide=-0.16),
        tone(147, 0.30, wave_fn=triangle, volume=0.34, attack=0.014, release=0.18, slide=-0.20),
        tone(98, 0.36, wave_fn=sine, volume=0.30, attack=0.02, release=0.20, slide=-0.10),
    )
    wobble = overlay(
        tone(midi_freq(55), 0.32, wave_fn=triangle, volume=0.20, attack=0.02, release=0.22, slide=-0.08),
        tone(midi_freq(62), 0.24, volume=0.14, attack=0.03, release=0.18),
    )
    return concat(impact, rest(0.05), overlay(oof, concat(rest(0.06), wobble)))


def make_spawn_wander() -> list[float]:
    """Curious woodblock toot — small wanderer is nearby."""
    return overlay(
        tone(midi_freq(72), 0.10, wave_fn=triangle, volume=0.36, attack=0.004, release=0.07),
        concat(rest(0.08), tone(midi_freq(79), 0.14, wave_fn=triangle, volume=0.30, attack=0.006, release=0.10)),
    )


def make_spawn_chase() -> list[float]:
    """Quick kid-friendly 'uh-oh' as the chaser appears."""
    return concat(
        tone(midi_freq(76), 0.09, wave_fn=square, volume=0.22, attack=0.004, release=0.05),
        tone(midi_freq(71), 0.12, wave_fn=square, volume=0.20, attack=0.004, release=0.07),
        tone(midi_freq(67), 0.16, wave_fn=triangle, volume=0.24, attack=0.006, release=0.10),
    )


def make_spawn_fire() -> list[float]:
    """Soft whoosh + sparkle — fire-breath is coming."""
    return overlay(
        crunch(0.20, 0.26),
        tone(220, 0.22, wave_fn=sine, volume=0.16, attack=0.04, release=0.12, slide=0.35),
        concat(rest(0.10), tone(midi_freq(84), 0.12, volume=0.18, attack=0.002, release=0.10)),
        concat(rest(0.16), tone(midi_freq(88), 0.10, volume=0.12, attack=0.002, release=0.08)),
    )


def make_spawn_exploder() -> list[float]:
    """Fuse ticks — exploder is about to hop on."""
    tick = lambda freq, dur: tone(freq, dur, wave_fn=square, volume=0.18, attack=0.002, release=0.03)
    return concat(
        tick(880, 0.05),
        rest(0.07),
        tick(880, 0.05),
        rest(0.07),
        tick(988, 0.06),
        rest(0.05),
        overlay(
            tone(midi_freq(60), 0.14, wave_fn=triangle, volume=0.22, attack=0.004, release=0.08),
            tone(midi_freq(72), 0.12, volume=0.14, attack=0.004, release=0.08),
        ),
    )


def make_spawn_hunter() -> list[float]:
    """Low gulp / boing — hunter incoming."""
    return overlay(
        tone(90, 0.18, wave_fn=sine, volume=0.40, attack=0.008, release=0.10, slide=-0.25),
        tone(140, 0.14, wave_fn=triangle, volume=0.22, attack=0.01, release=0.08, slide=-0.30),
        concat(
            rest(0.12),
            tone(midi_freq(55), 0.20, wave_fn=triangle, volume=0.20, attack=0.02, release=0.12, slide=0.15),
        ),
    )


def make_level_clear() -> list[float]:
    notes = [72, 76, 79, 84]  # C5 E5 G5 C6
    cursor = 0.0
    layers: list[list[float]] = []
    for i, note in enumerate(notes):
        start = concat(rest(cursor), tone(midi_freq(note), 0.18, volume=0.36, attack=0.008, release=0.1))
        layers.append(start)
        if i == len(notes) - 1:
            layers.append(concat(rest(cursor), tone(midi_freq(note + 12), 0.28, volume=0.14, attack=0.01, release=0.16)))
        cursor += 0.12
    return overlay(*layers)


def make_game_over() -> list[float]:
    notes = [(67, 0.22), (63, 0.24), (60, 0.28), (55, 0.46)]  # G4 Eb4 C4 G3
    cursor = 0.0
    layers: list[list[float]] = []
    for note, dur in notes:
        layers.append(concat(rest(cursor), tone(midi_freq(note), dur, volume=0.34, attack=0.02, release=0.14)))
        layers.append(
            concat(rest(cursor), tone(midi_freq(note) * 0.5, dur, wave_fn=triangle, volume=0.16, attack=0.02, release=0.16))
        )
        cursor += dur * 0.82
    return overlay(*layers)


def make_title() -> list[float]:
    # Short educational-software jingle: C4 G4 E5 C5, then a little bounce.
    melody = [(60, 0.14), (67, 0.14), (76, 0.16), (72, 0.22), (74, 0.12), (76, 0.28)]
    cursor = 0.0
    layers: list[list[float]] = []
    bass = [(48, 0.28), (43, 0.28), (45, 0.40)]
    bcur = 0.0
    for note, dur in melody:
        layers.append(concat(rest(cursor), tone(midi_freq(note), dur, volume=0.34, attack=0.01, release=0.08)))
        layers.append(
            concat(
                rest(cursor),
                tone(midi_freq(note + 12), dur * 0.7, volume=0.1, attack=0.008, release=0.08),
            )
        )
        cursor += dur * 0.92
    for note, dur in bass:
        layers.append(
            concat(rest(bcur), tone(midi_freq(note), dur, wave_fn=triangle, volume=0.14, attack=0.02, release=0.12))
        )
        bcur += dur
    return overlay(*layers)



def make_celebrate() -> list[float]:
    # Short cheerful fanfare for milestone celebrations.
    notes = [(72, 0.12), (76, 0.12), (79, 0.12), (84, 0.28)]
    layers: list[list[float]] = []
    cursor = 0.0
    for note, dur in notes:
        layers.append(
            concat(
                rest(cursor),
                tone(midi_freq(note), dur, volume=0.22, attack=0.01, release=0.08),
                tone(midi_freq(note + 7), dur * 0.8, volume=0.1, attack=0.01, release=0.08),
            )
        )
        cursor += dur * 0.85
    return overlay(*layers)

def make_bg_loop() -> list[float]:
    # Quiet 2-bar C-major arpeggio, loop-friendly (starts/ends near zero).
    pattern = [60, 67, 72, 76, 72, 67, 64, 67]
    step = 0.25
    layers: list[list[float]] = []
    for i, note in enumerate(pattern):
        start = i * step
        layers.append(
            concat(
                rest(start),
                tone(midi_freq(note), 0.22, volume=0.055, attack=0.03, release=0.12),
            )
        )
        if i % 4 == 0:
            layers.append(
                concat(
                    rest(start),
                    tone(midi_freq(note - 12), 0.9, wave_fn=triangle, volume=0.03, attack=0.05, release=0.3),
                )
            )
    # Pad to exact 2.0s for seamless looping
    frames = overlay(*layers)
    target = int(2.0 * SAMPLE_RATE)
    if len(frames) < target:
        frames.extend([0.0] * (target - len(frames)))
    else:
        frames = frames[:target]
    # Fade edges slightly so the loop does not click
    fade = int(0.02 * SAMPLE_RATE)
    for i in range(fade):
        frames[i] *= i / fade
        frames[-1 - i] *= i / fade
    return frames


SOUNDS = {
    "correct.wav": make_correct,
    "wrong.wav": make_wrong,
    "hit.wav": make_hit,
    "level_clear.wav": make_level_clear,
    "game_over.wav": make_game_over,
    "title.wav": make_title,
    "celebrate.wav": make_celebrate,
    "bg_loop.wav": make_bg_loop,
    "spawn_wander.wav": make_spawn_wander,
    "spawn_chase.wav": make_spawn_chase,
    "spawn_fire.wav": make_spawn_fire,
    "spawn_exploder.wav": make_spawn_exploder,
    "spawn_hunter.wav": make_spawn_hunter,
}


def generate_all(output_dir: Path = OUTPUT_DIR) -> list[Path]:
    written: list[Path] = []
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, factory in SOUNDS.items():
        path = output_dir / name
        write_wav(path, factory())
        written.append(path)
    return written


if __name__ == "__main__":
    paths = generate_all()
    for path in paths:
        print(f"wrote {path} ({path.stat().st_size} bytes)")