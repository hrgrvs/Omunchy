from pathlib import Path
import unittest

from omunchy.constants import TITLE
from omunchy.title_art import (
    CONTROLS_HINT,
    LICENSE_LINE,
    TAGLINE,
    TITLE_WORD,
    glyph,
    letter_color,
    letter_poses,
    logo_width,
)


class TitleArtTests(unittest.TestCase):
    def test_logo_is_blocky_omunchy_not_ascii_doodles(self) -> None:
        self.assertEqual(TITLE, "Omunchy")
        self.assertEqual(TITLE_WORD, "OMUNCHY")
        for ch in TITLE_WORD:
            rows = glyph(ch)
            self.assertEqual(len(rows), 7)
            self.assertTrue(all(len(row) == 7 for row in rows))
            self.assertIn("X", "".join(rows))
        self.assertLess(logo_width(), 1280)
        self.assertIn("2–5", TAGLINE)
        self.assertIn("Esc", CONTROLS_HINT)
        self.assertIn("F11", CONTROLS_HINT)
        self.assertIn("Damon Hargraves", LICENSE_LINE)
        self.assertIn("MIT", LICENSE_LINE)
        self.assertNotEqual(TITLE, "Omunch")

    def test_letters_pop_in_then_wave(self) -> None:
        early = letter_poses(0.0)
        self.assertTrue(early[0].visible)
        self.assertFalse(early[-1].visible)
        later = letter_poses(1.6)
        self.assertTrue(all(p.visible for p in later))
        self.assertEqual("".join(p.ch for p in later), "OMUNCHY")
        waves = {p.y for p in later}
        self.assertGreater(len(waves), 1)
        self.assertNotEqual(letter_color(0, 0.0), letter_color(3, 1.4))

    def test_no_creature_doodle_constants(self) -> None:
        import omunchy.title_art as art

        self.assertFalse(hasattr(art, "TITLE_DOODLE"))
        self.assertFalse(hasattr(art, "TITLE_BANNER"))

    def test_license_file_is_mit_damon_hargraves(self) -> None:
        text = Path(__file__).resolve().parents[1].joinpath("LICENSE").read_text()
        self.assertTrue(text.startswith("MIT License"))
        self.assertIn("Copyright (c) Damon Hargraves", text)
        self.assertNotIn("Omunchy contributors", text)
        self.assertIn("THE SOFTWARE IS PROVIDED \"AS IS\"", text)


if __name__ == "__main__":
    unittest.main()
