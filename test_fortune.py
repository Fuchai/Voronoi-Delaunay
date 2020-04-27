from unittest import TestCase
from fortune import *


class TestFortune(TestCase):
    def test_run(self):
        points = [(0, 1), (-1, 0), (1, -0.3), (2, -2), (-2, -5), (3,-3)]
        # points = [(0, 1), (-1, 0), (1, -0.3), (2, -2), (-2, -5)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
        print()
        fortune = Fortune(sites)
        fortune.run()

    def test_colinear_horizontal(self):
        points = [(1, 0), (2, 0), (-1, 0), (3, 0), (-2, 0)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
        print()

        fortune = Fortune(sites)
        fortune.run()

    def test_colinear_vertical(self):
        points = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))

        print()

        fortune = Fortune(sites)
        fortune.run()

    def test_colinear(self):
        points = [(2, 1), (4, 2), (6, 3), (8, 4), (10, 5)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
        print()

        fortune = Fortune(sites)
        fortune.run()

    def test_multiple_site_events(self):
        points = [(0, 1), (-1, 0), (1, -0.3), (2, -2), (0, -3), (2, -3), (-2, -5)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
        print()

        fortune = Fortune(sites)
        fortune.run()

    def test_multiple_circle_events(self):
        pass

    def test_multiple_mix(self):
        pass

    def test_site_right_underneath(self):
        pass