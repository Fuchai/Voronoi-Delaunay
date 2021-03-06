# Python code to delete a node in AVL tree
# Generic tree node class
import abc
import math

import matplotlib.pyplot as plt
import numpy as np


class TreeNode:
    def __init__(self, payload):
        assert isinstance(payload, Payload)
        self.payload = payload
        self.left_child = None
        self.right_child = None
        self.height = 1
        self.parent = None

        self.left_nbr = None
        self.right_nbr = None

    def eval(self, ly=None):
        if isinstance(self.payload, float):
            # when is this called?
            return self.payload
        else:
            return self.payload.eval(ly)

    def __str__(self):
        return "node." + str(self.payload)

    # @property
    # def left_nbr(self):
    #     return self.payload.left_nbr
    #
    # @left_nbr.setter
    # def left_nbr(self, val):
    #     self.payload.left_nbr=val
    #
    # @property
    # def right_nbr(self):
    #     return self.payload.right_nbr
    #
    # @right_nbr.setter
    # def right_nbr(self,val):
    #     return s


#
# class Parabola:
#     def __init__(self, site):
#         self.site = site
#
#     def get_y(self, x, ly):
#         return 1 / (self.site.y - ly) * (
#                 x * x - 2 * self.site.x * x + self.site.x * self.site.x + self.site.y * self.site.y - ly * ly)
#

class Payload(abc.ABC):
    @abc.abstractmethod
    def eval(self, l):
        pass


class Site(Payload):
    def __init__(self, x, y, name="site"):
        self.x = x
        self.y = y
        self.name = name
        self.cell = None

    def __str__(self):
        return f"{self.name} ({self.x}, {self.y})"

    # def __le__(self, other):
    #     pass

    def eval(self, l=None):
        return self.x

    def get_parabola_y(self, x, ly):
        return 1 / (2 * (self.y - ly)) * (
                x * x - 2 * self.x * x + self.x * self.x + self.y * self.y - ly * ly)

    def get_parabola_derivative(self, x, ly):
        ret = 1 / (2 * (self.y - ly)) * (2 * x - 2 * self.x)
        return ret

    def string_parabola(self, l):
        a = self.x
        b = self.y
        if math.isclose(b, l, abs_tol=1e-5):
            return f"vertical site ({self.x}, {self.y})"
        else:
            coef2 = 1 / (2 * (b - l))
            coef1 = coef2 * (-2 * a)
            coef0 = coef2 * (a * a + b * b - l * l)
            plus = "+"
            empty = ""
            repr = f"y = {coef2:.2f}x^2 {plus if coef1 >= 0 else empty}{coef1:.2f}x {plus if coef0 >= 0 else empty}{coef0:.2f}"
            return repr


