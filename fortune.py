from dcel import *
from input_output import *
from avl_beach import *
import bisect
from matplotlib import collections  as mc
import pylab as pl


class Fortune:
    def __init__(self, sites):
        self.dcel = None
        self.tree = None
        self.queue = None
        self.sites = sites
        self.debug = True

        self.cell_site = {}
        self.vertex_count = 1
        self._horizontal_co_linear = []

    def run(self):
        ## init all
        # dcel
        self.dcel = DCEL()
        uf = Face(self.dcel)
        uf.name = "uf"
        self.dcel.faces.append(uf)

        # create the bounding box
        max_x = -float("inf")
        max_y = -float("inf")
        min_x = float("inf")
        min_y = float("inf")

        for site in self.sites:
            if site.x > max_x:
                max_x = site.x
            if site.x < min_x:
                min_x = site.x
            if site.y > max_y:
                max_y = site.y
            if site.y < min_y:
                min_y = site.y

        diam = max_x - min_x
        if max_y - min_y > diam:
            diam = max_y - min_y
        center_x = (max_x + min_x) / 2
        center_y = (max_y + min_y) / 2

        box_border = 1
        self.b1 = Vertex(self.dcel, center_x - diam / 2 - box_border, center_y - diam / 2 - box_border, None, "b1")
        self.b2 = Vertex(self.dcel, center_x + diam / 2 + box_border, center_y - diam / 2 - box_border, None, "b2")
        self.b3 = Vertex(self.dcel, center_x + diam / 2 + box_border, center_y + diam / 2 + box_border, None, "b3")
        self.b4 = Vertex(self.dcel, center_x - diam / 2 - box_border, center_y + diam / 2 + box_border, None, "b4")
        self.dcel.naive_polygon([self.b1, self.b2, self.b3, self.b4], uf, "bounding box")

        # we use event queue to store the points on the box so that we achieve O(log n) performance
        self.border_vertices_queue = {"top": EventQueue(),
                                      "left": EventQueue(),
                                      "right": EventQueue(),
                                      "bottom": EventQueue()}

        # tree
        self.tree = BeachLineTree(debug=self.debug)
        # queue
        self.queue = EventQueue()
        for site in self.sites:
            self.queue.add(SiteEvent(site))

        ## work
        while len(self.queue) != 0:
            event = self.queue.pop()
            if self.debug:
                self.tree.consistency_test()
            self.tree.l = event.y
            self.plot(event)
            if self.debug:
                self.tree.consistency_test()
            self.plot(event)
            if event.is_site_event():
                self.handle_site_event(event)
            else:
                self.handle_circle_event(event)
            self.plot(event)

        # get unbounded edges again
        # insert bounding box vertices
        self.finish_unbounded_edges()

        # self.label_bounding_box()

        self.plot(final=True)

    def insert_horizontal_colinear(self):
        sites = sorted(self._horizontal_co_linear, key=lambda site: site.x)
        breakpoints = self.tree.insert_horizontal_colinear(sites)
        # add parallel edges between the cells.
        if len(breakpoints)!=0:
            bp=None
            from_edge=None
            for i in range(len(breakpoints)):
                bp = breakpoints[i]
                left_site = sites[i]
                right_site = sites[i + 1]

                to_edge = HalfEdge(self.dcel)
                from_edge = HalfEdge(self.dcel)
                to_edge.twin = from_edge
                from_edge.twin = to_edge

                # DCEL manipulation
                bp.site.cell = Face(self.dcel, name="c" + bp.site.name[1:])
                self.cell_site[bp.site.cell] = bp.site
                bp.site.cell.outer=from_edge

                origin = Vertex(self.dcel, x=(left_site.x + right_site.x) / 2, y=self.b3.y, incident_edge=to_edge,
                                name="bb")
                to_edge.origin = origin
                to_edge.incident_face = right_site
                from_edge.incident_face = left_site

                bp.half_edge = to_edge
                from_edge=to_edge

            # set the last site
            bp.site.cell = Face(self.dcel, name="c" + bp.site.name[1:])
            self.cell_site[bp.site.cell] = bp.site
            bp.site.cell.outer = from_edge
        else:
            site=sites[0]
            site.cell = Face(self.dcel, name="c" + site.name[1:])
            self.cell_site[site.cell] = site
            # bp.site.cell.outer = from_edge
            # TODO check this
        self._horizontal_co_linear = None

    def handle_site_event(self, site_event):
        if self._horizontal_co_linear is not None:
            if len(self._horizontal_co_linear) == 0:
                self._horizontal_co_linear.append(site_event.site)
                return
            elif self._horizontal_co_linear[0].y == site_event.site.y:
                self._horizontal_co_linear.append(site_event.site)
                return
            else:
                # co_linear broken
                self.insert_horizontal_colinear()

        new_site = site_event.site
        left_new_node, right_new_node = self.tree.insert(new_site)

        if len(self.tree) > 0:
            if right_new_node.right_nbr is not None:
                # as a site parabola pierce through an existing arc (middle of a triplet),
                # the previous triplets were nullified
                old_arc = right_new_node.right_nbr.payload
                # remove the circle events demarcating this arc, because the previous triplet is not longer consecutive
                if old_arc.circle_event is not None:
                    self.queue.remove(old_arc.circle_event)
                    old_arc.circle_event = None

            # # check if directly under an arc
            # if left_new_node.left_higher_site is right_new_node.left_lower_site:
            #     directly_under_an_arc=True
            # else:
            #     directly_under_an_arc=False

            # insert new circle event for triplets (a, b, new) and (new, b, a)
            insert_circle_event_if_exists(left_new_node, self.queue)

            b_node = right_new_node.right_nbr
            if b_node is not None:  # and not directly_under_an_arc:
                insert_circle_event_if_exists(b_node, self.queue)

            # DCEL manipulation
            new_site.cell = Face(self.dcel, name="c" + new_site.name[1:])
            self.cell_site[new_site.cell] = new_site

            # generate two new edges
            old_site = right_new_node.payload.left_lower_site
            old_site_edge = HalfEdge(self.dcel)
            new_site_edge = HalfEdge(self.dcel)
            old_site_edge.incident_face = old_site.cell
            new_site_edge.incident_face = new_site.cell
            old_site_edge.twin = new_site_edge
            new_site_edge.twin = old_site_edge
            left_new_node.payload.half_edge = new_site_edge
            right_new_node.payload.half_edge = old_site_edge

            new_site.outer = new_site_edge

        else:
            # the first site
            new_site.cell = Face(self.dcel, name="c" + new_site.name[1:])
            self.cell_site[new_site.cell] = new_site

    def handle_circle_event(self, circle_event):

        # check the queue and remove all circle events involving the disappearing arc
        old_arc = circle_event.vanishing_arc_right_break_point
        old_arc.circle_event = None
        old_site = old_arc.arc_to_site()
        aln = self.tree.delete(old_arc)
        assert circle_event.vanishing_arc_left_break_point is aln.payload
        # arc to the left and right of the old_arc
        left_arc = aln.payload
        if aln.right_nbr is not None:
            right_arc = aln.right_nbr.payload
            if right_arc.circle_event is not None:
                self.queue.remove(right_arc.circle_event)
                right_arc.circle_event = None
        if left_arc.circle_event is not None:
            self.queue.remove(left_arc.circle_event)
            left_arc.circle_event = None

        # check if the new triplets incur new circle events
        insert_circle_event_if_exists(aln, self.queue)
        if aln.right_nbr is not None:
            insert_circle_event_if_exists(aln.right_nbr, self.queue)

        # DCEL manipulation
        center, _ = circle_center_radius(circle_event.a, circle_event.b, circle_event.c)
        new_vertex = Vertex(self.dcel, x=center[0], y=center[1], name="v" + str(self.vertex_count))
        self.vertex_count += 1

        left_edge_to = left_arc.half_edge
        right_edge_to = old_arc.half_edge

        left_edge_to.twin.origin = new_vertex
        right_edge_to.twin.origin = new_vertex

        # create new pair
        new_edge_from = HalfEdge(self.dcel, origin=new_vertex)
        new_edge_to = HalfEdge(self.dcel)
        new_edge_from.twin = new_edge_to
        new_edge_to.twin = new_edge_from

        # set right cell
        new_edge_from.prev_edge = right_edge_to
        right_edge_to.next_edge = new_edge_from
        new_edge_from.incident_face = right_edge_to.incident_face

        # set left cell
        new_edge_to.next_edge = left_edge_to.twin
        left_edge_to.twin.prev_edge = new_edge_to
        new_edge_to.incident_face = left_edge_to.twin.incident_face

        # finish up cell
        left_edge_to.next_edge = right_edge_to.twin
        right_edge_to.twin.prev_edge = left_edge_to

        assert left_edge_to.incident_face is not None
        assert right_edge_to.incident_face is not None

        left_arc.half_edge = new_edge_from
        # self.finish_unbounded_edges_helper(left_edge_to, left_arc.left_higher_site, left_arc.left_lower_site, bottom=False)
        # self.finish_unbounded_edges_helper(right_edge_to, old_site, left_arc.left_higher_site, bottom=False)

        for break_point, unbound_edge, left_site, right_site in \
                zip((left_arc, old_arc), (left_edge_to, right_edge_to),
                    (left_arc.left_lower_site, old_site), (old_site, left_arc.left_higher_site)):
            if unbound_edge.origin is None:
                # then this edge is unbounded
                k, c = bisector(left_site, right_site)
                # the unbounded edge might intersect left, top or right border
                # top
                xx = (self.b3.y - c) / k
                if self.b1.x < xx < self.b3.x:
                    vertex = Vertex(self.dcel, x=xx, y=self.b3.y, name="bb")
                    unbound_edge.origin = vertex
                    self.border_vertices_queue["top"].add(Comparable(vertex, "x"))
                else:
                    # left
                    yy = k * self.b1.x + c
                    if new_vertex.y < yy:
                        vertex = Vertex(self.dcel, x=self.b1.x, y=yy, name="bb")
                        unbound_edge.origin = vertex
                        self.border_vertices_queue["left"].add(Comparable(vertex, "y"))
                    else:
                        # right
                        yy = k * self.b3.x + c
                        if new_vertex.y < yy:
                            vertex = Vertex(self.dcel, x=self.b3.x, y=yy, name="bb")
                            unbound_edge.origin = vertex
                            self.border_vertices_queue["right"].add(Comparable(vertex, "y"))
                        else:
                            raise ValueError("Why does this edge not have an origin?")

        # # delete should not touch left_arc.half_edge, despite that its left_higher_site is changed
        # e_left_from = left_arc.half_edge.twin
        # e_left_to = left_arc.half_edge
        # e_right_from = old_arc.half_edge.twin
        # e_right_to = old_arc.half_edge
        #
        # new_vertex.incident_edge = e_left_from
        # assert e_left_from.origin is None
        # e_left_from.origin = new_vertex
        # assert e_right_from.origin is None
        # e_right_from.origin = new_vertex
        #
        # assert e_left_to.next_edge is None
        # e_left_to.next_edge = e_right_from
        # assert e_right_from.prev_edge is None
        # e_right_from.prev_edge = e_left_to
        #
        # # convergence creates a new edge, which needs to be updated
        # new_from = HalfEdge(self.dcel, origin=new_vertex)
        # new_to = HalfEdge(self.dcel)
        # new_from.twin = new_to
        # new_to.twin = new_from
        #
        # assert new_from.prev_edge is None
        # new_from.prev_edge = e_right_to
        # assert e_right_to.next_edge is None
        # e_right_to.next_edge = new_from
        # assert new_to.next_edge is None
        # new_to.next_edge = e_left_from
        # assert e_left_from.prev_edge is None
        # e_left_from.prev_edge = new_to
        #
        # if e_right_to.origin is None:
        #     # then this edge is unbounded
        #     k, c = bisector(old_arc.left_lower_site, old_arc.left_higher_site)
        #     # the unbounded edge might intersect left, top or right border
        #     # top
        #     xx = (self.max_y - c) / k
        #     if self.min_x < xx < self.max_x:
        #         self.border_vertices_queue["top"].add(Comparable(Vertex(self.dcel, x=xx, y=self.max_y, name="bb"), "x"))
        #     else:
        #         # left
        #         yy = k * self.min_x + c
        #         if new_vertex.y < yy:
        #             self.border_vertices_queue["left"].add(Comparable(Vertex(self.dcel, x=self.min_x, y=yy, name="bb"), "y"))
        #         else:
        #             # right
        #             yy = k * self.max_x + c
        #             if new_vertex.y < yy:
        #                 self.border_vertices_queue["right"].add(Comparable(Vertex(self.dcel, x=self.max_x, y=yy, name="bb"), "y"))
        #             else:
        #                 raise ValueError("Why does this edge not have an origin?")

    def plot(self, event=None, final=False):
        # plot dcel
        dcel = self.dcel
        plt.figure()
        lines = []
        for edge in dcel.edges:
            try:
                lines.append([(edge.origin.x, edge.origin.y), (edge.destination.x, edge.destination.y)])
            except AttributeError:
                pass

        lc = mc.LineCollection(lines)
        fig, ax = pl.subplots()
        ax.add_collection(lc)
        # ax.set_aspect('equal', 'box')

        ax.set(xlim=(self.b1.x - 1, self.b3.x + 1), ylim=(self.b1.y - 1, self.b3.y + 1))
        for vertex in self.dcel.vertices:
            ax.plot([vertex.x], [vertex.y], marker='o', markersize=3, color="red")
        for cell, site in self.cell_site.items():
            ax.plot([site.x], [site.y], marker='o', markersize=3, color="purple")

        if not final:
            if len(self.tree) != 0:
                # plot the current beach line
                left_x = self.b1.x - 1
                last_node = None
                for node in self.tree:
                    # repeatedly plot the left site
                    bp = node.payload
                    right_x, y = bp.get_coordinates(self.tree.l)
                    ax.plot([right_x], [y], marker='o', markersize=3, color="green")
                    site = bp.left_lower_site
                    x = np.linspace(left_x, right_x, 5000)
                    left_x = right_x
                    if math.isclose(site.y, self.tree.l):
                        ax.axvline(x=site.x)
                    else:
                        y = site.get_parabola_y(x, self.tree.l)
                        ax.plot(x, y)
                    last_node = node

                    # plot unfinished edges
                    try:
                        lines.append([(bp.half_edge.origin.x, bp.half_edge.origin.y), (right_x, y)])
                    except AttributeError:
                        pass

                # plot the last site
                site = last_node.payload.left_higher_site
                x = np.linspace(left_x, self.b3.x + 1, 5000)
                if math.isclose(site.y, self.tree.l):
                    ax.axvline(x=site.x)
                else:
                    y = site.get_parabola_y(x, self.tree.l)
                    ax.plot(x, y)

            # plot the sweeping line
            ax.axhline(y=self.tree.l)
            if event:
                ax.plot([event.x], [event.y], marker='X', markersize=3, color="red")
        fig.set_size_inches(8, 8)
        fig.show()

    def finish_unbounded_edges_helper(self, unbound_edge, incident_site, co_site, bottom=True):
        origin = ((incident_site.x + co_site.x) / 2, (incident_site.y + co_site.y) / 2)
        incident_co = (co_site.x - incident_site.x, co_site.y - incident_site.y)

        vector = (-incident_co[1], incident_co[0])
        a, b = origin
        c, d = vector
        border_vertex = None
        maxx = self.b3.x
        maxy = self.b3.y
        minx = self.b1.x
        miny = self.b1.y
        if c > 0:
            # right
            intercept = d / c * (maxx - a) + b
            if miny <= intercept < maxy:
                border_vertex = Vertex(self.dcel, x=maxx, y=intercept, name="bbb")
                unbound_edge.destination = border_vertex
                self.border_vertices_queue["right"].add(Comparable(border_vertex, "y"))
        if c < 0:
            # left
            intercept = d / c * (minx - a) + b
            if miny < intercept <= maxy:
                assert border_vertex is None
                border_vertex = Vertex(self.dcel, x=minx, y=intercept, name="bbb")
                unbound_edge.destination = border_vertex
                self.border_vertices_queue["left"].add(Comparable(border_vertex, "y"))
        if d > 0:
            # top
            intercept = c / d * (maxy - b) + a
            if minx < intercept <= maxx:
                assert border_vertex is None
                border_vertex = Vertex(self.dcel, x=intercept, y=maxy, name="bbb")
                unbound_edge.destination = border_vertex
                self.border_vertices_queue["top"].add(Comparable(border_vertex, "x"))
        if bottom:
            if d < 0:
                # bottom
                intercept = c / d * (miny - b) + a
                if minx <= intercept < maxx:
                    assert border_vertex is None
                    border_vertex = Vertex(self.dcel, x=intercept, y=miny, name="bbb")
                    unbound_edge.destination = border_vertex
                    self.border_vertices_queue["bottom"].add(Comparable(border_vertex, "x"))
            assert border_vertex is not None

    def finish_unbounded_edges(self):
        if self._horizontal_co_linear:
            self.insert_horizontal_colinear()

        for node in self.tree:
            break_point = node.payload
            unbound_edge = break_point.half_edge
            incident_site = break_point.left_higher_site
            co_site = break_point.left_lower_site
            if unbound_edge.destination is None:
                self.finish_unbounded_edges_helper(unbound_edge, incident_site, co_site)
            if unbound_edge.origin is None:
                self.finish_unbounded_edges_helper(unbound_edge.twin, co_site, incident_site)

    # def finish_unbounded_edges(self):
    #     if self._horizontal_co_linear:
    #         self.insert_horizontal_colinear()
    #
    #     for node in self.tree:
    #         break_point = node.payload
    #         unbound_edge = break_point.half_edge
    #         # assert unbound_edge.origin is not None
    #         # I cannot assert it, because of the co-linear case,
    #         # unbounded edge can only be discovered in the end.
    #         origin = unbound_edge.origin
    #         left_site, right_site = break_point.left_lower_site, break_point.left_higher_site
    #         if unbound_edge.destination is None:
    #             # then this edge is unbounded
    #             k, c = bisector(break_point.left_lower_site, break_point.left_higher_site)
    #             if c is None:
    #                 # if k is infinity
    #                 xx = (break_point.left_lower_site.x + break_point.left_higher_site.x) / 2
    #                 vertex = Vertex(self.dcel, x=xx, y=self.b1.y, name="bbb")
    #                 break_point.half_edge.destination = vertex
    #                 self.border_vertices_queue["bottom"].add(Comparable(vertex, "x"))
    #             else:
    #                 # the unbounded edge might intersect left, top or right border
    #                 # bottom
    #                 try:
    #                     xx = (self.b1.y - c) / k
    #                     if self.b1.x < xx < self.b3.x:
    #                         vertex = Vertex(self.dcel, x=xx, y=self.b1.y, name="bbb")
    #                         break_point.half_edge.destination = vertex
    #                         self.border_vertices_queue["bottom"].add(Comparable(vertex, "x"))
    #                     else:
    #                         # left
    #                         yy = k * self.b1.x + c
    #                         if break_point.half_edge.y < yy:
    #                             vertex = Vertex(self.dcel, x=self.b1.x, y=yy, name="bbb")
    #                             break_point.half_edge.destination = vertex
    #                             self.border_vertices_queue["left"].add(Comparable(vertex, "y"))
    #                         else:
    #                             # right
    #                             yy = k * self.b3.x + c
    #                             if origin.y < yy:
    #                                 vertex = Vertex(self.dcel, x=self.b3.x, y=yy, name="bbb")
    #                                 break_point.half_edge.destination = vertex
    #                                 self.border_vertices_queue["right"].add(Comparable(vertex, "y"))
    #                             else:
    #                                 raise ValueError("Why does this edge not have a destination?")
    #                 except ZeroDivisionError:
    #                     # horizontal edge
    #                     incident_y = break_point.left_higher_site.y
    #                     opposite_y = break_point.left_lower_site.y
    #                     if break_point.left_lower_site.y < break_point.left_higher_site.y:
    #                         # unbounded edge pointing left
    #                         vertex = Vertex(self.dcel, x=self.b1.x, y=(incident_y + opposite_y) / 2, name="bbb")
    #                         unbound_edge.destination = vertex
    #                         self.border_vertices_queue["left"].add(Comparable(vertex, "y"))
    #                     else:
    #                         # unbounded edge pointing left
    #                         vertex = Vertex(self.dcel, x=self.b3.x, y=(incident_y + opposite_y) / 2, name="bbb")
    #                         unbound_edge.destination = vertex
    #                         self.border_vertices_queue["right"].add(Comparable(vertex, "y"))

    def label_bounding_box(self):
        directions = ["bottom", "right", "top", "left"]
        origins = [self.b1, self.b2, self.b3, self.b4]

        for i, direction in enumerate(directions):
            queue = self.border_vertices_queue[direction]
            origin = origins[i]
            edge = origin.incident_edge
            outer = edge.twin
            if i % 2 == 0:
                iter = queue
            else:
                iter = reversed(queue)

            for border_node in iter:
                pass


