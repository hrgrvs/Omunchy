import unittest

from omunchy.celebrate import (
    CELEBRATE_EVERY,
    CELEBRATE_SECONDS,
    banner_for_level,
    is_celebration_level,
)


class CelebrateTests(unittest.TestCase):
    def test_every_third_level(self) -> None:
        self.assertEqual(CELEBRATE_EVERY, 3)
        for level in (3, 6, 9, 12):
            self.assertTrue(is_celebration_level(level))
        for level in (0, 1, 2, 4, 5, 7, 8, 10):
            self.assertFalse(is_celebration_level(level))

    def test_duration_is_short(self) -> None:
        self.assertGreaterEqual(CELEBRATE_SECONDS, 2.0)
        self.assertLessEqual(CELEBRATE_SECONDS, 4.0)

    def test_banners_are_encouraging(self) -> None:
        for level in (3, 6, 9, 12):
            banner = banner_for_level(level)
            self.assertTrue(banner)
            self.assertNotIn("die", banner.lower())
            self.assertNotIn("fail", banner.lower())


if __name__ == "__main__":
    unittest.main()