class BreakPoint(Payload):
    """
    A break point also represents the arc to its left.
    tree.delete(arc_right_break_point)
    """

    def __init__(self, left_higher_site, left_lower_site):
        # site event parabola for the left twin break point
        self.left_higher_site = left_higher_site
        self.left_lower_site = left_lower_site
        # self.left_nbr=None
        # self.right_nbr=None
        self.circle_event = None
        # the incident face of this half edge is not the site of this arc
        # assert self.half_edge.twin.incident_face is self.arc.site_of_arc().cell_face
        self.half_edge = None

    def get_coordinates(self, ly):
        # get parabolas
        a = self.left_higher_site.x
        b = self.left_higher_site.y
        c = self.left_lower_site.x
        d = self.left_lower_site.y

        # get intersection
        coef2 = d - b
        coef1 = 2 * a * ly - 2 * a * d - 2 * c * ly + 2 * c * b
        coef0 = a * a * d + b * b * d - ly * ly * d - a * a * ly - b * b * ly - \
                c * c * b - d * d * b + ly * ly * b + c * c * ly + d * d * ly

        # What if coef2 is zero? That only happens if the first two sites are the same height
        # need to handle it in the overall algorithm.

        if coef2 != 0:
            if math.isclose(self.left_lower_site.y, ly, abs_tol=1e-5) or math.isclose(self.left_higher_site.y, ly,
                                                                                      abs_tol=1e-5):
                has_vertical = True
            else:
                has_vertical = False
            if not has_vertical:
                x1 = (-coef1 - math.sqrt(coef1 * coef1 - 4 * coef2 * coef0)) / 2 / coef2
                x2 = (-coef1 + math.sqrt(coef1 * coef1 - 4 * coef2 * coef0)) / 2 / coef2
                if x2 < x1:
                    x1, x2 = x2, x1

                y1 = self.left_higher_site.get_parabola_y(x1, ly)
                y11 = self.left_lower_site.get_parabola_y(x1, ly)
                assert math.isclose(y1, y11, abs_tol=1e-5)

                y2 = self.left_higher_site.get_parabola_y(x2, ly)
                y22 = self.left_lower_site.get_parabola_y(x2, ly)
                assert math.isclose(y2, y22, abs_tol=1e-5)

                # to pick intersection, judge which site is lower
                if self.left_higher_site.y < self.left_lower_site.y:
                    # the left solution has left higher site lower
                    return x1, y1
                else:
                    # the right solution has left higher site higher
                    return x2, y2
            else:
                if math.isclose(self.left_lower_site.y, ly, abs_tol=1e-5):
                    return self.left_lower_site.x, self.left_higher_site.get_parabola_y(self.left_lower_site.x, ly)
                elif math.isclose(self.left_higher_site.y, ly, abs_tol=1e-5):
                    return self.left_higher_site.x, self.left_lower_site.get_parabola_y(self.left_higher_site.x, ly)
                else:
                    raise ValueError("Investigate this")
        else:
            if coef1 == 0:
                assert b == 0 and d == 0
                return (a + c) / 2, float("inf")
            else:
                x = -coef0 / coef1
                y = self.left_higher_site.get_parabola_y(x, ly)
                yy = self.left_lower_site.get_parabola_y(x, ly)
                assert math.isclose(y, yy, abs_tol=1e-5)
                return x, y

    def eval(self, l):
        return self.get_coordinates(l)[0]

    # def __le__(self, other):
    #     if isinstance(other, Site):
    #         # happens when a new site is inserted
    #         raise NotImplementedError
    #     elif isinstance(other, BreakPoint):
    #         # happens when a tree rotates
    #         return

    def plot(self, l):
        x, y = self.get_coordinates(l)
        m = np.linspace(-5 + x, 5 + x, 5000)
        for site in (self.left_higher_site, self.left_lower_site):
            my = site.get_parabola_y(m, l)
            plt.plot(m, my, label=site.string_parabola(l))

        plt.show()

    def __str__(self):
        return "bp: l " + str(self.left_lower_site) + " r " + str(self.left_higher_site)

    def arc_to_site(self):
        return self.left_lower_site

    def half_edge_to_incident_cell_site(self):
        return self.left_higher_site