# plot the bounding boxes
def colinear(a, b, c):
    ab = (b.x - a.x, b.y - a.y)
    bc = (c.x - b.x, c.y - b.y)
    inner = ab[0] * bc[0] + ab[1] * bc[1]

    ablen = ab[0] * ab[0] + ab[1] * ab[1]
    ablen = math.sqrt(ablen)

    bclen = bc[0] * bc[0] + bc[1] * bc[1]
    bclen = math.sqrt(bclen)

    sin = inner / ablen / bclen

    if math.isclose(sin, -1) or math.isclose(sin, 1):
        return True
    else:
        return False


def points_are_close(point1, point2):
    return math.isclose(point1[0], point2[0]) and math.isclose(point1[1], point2[1])


def circle_lowest_point(a, b, c):
    center, radius = circle_center_radius(a, b, c)
    return center[0], center[1] - radius


def circle_center_radius(a, b, c):
    bisect_ab = bisector(a, b)
    bisect_bc = bisector(b, c)
    bisect_ac = bisector(a, c)

    o1 = intersect(bisect_ab, bisect_bc)
    o2 = intersect(bisect_ab, bisect_ac)
    o3 = intersect(bisect_bc, bisect_ac)

    assert math.isclose(o1[0], o2[0]) and math.isclose(o1[0], o3[0]) and \
           math.isclose(o1[1], o2[1]) and math.isclose(o2[1], o3[1])
    if isinstance(a, Site):
        radius = math.sqrt((o1[0] - a.x) ** 2 + (o1[1] - a.y) ** 2)
    else:
        radius = math.sqrt((o1[0] - a[0]) ** 2 + (o1[1] - a[1]) ** 2)
    center = o1
    return center, radius


