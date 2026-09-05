import unittest

from omunchy.rules import factors_of, is_prime, rule_for


class PrimeTests(unittest.TestCase):
    def test_small_primes(self) -> None:
        for n in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29):
            self.assertTrue(is_prime(n), n)

    def test_composites_and_one(self) -> None:
        for n in (1, 4, 6, 8, 9, 15, 21, 25, 27):
            self.assertFalse(is_prime(n), n)


class RuleTests(unittest.TestCase):
    def test_multiples_level_one_is_twos(self) -> None:
        rule = rule_for("multiples", 1)
        self.assertEqual(rule.title, "Multiples of 2")
        self.assertTrue(rule.is_correct(2))
        self.assertTrue(rule.is_correct(18))
        self.assertFalse(rule.is_correct(9))
        self.assertFalse(rule.is_correct(0))

    def test_factors_of_twelve(self) -> None:
        rule = rule_for("factors", 3)
        self.assertEqual(rule.param, 12)
        self.assertTrue(rule.is_correct(1))
        self.assertTrue(rule.is_correct(6))
        self.assertTrue(rule.is_correct(12))
        self.assertFalse(rule.is_correct(5))
        self.assertEqual(factors_of(12), (1, 2, 3, 4, 6, 12))

    def test_primes_rule(self) -> None:
        rule = rule_for("primes", 1)
        self.assertEqual(rule.title, "Prime numbers")
        self.assertTrue(rule.is_correct(7))
        self.assertFalse(rule.is_correct(1))
        self.assertFalse(rule.is_correct(9))

    def test_equals_ten(self) -> None:
        rule = rule_for("equals", 1)
        self.assertEqual(rule.title, "Equals 10")
        self.assertTrue(rule.is_correct(10))
        self.assertFalse(rule.is_correct(9))

    def test_mixed_is_gone(self) -> None:
        with self.assertRaises(ValueError):
            rule_for("mixed", 1)

    def test_pairings_walks_ten_then_hundred_then_thousand(self) -> None:
        for level in range(1, 7):
            rule = rule_for("pairings", level)
            self.assertEqual(rule.mode, "pairings")
            self.assertEqual(rule.param, 10)
            self.assertEqual(rule.title, "Make 10")
            self.assertTrue(rule.is_correct_pair(1, 9))
            self.assertTrue(rule.is_correct_pair(5, 5))
            self.assertFalse(rule.is_correct_pair(1, 8))
            self.assertTrue(rule.is_pair_member(1))
            self.assertEqual(rule, rule_for("pairings", level))
        for level in range(7, 13):
            rule = rule_for("pairings", level)
            self.assertEqual(rule.param, 100)
            self.assertEqual(rule.title, "Make 100")
            self.assertTrue(rule.is_correct_pair(10, 90))
            self.assertTrue(rule.is_correct_pair(50, 50))
            self.assertFalse(rule.is_correct_pair(10, 80))
        for level in (13, 14, 20):
            rule = rule_for("pairings", level)
            self.assertEqual(rule.param, 1000)
            self.assertEqual(rule.title, "Make 1000")
            self.assertTrue(rule.is_correct_pair(100, 900))
            self.assertTrue(rule.is_correct_pair(400, 600))
            self.assertFalse(rule.is_correct_pair(100, 800))

    def test_multiples_covers_two_through_twenty_in_order(self) -> None:
        expected = list(range(2, 21))
        actual = [rule_for("multiples", level).param for level in range(1, 20)]
        self.assertEqual(actual, expected)
        for level, n in enumerate(expected, start=1):
            rule = rule_for("multiples", level)
            self.assertEqual(rule.title, f"Multiples of {n}")
            self.assertEqual(rule.param, n)
            self.assertGreaterEqual(rule.max_n or 0, n)
            self.assertLessEqual(rule.max_n or 0, 60)
            again = rule_for("multiples", level)
            self.assertEqual(rule, again)

    def test_multiples_wraps_deterministically_after_twenty(self) -> None:
        first = rule_for("multiples", 1)
        wrapped = rule_for("multiples", 20)
        self.assertEqual(wrapped.param, first.param)
        self.assertEqual(wrapped.title, first.title)
        self.assertEqual(rule_for("multiples", 20), rule_for("multiples", 20))

    def test_progression_stays_grade_band(self) -> None:
        for level in range(1, 16):
            multiples = rule_for("multiples", level)
            self.assertIn(multiples.param, range(2, 21))
            self.assertLessEqual(multiples.max_n or 0, 60)
            factors = rule_for("factors", level)
            self.assertLessEqual(factors.param or 0, 36)
            primes = rule_for("primes", level)
            self.assertLessEqual(primes.max_n or 0, 29)
            equals = rule_for("equals", level)
            self.assertLessEqual(equals.param or 0, 20)
            pairings = rule_for("pairings", level)
            self.assertIn(pairings.param, (10, 100, 1000))
            self.assertTrue(pairings.pairs)


if __name__ == "__main__":
    unittest.main()