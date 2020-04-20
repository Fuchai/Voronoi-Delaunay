from unittest import TestCase
from avl_beach import *


class TestBeachLineTree(TestCase):
    def test_insert(self):
        tree = BeachLineTree()
        tree.l = 1
        tree.insert(Site(0, 1))
        tree.l = 0
        tree.insert(Site(-1, 0))
        tree.insert(Site(1, 0))
        tree.l = -1
        tree.plot()
        print("hello")

    def test_delete(self):
        tree = BeachLineTree()
        tree.l = 1
        tree.insert(Site(0, 1))
        tree.l = 0
        tree.insert(Site(-1, 0))
        arc_right_node, bb = tree.insert(Site(1, 0))
        arc_left_node=arc_right_node.left_nbr
        tree.plot()
        tree.l = -0.5
        assert (arc_right_node.eval(tree.l) < bb.eval(tree.l))
        tree.plot()
        tree.consistency_test()
        tree.l = -1
        # tree.plot()
        tree.consistency_test()
        tree.delete(arc_left_node.payload, arc_right_node.payload)
        tree.consistency_test()

        print("hello")

    def test_iter(self):
        tree = BeachLineTree()
        tree.l = 1
        tree.insert(Site(0, 1))
        tree.l = 0
        tree.insert(Site(-1, 0))
        arc_right_node, bb = tree.insert(Site(1, 0))
        tree.l = -0.5
        assert (arc_right_node.eval(tree.l) < bb.eval(tree.l))
        tree.l = -1
        tree.delete(arc_right_node)
        tree.plot()

        for node in tree:
            print(node)