def bisector(a, b):
    """

    :param a:
    :param b:
    :return: the slope and the intercept
    """

    if isinstance(a, Site) and isinstance(b, Site):
        ax, ay = a.x, a.y
        bx, by = b.x, b.y
    else:
        # point
        ax, ay = a
        bx, by = b
    if math.isclose(ax, bx):
        return 0, (by + ay) / 2
    ab_delta = (ay - by) / (ax - bx)
    try:
        k = -1 / ab_delta
    except ZeroDivisionError:
        return float("inf"), None
    c = (ay + by) / 2 - k * (ax + bx) / 2

    return k, c


def intersect(kcline1, kcline2):
    k1, c1 = kcline1
    k2, c2 = kcline2
    x = (c2 - c1) / (k1 - k2)
    y = k1 * x + c1
    yy = k2 * x + c2
    assert math.isclose(y, yy)
    return x, y


class Comparable:
    def __init__(self, obj, key):
        self.obj = obj
        self.key = key

    def __lt__(self, other):
        return getattr(self.obj, self.key) < getattr(other.obj, self.key)


class EventQueue:
    def __init__(self):
        # maintain ascending
        self.q = []

    def in_place_sort(self):
        sorted(self.q)

    def add(self, event):
        bisect.insort(self.q, event)

    def pop(self):
        return self.q.pop()

    def __len__(self):
        return len(self.q)

    def remove(self, event):
        i = bisect.bisect_left(self.q, event)
        assert event is self.q[i]
        self.q.pop(i)

    def __iter__(self):
        yield from iter(self.q)

    def __reversed__(self):
        yield from reversed(self.q)


