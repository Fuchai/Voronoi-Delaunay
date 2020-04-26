from unittest import TestCase
from avl_beach import *


class TestBeachLineTree(TestCase):
    def test_insert(self):
        tree = BeachLineTree(debug=True)
        tree.y = 1
        tree.insert(Site(0, 1))
        tree.y = 0
        tree.insert(Site(-1, 0))
        tree.insert(Site(1, 0))
        tree.y = -1
        tree.plot()
        print("hello")

    def test_delete(self):
        tree = BeachLineTree(debug=True)
        tree.y = 1
        tree.insert(Site(0, 1))
        tree.y = 0
        tree.insert(Site(-1, 0))
        arc_right_node, bb = tree.insert(Site(1, 0))
        arc_left_node=arc_right_node.left_nbr
        tree.plot()
        tree.y = -0.5
        assert (arc_right_node.eval(tree.y) < bb.eval(tree.y))
        tree.plot()
        tree.consistency_test()
        tree.y = -1
        tree.plot()
        tree.consistency_test()
        tree.delete(arc_right_node.payload)
        tree.consistency_test()

        print("hello")

    def test_iter(self):
        tree = BeachLineTree()
        tree.y = 1
        tree.insert(Site(0, 1))
        tree.y = 0
        tree.insert(Site(-1, 0))
        arc_right_node, bb = tree.insert(Site(1, 0))
        tree.y = -0.5
        assert (arc_right_node.eval(tree.y) < bb.eval(tree.y))
        tree.y = -1
        tree.delete(arc_right_node.payload)
        tree.plot()

        for node in tree:
            print(node)