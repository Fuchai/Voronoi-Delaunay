from unittest import TestCase

from avl_beach import Site
from input_output import read_input


class TestRead_input(TestCase):
    def test_read_input(self):
        sites = read_input()
        new_sites = []
        for i, site in enumerate(sites):
            x, y = site.x, site.y
            new_sites.append(Site(x, y, name="p" + str(i + 1)))

        print(new_sites)
        return new_sites
