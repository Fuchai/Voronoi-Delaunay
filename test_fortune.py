from unittest import TestCase
from fortune import *


class TestFortune(TestCase):
    def test_run(self):
        points = [(0, 1), (-1, 0), (1, -0.3), (2, -2), (-2, -5)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
        print()
        print("Inserting sites")
        for site in sites:
            print(site)

        fortune = Fortune(sites)
        fortune.run()

        fortune.plot()

    def test_colinear_horizontal(self):
        points = [(1, 0), (2, 0), (-1, 0), (2, 0), (-2, 0)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
        print()
        print("Inserting sites")
        for site in sites:
            print(site)

        fortune = Fortune(sites)
        fortune.run()

        fortune.plot()
        print("done")

    def test_colinear_vertical(self):
        points = [(0, 1), (0, 2), (0, 3), (0, 4), (0, 5)]
        sites = []
        for i, point in enumerate(points):
            sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
        print()
        print("Inserting sites")
        for site in sites:
            print(site)

        fortune = Fortune(sites)
        fortune.run()

        fortune.plot()
        print("done")
