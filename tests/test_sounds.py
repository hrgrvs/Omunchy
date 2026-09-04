import unittest
import wave
from pathlib import Path

from omunch.audio import REQUIRED_SOUNDS, SOUNDS_DIR

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


if __name__ == "__main__":
    unittest.main()