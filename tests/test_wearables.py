import os
import unittest

from omunchy.sprites import eat_label_transform
from omunchy.wearables import (
    CATALOG,
    CATEGORIES,
    BY_ID,
    Outfit,
    draw_cape,
    is_reward_level,
    offer_wearables,
)


class WearableCatalogTests(unittest.TestCase):
    def test_catalog_is_plentiful_and_covers_every_category(self) -> None:
        self.assertGreaterEqual(len(CATALOG), 70)
        self.assertEqual(len(BY_ID), len(CATALOG))
        seen = {item.category for item in CATALOG}
        self.assertEqual(seen, set(CATEGORIES))
        for category in CATEGORIES:
            variants = [item for item in CATALOG if item.category == category]
            self.assertGreaterEqual(len(variants), 8, msg=category)
            names = {item.name for item in variants}
            self.assertEqual(len(names), len(variants), msg=category)

    def test_hats_and_crowns_share_head_slot(self) -> None:
        hat = next(item for item in CATALOG if item.category == "hat")
        crown = next(item for item in CATALOG if item.category == "crown")
        glasses = next(item for item in CATALOG if item.category == "glasses")
        monocle = next(item for item in CATALOG if item.category == "monocle")
        self.assertEqual(hat.slot, crown.slot)
        self.assertEqual(glasses.slot, monocle.slot)
        outfit = Outfit()
        outfit.wear(hat)
        outfit.wear(crown)
        self.assertEqual(len(outfit.slots), 1)
        self.assertEqual(outfit.resolve()[0].category, "crown")
        outfit.wear(glasses)
        self.assertEqual(len(outfit.slots), 2)

    def test_offer_is_short_deterministic_and_prefers_empty_slots(self) -> None:
        a = offer_wearables("multiples", 4, frozenset(), frozenset())
        b = offer_wearables("multiples", 4, frozenset(), frozenset())
        self.assertEqual([item.id for item in a], [item.id for item in b])
        self.assertGreaterEqual(len(a), 3)
        self.assertLessEqual(len(a), 5)
        slots = [item.slot for item in a]
        self.assertEqual(len(slots), len(set(slots)))
        other = offer_wearables("primes", 4, frozenset(), frozenset())
        self.assertNotEqual([item.id for item in a], [item.id for item in other])

    def test_reward_every_three_cleared_levels(self) -> None:
        self.assertTrue(is_reward_level(3))
        self.assertTrue(is_reward_level(6))
        self.assertFalse(is_reward_level(1))
        self.assertFalse(is_reward_level(2))
        self.assertFalse(is_reward_level(4))

    def test_bat_cape_replaces_rainbow_cape(self) -> None:
        self.assertNotIn("cape-rainbow", BY_ID)
        self.assertNotIn("Rainbow Cape", {item.name for item in CATALOG})
        bat = BY_ID["cape-bat"]
        self.assertEqual(bat.name, "Bat Cape")
        self.assertEqual(bat.category, "cape")
        self.assertEqual(bat.slot, "cape")
        self.assertEqual(bat.variant, 4)
        self.assertEqual(bat.primary, (28, 28, 32))
        self.assertEqual(bat.accent, (164, 80, 220))
        outfit = Outfit()
        outfit.wear(bat)
        self.assertEqual(outfit.slots, {"cape": "cape-bat"})
        outfit.wear(BY_ID["cape-ruby"])
        self.assertEqual(outfit.slots, {"cape": "cape-ruby"})
        self.assertEqual(len(outfit.slots), 1)


class BatCapeDrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
        try:
            import pygame
        except ImportError as exc:  # pragma: no cover
            raise unittest.SkipTest("pygame is not installed") from exc
        pygame.display.init()
        cls.pygame = pygame

    @classmethod
    def tearDownClass(cls) -> None:
        cls.pygame.display.quit()

    def test_bat_cape_pixels_are_dark_not_rainbow(self) -> None:
        src = self.pygame.Surface((16, 16), self.pygame.SRCALPHA)
        draw_cape(src, BY_ID["cape-bat"], frame=0)
        pixels = [
            src.get_at((x, y))[:3]
            for x in range(16)
            for y in range(16)
            if src.get_at((x, y))[3] > 0
        ]
        self.assertGreater(len(pixels), 10)
        self.assertIn((28, 28, 32), pixels)
        self.assertIn((164, 80, 220), pixels)
        self.assertNotIn((236, 120, 180), pixels)
        self.assertNotIn((64, 212, 212), pixels)


class EatMotionTests(unittest.TestCase):
    def test_correct_chomp_shrinks_into_the_bite(self) -> None:
        _dx0, dy0, scale0, alpha0 = eat_label_transform(0.0, True)
        _dx1, dy1, scale1, alpha1 = eat_label_transform(1.0, True)
        self.assertGreater(dy1, dy0)
        self.assertLess(scale1, scale0)
        self.assertLess(alpha1, alpha0)
        self.assertLess(scale1, 0.25)

    def test_wrong_chomp_bounces_back(self) -> None:
        _dx_mid, dy_mid, scale_mid, _a_mid = eat_label_transform(0.4, False)
        _dx_end, dy_end, scale_end, alpha_end = eat_label_transform(1.0, False)
        self.assertGreater(scale_end, scale_mid)
        self.assertLess(dy_end, dy_mid)
        self.assertEqual(alpha_end, 1.0)


if __name__ == "__main__":
    unittest.main()