class Event:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __lt__(self, other):
        return self.y < other.y

    def is_site_event(self):
        return isinstance(self, SiteEvent)


def insert_circle_event_if_exists(vanishing_arc_right_node, queue):
    if vanishing_arc_right_node.left_nbr is not None:
        vanishing_arc_left_break_point = vanishing_arc_right_node.left_nbr.payload
        vanishing_arc_right_break_point = vanishing_arc_right_node.payload

        b = vanishing_arc_left_break_point.left_higher_site
        assert b is vanishing_arc_right_break_point.left_lower_site

        a = vanishing_arc_left_break_point.left_lower_site
        c = vanishing_arc_right_break_point.left_higher_site
        if a is c:
            return None
        if not colinear(a, b, c):
            clp_x, clp_y = circle_lowest_point(a, b, c)

            if points_are_close((clp_x, clp_y), (b.x, b.y)):
                raise NotImplementedError("The site is directly below a breakpoint")
            else:
                # if middle vanishes
                if vanishing_arc_right_break_point.left_lower_site is vanishing_arc_left_break_point.left_higher_site:
                    ce = CircleEvent(vanishing_arc_left_break_point, vanishing_arc_right_break_point, a, b, c, clp_x, clp_y)
                    assert vanishing_arc_right_break_point.circle_event is None
                    vanishing_arc_right_break_point.circle_event = ce
                    queue.add(ce)
                    return ce
                elif math.isclose(clp_y, b.y):
                    raise NotImplementedError("Tangent new site")


class CircleEvent(Event):
    def __init__(self, vanishing_arc_left_break_point, vanishing_arc_right_break_point, a, b, c, clp_x, clp_y):
        self.vanishing_arc_left_break_point = vanishing_arc_left_break_point
        self.vanishing_arc_right_break_point = vanishing_arc_right_break_point

        self.a = a
        self.b = b
        self.c = c

        assert self.vanishing_arc_right_break_point.circle_event is None
        super(CircleEvent, self).__init__(clp_x, clp_y)


class SiteEvent(Event):
    def __init__(self, site):
        super(SiteEvent, self).__init__(site.x, site.y)
        self.site = site

    def __str__(self):
        return "event" + str(self.site)


def main():
    sites = [(0, 1), (-1, 0), (1, 0)]
    sites = [Site(x, y) for x, y in sites]
    for site in sites:
        print(site)

    fortune = Fortune(sites)
    fortune.run()


if __name__ == '__main__':
    main()
