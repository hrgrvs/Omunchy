from pathlib import Path
import unittest

from omunchy.constants import TITLE
from omunchy.title_art import CONTROLS_HINT, LICENSE_LINE, TAGLINE, TITLE_BANNER, TITLE_DOODLE


class TitleArtTests(unittest.TestCase):
    def test_banner_spells_omunchy(self) -> None:
        self.assertEqual(TITLE, "Omunchy")
        joined = "\n".join(TITLE_BANNER)
        self.assertGreaterEqual(len(TITLE_BANNER), 5)
        self.assertLessEqual(max(len(line) for line in TITLE_BANNER), 72)
        self.assertIn("██", joined)
        self.assertTrue(any("you" in line.lower() or "munch" in line.lower() for line in TITLE_DOODLE))
        self.assertIn("2–5", TAGLINE)
        self.assertIn("Esc", CONTROLS_HINT)
        self.assertIn("F11", CONTROLS_HINT)
        self.assertIn("Damon Hargraves", LICENSE_LINE)
        self.assertIn("MIT", LICENSE_LINE)
        self.assertNotIn("Omunch\n", TITLE + "\n")
        self.assertNotEqual(TITLE, "Omunch")

    def test_license_file_is_mit_damon_hargraves(self) -> None:
        text = Path(__file__).resolve().parents[1].joinpath("LICENSE").read_text()
        self.assertTrue(text.startswith("MIT License"))
        self.assertIn("Copyright (c) Damon Hargraves", text)
        self.assertNotIn("Omunchy contributors", text)
        self.assertIn("THE SOFTWARE IS PROVIDED \"AS IS\"", text)


if __name__ == "__main__":
    unittest.main()
