from unittest import TestCase

from avl_beach import *


class TestBreakPoint(TestCase):
    def test_get_coordinates(self):
        site1 = Site(0, 1, "s1")
        site2 = Site(0, 0, "s2")
        print(site1.string_parabola(-1))
        print(site2.string_parabola(-1))
        lbp = BreakPoint(site2, site1)
        rbp = BreakPoint(site1, site2)
        x, y = lbp.get_coordinates(-1)
        self.assertAlmostEquals(x, -math.sqrt(2))
        self.assertAlmostEqual(y, 1 / 2)

        x, y = rbp.get_coordinates(-1)
        self.assertAlmostEqual(x, math.sqrt(2))
        self.assertAlmostEqual(y, 1 / 2)

    def test_get_coordinate_1(self):
        site1 = Site(1, 1, "s1")
        site2 = Site(-1, 1, "s2")
        print(site1.string_parabola(-1))
        print(site2.string_parabola(-1))

        bp = BreakPoint(site1, site2)
        x, y = bp.get_coordinates(-1)

        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(y, 1 / 4)