# AVL tree class which supports insertion,
# deletion operations
class BeachLineTree:
    def __init__(self, root=None, debug=False):
        self.root = root
        self.y = None
        self.break_point_counts = 0
        self.debug = debug

    # def insert(self, site):
    #     """
    #
    #     :param site:
    #     :return: the right new node, marking the arc to the right
    #     """
    #     if self.debug:
    #         self.consistency_test()
    #     # first site and second site are handled differently
    #
    #     # keep inserting sites, do not make them into break points
    #     # if the site c is not co-linear, then re-organize the tree into break points
    #     # insert site c normally and in the future
    #
    #
    #     if self.root is None:
    #         self.root = TreeNode(site)
    #         left_new_node = None
    #         right_new_node = None
    #
    #     elif self._horizontal_co_linear:
    #         if site.y==self.root.payload.y:
    #             # still co linear
    #             # if len(self)==0:
    #             #     assert isinstance(self.root, Site)
    #             #     if site.x> self.root.x:
    #             #         self.root=TreeNode(BreakPoint(site,self.root))
    #             #     else:
    #             #         self.root=TreeNode(BreakPoint(self.root, site))
    #             #     self.break_point_counts += 1
    #             # else:
    #             self.root, new_node=self._insert(self.root, site)
    #             self.break_point_counts+=1
    #             left_new_node = None
    #             right_new_node = None
    #         else:
    #             # the current site breaks co-linearity
    #             # turn all the nodes in the tree into break points one by one
    #             self._horizontal_co_linear = False
    #
    #             if len(self)==0:
    #                 # if there is only one site, then
    #                 old_site = self.root.payload
    #                 self.root = None
    #
    #                 self.root, left_new_node = self._insert(self.root, site)
    #                 # have to insert from root because the tree might be imbalanced
    #                 self.root, right_new_node = self._insert(self.root, site)
    #
    #                 assert left_new_node.right_nbr is right_new_node
    #                 assert left_new_node is right_new_node.parent
    #
    #                 left_break_point = BreakPoint(site, old_site)
    #                 right_break_point = BreakPoint(old_site, site)
    #                 left_new_node.payload = left_break_point
    #                 right_new_node.payload = right_break_point
    #
    #                 self.break_point_counts += 2
    #             else:
    #                 # if there are multiple sites, then turn them into consecutive break points
    #                 left_site_node=None
    #                 for right_site_node in self:
    #                     if left_site_node is not None:
    #                         bp=BreakPoint(right_site_node.payload, left_site_node.payload)
    #                         left_site_node.payload=bp
    #                     left_site_node=right_site_node
    #
    #                 # delete the right most site node
    #                 self._delete(self.root, left_site_node.payload)
    #                 # insert normally
    #                 return self.insert(site)
    #
    #     else:
    #         # third site and so on
    #         self.root, left_new_node = self._insert(self.root, site)
    #         # have to insert from root because the tree might be imbalanced
    #         self.root, right_new_node = self._insert(self.root, site)
    #
    #         assert left_new_node.right_nbr is right_new_node
    #
    #         if left_new_node is right_new_node.parent:
    #             new_parent = left_new_node
    #         else:
    #             new_parent = right_new_node
    #
    #         if new_parent is new_parent.parent.left_child:
    #             old_site = new_parent.parent.payload.left_lower_site
    #         else:
    #             old_site = new_parent.parent.payload.left_higher_site
    #
    #         left_break_point = BreakPoint(site, old_site)
    #         right_break_point = BreakPoint(old_site, site)
    #         left_new_node.payload = left_break_point
    #         right_new_node.payload = right_break_point
    #         self.break_point_counts += 2
    #     if self.debug:
    #         self.consistency_test()
    #     return left_new_node, right_new_node

    #
    # def insert(self, site):
    #     """
    #
    #     :param site:
    #     :return: the right new node, marking the arc to the right
    #     """
    #     if self.debug:
    #         self.consistency_test()
    #     # first site and second site are handled differently
    #     if self.root is None:
    #         self.root = site
    #         left_new_node = None
    #         right_new_node = None
    #     elif self.root is not None and isinstance(self.root, Site):
    #         # second site
    #         # the root is a parabola by a site
    #         assert len(self) == 0
    #         old_site = self.root
    #         self.root = None
    #
    #         self.root, left_new_node = self._insert(self.root, site)
    #         # have to insert from root because the tree might be imbalanced
    #         self.root, right_new_node = self._insert(self.root, site)
    #
    #         assert left_new_node.right_nbr is right_new_node
    #
    #         assert left_new_node is right_new_node.parent
    #         assert left_new_node.right_nbr is right_new_node
    #         assert right_new_node.left_nbr is left_new_node
    #
    #         left_break_point = BreakPoint(site, old_site)
    #         right_break_point = BreakPoint(old_site, site)
    #         left_new_node.payload = left_break_point
    #         right_new_node.payload = right_break_point
    #
    #         self.break_point_counts += 2
    #     else:
    #         # third site and so on
    #         self.root, left_new_node = self._insert(self.root, site)
    #         # have to insert from root because the tree might be imbalanced
    #         self.root, right_new_node = self._insert(self.root, site)
    #
    #         assert left_new_node.right_nbr is right_new_node
    #
    #         if left_new_node is right_new_node.parent:
    #             new_parent = left_new_node
    #         else:
    #             new_parent = right_new_node
    #
    #         if new_parent is new_parent.parent.left_child:
    #             old_site = new_parent.parent.payload.left_lower_site
    #         else:
    #             old_site = new_parent.parent.payload.left_higher_site
    #
    #         left_break_point = BreakPoint(site, old_site)
    #         right_break_point = BreakPoint(old_site, site)
    #         left_new_node.payload = left_break_point
    #         right_new_node.payload = right_break_point
    #         self.break_point_counts += 2
    #     if self.debug:
    #         self.consistency_test()
    #     return left_new_node, right_new_node

    def insert_horizontal_colinear(self, sites):
        assert self.root is None
        bps = []
        if len(sites) != 1:
            for i in range(len(sites) - 1):
                left_site = sites[i]
                right_site = sites[i + 1]
                bp = BreakPoint(right_site, left_site)
                self.root, new_node = self._insert(self.root, bp)
                self.break_point_counts += 1
                bps.append(bp)
        else:
            self.root = sites[0]
        return bps

    def insert(self, site):
        """

        :param site:
        :return: the right new node, marking the arc to the right
        """
        if self.debug:
            self.consistency_test()
        # first site and second site are handled differently
        if self.root is None:
            self.root = site
            left_new_node = None
            right_new_node = None
        elif self.root is not None and isinstance(self.root, Site):
            # second site
            # the root is a parabola by a site
            assert len(self) == 0
            old_site = self.root
            self.root = None

            self.root, left_new_node = self._insert(self.root, site)
            # have to insert from root because the tree might be imbalanced
            self.root, right_new_node = self._insert(self.root, site)

            assert left_new_node.right_nbr is right_new_node

            assert left_new_node is right_new_node.parent
            assert left_new_node.right_nbr is right_new_node
            assert right_new_node.left_nbr is left_new_node

            left_break_point = BreakPoint(site, old_site)
            right_break_point = BreakPoint(old_site, site)
            left_new_node.payload = left_break_point
            right_new_node.payload = right_break_point

            self.break_point_counts += 2
        else:
            # third site and so on
            self.root, left_new_node = self._insert(self.root, site)
            # have to insert from root because the tree might be imbalanced
            self.root, right_new_node = self._insert(self.root, site)

            assert left_new_node.right_nbr is right_new_node

            if left_new_node is right_new_node.parent:
                new_parent = left_new_node
            else:
                new_parent = right_new_node

            if new_parent is new_parent.parent.left_child:
                old_site = new_parent.parent.payload.left_lower_site
            else:
                old_site = new_parent.parent.payload.left_higher_site

            left_break_point = BreakPoint(site, old_site)
            right_break_point = BreakPoint(old_site, site)
            left_new_node.payload = left_break_point
            right_new_node.payload = right_break_point
            self.break_point_counts += 2
        if self.debug:
            self.consistency_test()
        return left_new_node, right_new_node

    def _insert(self, node, payload, left_nbr=None, right_nbr=None):
        # Step 1 - Perform normal BST
        if not node:
            new_node = TreeNode(payload)
            # rotations do not change neighbors
            new_node.left_nbr = left_nbr
            new_node.right_nbr = right_nbr
            if left_nbr is not None:
                # when it is the only site
                left_nbr.right_nbr = new_node
            if right_nbr is not None:
                right_nbr.left_nbr = new_node
            return new_node, new_node
        elif payload.eval(self.y) < node.eval(self.y):
            ch, new_node = self._insert(node.left_child, payload, left_nbr=left_nbr, right_nbr=node)
            node.left_child = ch
            ch.parent = node
        # elif payload > node.eval(self.l):
        #     ch, new_node = self._insert(node.right_child, payload)
        #     node.right_child = ch
        #     ch.parent = node
        else:
            ch, new_node = self._insert(node.right_child, payload, left_nbr=node, right_nbr=right_nbr)
            node.right_child = ch
            ch.parent = node

        # Step 2 - Update the height of the
        # ancestor node
        node.height = 1 + max(self.get_height(node.left_child),
                              self.get_height(node.right_child))

        # Step 3 - Get the balance factor
        balance = self.get_balance(node)

        # Step 4 - If the node is unbalanced,
        # then try out the 4 cases
        # Case 1 - Left Left
        if balance > 1 and payload.eval(self.y) < node.left_child.eval(self.y):
            return self.right_rotate(node), new_node

            # Case 2 - Right Right
        if balance < -1 and payload.eval(self.y) > node.right_child.eval(self.y):
            return self.left_rotate(node), new_node

            # Case 3 - Left Right
        if balance > 1 and payload.eval(self.y) > node.left_child.eval(self.y):
            ch = self.left_rotate(node.left_child)
            node.left_child = ch
            ch.parent = node
            return self.right_rotate(node), new_node

            # Case 4 - Right Left
        if balance < -1 and payload.eval(self.y) < node.right_child.eval(self.y):
            ch = self.right_rotate(node.right_child)
            node.right_child = ch
            ch.parent = node
            return self.left_rotate(node), new_node

        return node, new_node

    # def node_to_arc_site(self, right_new_node):
    #     # the insert function returns the right of the new breakpoints pair
    #     # use this function to find which arc and site it represents
    #     arc = (right_new_node, right_new_node.right_nbr)
    #     site = right_new_node.payload.left_higher_site
    #     assert site is right_new_node.right_nbr.payload.left_lower_site
    #     return arc, site

    def find(self, key):
        def _find(node, _key):
            if not node:
                return node
            elif _key < node.eval(self.y):
                return _find(node.left_child, _key)
            else:
                return _find(node.right_child, _key)

        return _find(self.root, key)

    # given key from subtree with given self.root.
    # It returns self.root of the modified subtree.

    # How do we delete during a circle event?
    def delete(self, arc_right_break_point):
        """

        :param arc_right_break_point: the right break point of the arc to be deleted
        :return:
        """
        if self.debug:
            self.consistency_test()

        # arc_left_node = arc_right_break_point.left_nbr

        # we want to remove the right break point from the tree
        self.root, arc_left_node = self._delete(self.root, arc_right_break_point)
        self.break_point_counts -= 1
        arc_left_break_point = arc_left_node.payload
        assert arc_left_break_point.left_higher_site is arc_right_break_point.left_lower_site

        # the arc left node needs to refer to the correct site and have the correct neighbors
        arc_left_break_point.left_higher_site = arc_right_break_point.left_higher_site

        if self.debug:
            self.consistency_test()
        return arc_left_node

    def _delete(self, current_node, to_delete_node):
        """

        :param current_node:
        :param to_delete_node:
        :return:
        """
        # Step 1 - Perform standard BST delete
        if not current_node:
            raise ValueError("Node not found?")
        else:
            tdne = to_delete_node.eval(self.y)
            cne = current_node.eval(self.y)
            if current_node is to_delete_node or current_node.payload is to_delete_node:
                # current node is to be deleted
                # assert current_node is to_delete_node or current_node.payload is to_delete_node
                if current_node.left_child is None and current_node.right_child is None:
                    if current_node.left_nbr is not None:
                        current_node.left_nbr.right_nbr = current_node.right_nbr
                    if current_node.right_nbr is not None:
                        current_node.right_nbr.left_nbr = current_node.left_nbr
                    return None, current_node.left_nbr
                elif current_node.left_child is None:
                    if current_node.left_nbr is not None:
                        current_node.left_nbr.right_nbr = current_node.right_nbr
                    if current_node.right_nbr is not None:
                        current_node.right_nbr.left_nbr = current_node.left_nbr
                    return current_node.right_child, current_node.left_nbr

                elif current_node.right_child is None:
                    if current_node.left_nbr is not None:
                        current_node.left_nbr.right_nbr = current_node.right_nbr
                    if current_node.right_nbr is not None:
                        current_node.right_nbr.left_nbr = current_node.left_nbr

                    return current_node.left_child, current_node.left_nbr
                else:
                    # node has both children
                    temp = self.get_min_value_node(current_node.right_child)
                    assert current_node.right_nbr is temp
                    current_node.payload = temp.payload
                    # if temp.right_nbr is not None:
                    #     temp.right_nbr.left_nbr = current_node
                    # current_node.right_nbr = temp.right_nbr
                    # if temp.left_nbr is not None:
                    #     temp.left_nbr = current_node.left_nbr
                    # current_node.left_nbr.right_nbr=current_node

                    ch, _ = self._delete(current_node.right_child, temp)
                    # rotate possible
                    current_node.right_child = ch
                    if ch is not None:
                        ch.parent = current_node
                    arc_left_node = current_node.left_nbr
            elif math.isclose(tdne, cne, abs_tol=1e-5):
                # have to check both children. float point error
                try:
                    ch, arc_left_node = self._delete(current_node.left_child, to_delete_node)
                    current_node.left_child = ch
                    if ch:
                        ch.parent = current_node
                except ValueError:
                    try:
                        ch, arc_left_node = self._delete(current_node.right_child, to_delete_node)
                        current_node.right_child = ch
                        if ch:
                            ch.parent = current_node
                    except ValueError:
                        raise
            else:
                if tdne < cne:
                    # TODO I want the delete function to find me the left break point of the arc.
                    ch, arc_left_node = self._delete(current_node.left_child, to_delete_node)
                    # a rotation in the subtree might have happened, which requires that the parent-child pointers to be changed
                    # neighbor references do not change
                    current_node.left_child = ch
                    if ch:
                        ch.parent = current_node
                else:
                    ch, arc_left_node = self._delete(current_node.right_child, to_delete_node)
                    current_node.right_child = ch
                    if ch:
                        ch.parent = current_node

        # If the subtree has only one node,
        # simply return it
        if current_node is None:
            return current_node, arc_left_node

        # Step 2 - Update the height of the
        # ancestor node
        current_node.height = 1 + max(self.get_height(current_node.left_child),
                                      self.get_height(current_node.right_child))

        # Step 3 - Get the balance factor
        balance = self.get_balance(current_node)

        # Step 4 - If the node is unbalanced,
        # then try out the 4 cases
        # Case 1 - Left Left
        if balance > 1 and self.get_balance(current_node.left_child) >= 0:
            return self.right_rotate(current_node), arc_left_node

            # Case 2 - Right Right
        if balance < -1 and self.get_balance(current_node.right_child) <= 0:
            return self.left_rotate(current_node), arc_left_node

            # Case 3 - Left Right
        if balance > 1 and self.get_balance(current_node.left_child) < 0:
            ch = self.left_rotate(current_node.left_child)
            current_node.left_child = ch
            ch.parent = current_node
            return self.right_rotate(current_node), arc_left_node

            # Case 4 - Right Left
        if balance < -1 and self.get_balance(current_node.right_child) > 0:
            ch = self.right_rotate(current_node.right_child)
            current_node.right_child = ch
            ch.parent = current_node
            return self.left_rotate(current_node), arc_left_node

        return current_node, arc_left_node

    def left_rotate(self, z):
        y = z.right_child
        T2 = y.left_child

        # Perform rotation
        y.left_child = z
        if z is not None:
            z.parent = y
        z.right_child = T2
        if T2 is not None:
            T2.parent = z

        # Update heights
        z.height = 1 + max(self.get_height(z.left_child),
                           self.get_height(z.right_child))
        y.height = 1 + max(self.get_height(y.left_child),
                           self.get_height(y.right_child))

        # Return the new self.root
        return y

    def right_rotate(self, z):
        y = z.left_child
        T3 = y.right_child

        # Perform rotation
        y.right_child = z
        if z is not None:
            z.parent = y
        z.left_child = T3
        if T3 is not None:
            T3.parent = z

        # Update heights
        z.height = 1 + max(self.get_height(z.left_child),
                           self.get_height(z.right_child))
        y.height = 1 + max(self.get_height(y.left_child),
                           self.get_height(y.right_child))

        # Return the new self.root
        return y

    def get_height(self, node):
        if not node:
            return 0

        return node.height

    def get_balance(self, node):
        if not node:
            return 0

        return self.get_height(node.left_child) - self.get_height(node.right_child)

    def get_min_value_node(self, node):
        if node is None or node.left_child is None:
            return node
        return self.get_min_value_node(node.left_child)

    def get_max_value_node(self, node):
        if node is None or node.right_child is None:
            return node
        return self.get_max_value_node(node.right_child)

    def pre_order(self, node):

        if node.left_child is not None:
            yield from self.pre_order(node.left_child)
        yield node
        if node.right_child is not None:
            yield from self.pre_order(node.right_child)

    def __len__(self):
        return self.break_point_counts

    def consistency_test(self):
        # test
        if len(self) == 0:
            assert self.root is None or isinstance(self.root, Site)
        else:
            minimum = self.get_min_value_node(self.root)
            assert minimum.left_nbr == None
            count = 0

            previous_node = None
            for node in self.pre_order(self.root):
                assert minimum is node
                if node.left_child is not None:
                    assert node.left_child.parent is node
                if node.right_child is not None:
                    assert node.right_child.parent is node

                if previous_node is not None:
                    assert previous_node.right_nbr is node
                    assert node.left_nbr is previous_node

                node_x, node_y = node.payload.get_coordinates(self.y)

                if node.left_nbr is not None:
                    assert node.payload.left_lower_site is node.left_nbr.payload.left_higher_site
                    left_nbr_x, left_nbr_y = node.left_nbr.payload.get_coordinates(self.y)
                    assert left_nbr_x < node_x or math.isclose(node_x, left_nbr_x, abs_tol=1e-5)

                if node.right_nbr is not None:
                    assert node.right_nbr.left_nbr is node
                    assert node.payload.left_higher_site is node.right_nbr.payload.left_lower_site
                    right_nbr_x, right_nbr_y = node.right_nbr.payload.get_coordinates(self.y)
                    assert node_x < right_nbr_x or math.isclose(node_x, right_nbr_x, abs_tol=1e-5)

                try:
                    ldelta = node.payload.left_higher_site.get_parabola_derivative(node_x, self.y)
                    assert node.payload.left_higher_site.get_parabola_derivative(node_x, self.y) < \
                           node.payload.left_lower_site.get_parabola_derivative(node_x, self.y)
                except ZeroDivisionError:
                    # then the newly inserted site is a vertical line
                    assert math.isclose(node.payload.left_higher_site.y, self.y, abs_tol=1e-5) or \
                           math.isclose(node.payload.left_lower_site.y, self.y, abs_tol=1e-5)

                minimum = minimum.right_nbr
                count += 1
            assert minimum is None
            assert count == len(self)

    def plot(self):
        if len(self) == 0:
            pass
        else:
            mmin = self.get_min_value_node(self.root)
            mmax = self.get_max_value_node(self.root)

            x = np.linspace(mmin.eval(self.y) - 1, mmax.eval(self.y) + 1, 5000)
            # plot all parabolas
            for site in self.sites():
                if math.isclose(site.y, self.y, abs_tol=1e-5):
                    plt.axvline(x=site.x)
                else:
                    y = site.get_parabola_y(x, self.y)
                    plt.plot(x, y)

            for node in self.pre_order(self.root):
                x, y = node.payload.get_coordinates(self.y)
                plt.plot([x], [y], marker='o', markersize=3, color="red")
                plt.annotate(f"{x:.1f},{y:.1f}", (x, y))

            for site in self.sites():
                x, y = site.x, site.y
                plt.plot([x], [y], marker='o', markersize=3, color="green")
                plt.annotate(f"{x:.1f}, {y:.1f}", (x, y))
        plt.show()

    def sites(self):
        sites = set()
        for node in self.pre_order(self.root):
            sites.add(node.payload.left_lower_site)
            sites.add(node.payload.left_higher_site)

        return sites

    def __iter__(self):
        yield from self.pre_order(self.root)
