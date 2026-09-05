import unittest

from omunchy.constants import TITLE
from omunchy.title_art import CONTROLS_HINT, TAGLINE, TITLE_BANNER, TITLE_DOODLE


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
        self.assertNotIn("Omunch\n", TITLE + "\n")
        self.assertNotEqual(TITLE, "Omunch")


if __name__ == "__main__":
    unittest.main()
