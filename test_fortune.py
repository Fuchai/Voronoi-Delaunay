from unittest import TestCase
from voro import *

class TestFortune(TestCase):
    def test_run(self):
        sites = [(0, 1), (-1, 0), (1, -0.3)]
        sites = [Site(x, y) for x, y in sites]
        for site in sites:
            print(site)

        fortune = Fortune(sites)
        fortune.run()