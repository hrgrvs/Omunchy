"""Load shipped WAV assets and play them. Survive missing audio devices."""

from __future__ import annotations

from pathlib import Path

SOUNDS_DIR = Path(__file__).resolve().parent / "assets" / "sounds"

REQUIRED_SOUNDS = (
    "correct",
    "wrong",
    "hit",
    "level_clear",
    "game_over",
    "title",
    "celebrate",
)

BG_LOOP = "bg_loop"
BG_VOLUME = 0.18
SFX_VOLUME = 0.72


class Audio:
    """Session-muteable mixer wrapper. If init fails, every call is a no-op."""

    def __init__(self) -> None:
        self.available = False
        self.muted = False
        self._sounds: dict[str, object] = {}
        self._bg = None
        self._mixer = None
        self._init_mixer()

    def _init_mixer(self) -> None:
        try:
            import pygame

            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
            self._mixer = pygame.mixer
            self.available = True
        except Exception:
            self.available = False
            self._mixer = None
            return
        self._load()

    def _load(self) -> None:
        assert self._mixer is not None
        for name in REQUIRED_SOUNDS + (BG_LOOP,):
            path = SOUNDS_DIR / f"{name}.wav"
            if not path.is_file():
                continue
            try:
                sound = self._mixer.Sound(str(path))
                if name == BG_LOOP:
                    sound.set_volume(BG_VOLUME)
                    self._bg = sound
                else:
                    sound.set_volume(SFX_VOLUME)
                    self._sounds[name] = sound
            except Exception:
                continue

    def play(self, name: str) -> None:
        if not self.available or self.muted:
            return
        sound = self._sounds.get(name)
        if sound is None:
            return
        try:
            sound.play()
        except Exception:
            pass

    def play_bg(self) -> None:
        if not self.available or self.muted or self._bg is None:
            return
        try:
            self._bg.play(loops=-1)
        except Exception:
            pass

    def stop_bg(self) -> None:
        if self._bg is None:
            return
        try:
            self._bg.stop()
        except Exception:
            pass

    def stop_all(self) -> None:
        if not self.available or self._mixer is None:
            return
        try:
            self._mixer.stop()
        except Exception:
            pass

    def toggle_mute(self) -> bool:
        self.muted = not self.muted
        if self.muted:
            self.stop_all()
        else:
            self.play_bg()
        return self.muted

    def shutdown(self) -> None:
        self.stop_all()
        if self._mixer is None:
            return
        try:
            self._mixer.quit()
        except Exception:
            pass