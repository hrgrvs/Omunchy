import unittest
import wave
from pathlib import Path

from omunchy.audio import REQUIRED_SOUNDS, SOUNDS_DIR

ALL = REQUIRED_SOUNDS + ("bg_loop",)


class SoundAssetTests(unittest.TestCase):
    def test_wav_assets_exist_and_are_valid(self) -> None:
        for name in ALL:
            path = SOUNDS_DIR / f"{name}.wav"
            self.assertTrue(path.is_file(), f"missing {path}")
            with wave.open(str(path), "rb") as wav:
                self.assertEqual(wav.getnchannels(), 1)
                self.assertEqual(wav.getsampwidth(), 2)
                self.assertGreater(wav.getnframes(), 200)
                self.assertGreater(path.stat().st_size, 400)

    def test_hit_is_longer_than_the_old_short_buzz(self) -> None:
        hit = SOUNDS_DIR / "hit.wav"
        wrong = SOUNDS_DIR / "wrong.wav"
        with wave.open(str(hit), "rb") as wav:
            hit_frames = wav.getnframes()
            rate = wav.getframerate()
        with wave.open(str(wrong), "rb") as wav:
            wrong_frames = wav.getnframes()
        self.assertGreater(hit_frames / rate, 0.50)
        self.assertGreater(hit_frames, wrong_frames)

    def test_each_troggle_has_a_distinct_spawn_cue(self) -> None:
        names = (
            "spawn_wander",
            "spawn_chase",
            "spawn_fire",
            "spawn_exploder",
            "spawn_hunter",
        )
        blobs: list[bytes] = []
        for name in names:
            self.assertIn(name, REQUIRED_SOUNDS)
            path = SOUNDS_DIR / f"{name}.wav"
            blobs.append(path.read_bytes())
        self.assertEqual(len(set(blobs)), len(names))


if __name__ == "__main__":
    unittest.main()