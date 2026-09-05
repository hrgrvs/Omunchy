import unittest

from omunchy.bestiary import PAUSE_MENU, TITLE_MENU, TROGGLE_GUIDE
from omunchy.entities import TROGGLE_KINDS


class BestiaryTests(unittest.TestCase):
    def test_guide_covers_all_five_kinds(self) -> None:
        kinds = tuple(row[0] for row in TROGGLE_GUIDE)
        self.assertEqual(kinds, TROGGLE_KINDS)
        self.assertEqual(len(TROGGLE_GUIDE), 5)
        names = [row[1].lower() for row in TROGGLE_GUIDE]
        self.assertIn("wander", names)
        self.assertIn("chase", names)
        self.assertIn("fire-breath", names)
        self.assertIn("exploder", names)
        self.assertIn("hunter", names)

    def test_blurbs_match_kid_friendly_behaviors(self) -> None:
        blurbs = {kind: blurb.lower() for kind, _name, blurb in TROGGLE_GUIDE}
        self.assertIn("random", blurbs["wander"])
        self.assertIn("follow", blurbs["chase"])
        self.assertIn("front", blurbs["fire"])
        self.assertIn("warning", blurbs["exploder"])
        self.assertIn("side", blurbs["exploder"])
        self.assertIn("eats", blurbs["hunter"])
        self.assertIn("hurt", blurbs["hunter"])
        for _kind, _name, blurb in TROGGLE_GUIDE:
            self.assertLessEqual(len(blurb), 64)

    def test_menus_include_troggles(self) -> None:
        self.assertIn("Play", TITLE_MENU)
        self.assertIn("Troggles", TITLE_MENU)
        self.assertIn("Resume", PAUSE_MENU)
        self.assertIn("Troggles", PAUSE_MENU)
        self.assertIn("Title", PAUSE_MENU)


if __name__ == "__main__":
    unittest.main()
