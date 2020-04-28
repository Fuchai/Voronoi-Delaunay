from unittest import TestCase

from dcel import *


class TestDCEL(TestCase):
    def test_naive_polygon(self):
        dcel = DCEL(demo=True)
        v1 = Vertex(dcel, 0, 0, None, "v1")
        v2 = Vertex(dcel, 1, 0, None, "v2")
        v3 = Vertex(dcel, 0, 1, None, "v3")

        dcel.naive_polygon([v1, v2, v3], dcel.faces[0])

        print(repr(dcel))
