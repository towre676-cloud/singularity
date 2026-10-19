"""Kernel-checked bounded quadratic queries (`perfectpower.bounded_pell`, `BoundedPell.lean`)."""
import random
import shutil
import sys
import unittest
from math import isqrt
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from perfectpower.bounded_pell import Unsupported, kernel_check, plan  # noqa: E402

LAKE = shutil.which('lake') or (Path.home() / '.elan' / 'bin' / 'lake').exists()


def brute(a, b, c, q, p, r, lo, hi):
    out = set()
    for N in range(lo, hi + 1):
        rhs = q * N * N + p * N + r - c          # a S^2 + b S = rhs  <=>  (2aS + b)^2 = 4a rhs + b^2
        t = 4 * a * rhs + b * b
        if t < 0:
            continue
        w = isqrt(t)
        if w * w != t:
            continue
        for Y in {w, -w}:
            if (Y - b) % (2 * a) == 0:
                out.add((N, (Y - b) // (2 * a)))
    return sorted(out)


class Plan(unittest.TestCase):
    def test_matches_brute_force(self):
        rng = random.Random(7)
        done = 0
        while done < 40:
            a, q = rng.randint(1, 4), rng.randint(1, 4)
            b, c, p, r = (rng.randint(-5, 5) for _ in range(4))
            if isqrt(a * q) ** 2 == a * q:
                continue
            lo = max(-p // (2 * q) + 1, 1)
            try:
                P = plan(a, b, c, q, p, r, lo, lo + 3000)
            except Unsupported:
                continue
            self.assertEqual(P['L0'], brute(a, b, c, q, p, r, lo, lo + 3000), (a, b, c, q, p, r))
            done += 1

    def test_refusals(self):
        with self.assertRaises(Unsupported):
            plan(2, 1, 0, 263, 0, 1, 1, 10 ** 30)        # unit ~ 8.4e19: root box too large
        with self.assertRaises(Unsupported):
            plan(2, 0, 0, 1, -1, 0, 0, 100)              # 2q lo + p = -1: range crosses the turning point
        with self.assertRaises(Unsupported):
            plan(1, 0, 0, 4, 0, 1, 1, 100)               # D = 4 is a square

    @unittest.skipUnless(LAKE, 'lake not available')
    def test_kernel_checks_pairs_square(self):
        P = plan(2, 0, 0, 1, -1, 0, 2, 10 ** 9)
        self.assertEqual(len(P['L0']), 24)
        ok, detail = kernel_check(P)
        self.assertTrue(ok, detail)

    @unittest.skipUnless(LAKE, 'lake not available')
    def test_kernel_rejects_a_wrong_list(self):
        P = plan(2, 0, 0, 1, -1, 0, 2, 10 ** 6)
        P = dict(P, L0=[x for x in P['L0'] if x != (9, -6)])     # drop one solution
        ok, _ = kernel_check(P)
        self.assertFalse(ok)


if __name__ == '__main__':
    unittest.main()
