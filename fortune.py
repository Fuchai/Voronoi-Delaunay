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

        self.max_x = -float("inf")
        self.max_y = -float("inf")
        self.min_x = float("inf")
        self.min_y = float("inf")
        self.diam = None
        self.box_border = 4
        self.border_vertices_queue = None
        self.uf = None

    def run(self):
        ## init all
        # dcel
        self.dcel = DCEL()
        self.uf = Face(self.dcel)
        self.uf.name = "uf"

        # create the bounding box for now, this will not be the final bounding box.

        for site in self.sites:
            if site.x > self.max_x:
                self.max_x = site.x
            if site.x < self.min_x:
                self.min_x = site.x
            if site.y > self.max_y:
                self.max_y = site.y
            if site.y < self.min_y:
                self.min_y = site.y

        self.diam = self.max_x - self.min_x
        if self.max_y - self.min_y > self.diam:
            self.diam = self.max_y - self.min_y
        center_x = (self.max_x + self.min_x) / 2
        center_y = (self.max_y + self.min_y) / 2

        self.b1 = Vertex(self.dcel, center_x - self.diam / 2 - self.box_border,
                         center_y - self.diam / 2 - self.box_border, None,
                         "b1")
        self.b2 = Vertex(self.dcel, center_x + self.diam / 2 + self.box_border,
                         center_y - self.diam / 2 - self.box_border, None,
                         "b2")
        self.b3 = Vertex(self.dcel, center_x + self.diam / 2 + self.box_border,
                         center_y + self.diam / 2 + self.box_border, None,
                         "b3")
        self.b4 = Vertex(self.dcel, center_x - self.diam / 2 - self.box_border,
                         center_y + self.diam / 2 + self.box_border, None,
                         "b4")
        self.dcel.naive_polygon([self.b1, self.b2, self.b3, self.b4], self.uf, "bounding box", face=False)

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
                self.consistency_test()
            self.tree.y = event.y
            if self.debug:
                self.consistency_test()
            self.plot(event)
            if event.is_site_event():
                self.handle_site_event(event)
            else:
                self.handle_circle_event(event)
            if self.debug:
                self.consistency_test()
            self.plot(event)

        # get unbounded edges again
        # insert bounding box vertices
        self.finish_unbounded_edges_on_beach_line()

        self.redo_bounding_box()

        self.label_bounding_box()

        self.plot(final=True, arrow=False)
        print(repr(self.dcel))

    def insert_horizontal_colinear(self):
        sites = sorted(self._horizontal_co_linear, key=lambda site: site.x)
        breakpoints = self.tree.insert_horizontal_colinear(sites)
        # add parallel edges between the cells.
        if len(breakpoints) != 0:
            bp = None
            to_edge = None
            for i in range(len(breakpoints)):
                bp = breakpoints[i]
                left_site = sites[i]
                right_site = sites[i + 1]

                to_edge = HalfEdge(self.dcel)
                from_edge = HalfEdge(self.dcel)
                to_edge.twin = from_edge
                from_edge.twin = to_edge

                # DCEL manipulation
                bp.left_lower_site.cell = Face(self.dcel, name="c" + bp.left_lower_site.name[1:])
                self.cell_site[bp.left_lower_site.cell] = bp.left_lower_site
                bp.left_lower_site.cell.outer = from_edge
                to_edge.incident_face = right_site
                from_edge.incident_face = left_site
                left_site.cell.outer = from_edge
                right_site.cell.outer = to_edge
                bp.half_edge = to_edge

                # origin = Vertex(self.dcel, x=(left_site.x + right_site.x) / 2, y=self.b3.y, incident_edge=to_edge,
                #                 name="bb")
                # to_edge.origin = origin

                self.finish_unbounded_edges_helper(from_edge, left_site, right_site)
                # from_edge=to_edge

            # set the last site
            bp.left_higher_site.cell = Face(self.dcel, name="c" + bp.left_higher_site.name[1:])
            self.cell_site[bp.left_higher_site.cell] = bp.left_higher_site
            bp.left_higher_site.cell.outer = to_edge
        else:
            site = sites[0]
            site.cell = Face(self.dcel, name="c" + site.name[1:])
            self.cell_site[site.cell] = site
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
            self.insert_circle_event_if_exists(left_new_node, self.queue)

            b_node = right_new_node.right_nbr
            if b_node is not None:  # and not directly_under_an_arc:
                self.insert_circle_event_if_exists(b_node, self.queue)

            # DCEL manipulation
            new_site.cell = Face(self.dcel, name="c" + new_site.name[1:])
            self.cell_site[new_site.cell] = new_site

            # generate two new edges
            old_site = right_new_node.payload.left_higher_site
            old_site_edge = HalfEdge(self.dcel)
            new_site_edge = HalfEdge(self.dcel)
            old_site_edge.incident_face = old_site.cell
            new_site_edge.incident_face = new_site.cell

            old_site_edge.twin = new_site_edge
            new_site_edge.twin = old_site_edge
            left_new_node.payload.half_edge = new_site_edge
            right_new_node.payload.half_edge = old_site_edge

            new_site.cell.outer = new_site_edge
            if old_site.cell.outer is None:
                old_site.cell.outer = old_site_edge
            self.uf.inner.append(old_site_edge)

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
        self.insert_circle_event_if_exists(aln, self.queue)
        if aln.right_nbr is not None:
            self.insert_circle_event_if_exists(aln.right_nbr, self.queue)

        # DCEL manipulation
        center, _ = circle_center_radius(circle_event.a, circle_event.b, circle_event.c)
        new_vertex = Vertex(self.dcel, x=center[0], y=center[1], name="v" + str(self.vertex_count))
        if self.max_x < center[0]:
            self.max_x = center[0]
        if self.min_x > center[0]:
            self.min_x = center[0]
        if self.max_y < center[1]:
            self.max_y = center[1]
        if self.min_y > center[1]:
            self.min_y = center[1]
        self.vertex_count += 1

        left_edge_to = left_arc.half_edge
        right_edge_to = old_arc.half_edge

        new_vertex.incident_edge = left_edge_to.twin

        for edge in (left_edge_to, right_edge_to):
            if edge.destination is not None:
                border_vertex = edge.destination
                # remove the border node from the queue as well as dcel
                queue_name = border_vertex.name
                self.border_vertices_queue[queue_name].remove(Comparable(border_vertex, "y"))
                self.dcel.vertices.remove(border_vertex)

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

        if left_edge_to.origin is None:
            self.finish_unbounded_edges_helper(left_edge_to.twin, left_arc.left_lower_site, old_site)
        if right_edge_to.origin is None:
            self.finish_unbounded_edges_helper(right_edge_to.twin, old_site, left_arc.left_higher_site)

    def insert_circle_event_if_exists(self, vanishing_arc_right_node, queue):
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
                center, radius = circle_center_radius(a, b, c)
                # check if the breakpoints converge: head
                converge = True
                for left, right in ((a, b), (b, c)):
                    vector_ab = (right.x - left.x, right.y - left.y)
                    mid = ((left.x + right.x) / 2, (right.y + left.y) / 2)
                    vector_cc = (center[0] - mid[0], center[1] - mid[1])
                    cp = cross_product(vector_ab, vector_cc)
                    if cp > 0:
                        converge = False

                if converge and clp_y < self.tree.y:
                    if points_are_close((clp_x, clp_y), (b.x, b.y)):
                        raise NotImplementedError("The site is directly below a breakpoint")
                    else:
                        # if middle vanishes
                        if vanishing_arc_right_break_point.left_lower_site is vanishing_arc_left_break_point.left_higher_site:
                            ce = CircleEvent(vanishing_arc_left_break_point, vanishing_arc_right_break_point, a, b, c,
                                             clp_x, clp_y)
                            assert vanishing_arc_right_break_point.circle_event is None
                            vanishing_arc_right_break_point.circle_event = ce
                            queue.add(ce)
                            return ce
                        elif math.isclose(clp_y, b.y):
                            raise NotImplementedError("Tangent new site")

    def plot(self, event=None, final=False, arrow=False):
        def site_to_color(site):
            cm = plt.cm.get_cmap("tab10")
            site_num = int(site.name[1:])
            color = cm(1. * site_num / len(self.sites))
            return color

        # plot dcel
        dcel = self.dcel
        fig, ax = pl.subplots()

        lines = []
        for edge in dcel.edges:
            try:
                if arrow:
                    ax.arrow(edge.origin.x, edge.origin.y, edge.destination.x - edge.origin.x,
                             edge.destination.y - edge.origin.y,
                             head_width=self.diam / 20, head_length=self.diam / 10, ec=None, fc=None,
                             length_includes_head=True)
                else:
                    lines.append([(edge.origin.x, edge.origin.y), (edge.destination.x, edge.destination.y)])
            except AttributeError:
                if final:
                    raise
                else:
                    pass

        for vertex in self.dcel.vertices:
            ax.plot([vertex.x], [vertex.y], marker='o', markersize=3, color="red")
            ax.annotate(s=str(vertex), xy=(vertex.x, vertex.y), xytext=(2, 4), textcoords='offset points')

        for cell, site in self.cell_site.items():
            ax.plot([site.x], [site.y], marker='o', markersize=3, color=site_to_color(site))
            ax.annotate(s=str(site), xy=(site.x, site.y), xytext=(-4, -10), textcoords='offset points')

        if not final:
            if len(self.tree) != 0:
                # plot the current beach line
                left_x = None
                last_node = None
                right_x = None
                for node in self.tree:
                    # repeatedly plot the left site
                    bp = node.payload
                    right_x, right_y = bp.get_coordinates(self.tree.y)
                    site = bp.left_lower_site
                    ax.plot([right_x], [right_y], marker='o', markersize=3, color="green")
                    ax.annotate(s=bp.left_lower_site.name + " " + bp.left_higher_site.name, xy=(right_x, right_y),
                                xytext=(-3, -3), textcoords='offset points')
                    if left_x is None:
                        left_x = right_x - 1
                    x = np.linspace(left_x, right_x, 5000)
                    left_x = right_x
                    if math.isclose(site.y, self.tree.y):
                        ax.axvline(x=site.x)
                    else:
                        color = site_to_color(site)
                        y = site.get_parabola_y(x, self.tree.y)
                        ax.plot(x, y, color=color)
                    last_node = node

                    # plot unfinished edges
                    try:
                        lines.append([(bp.half_edge.origin.x, bp.half_edge.origin.y), (right_x, right_y)])
                    except AttributeError:
                        pass

                # plot the last site
                site = last_node.payload.left_higher_site
                x = np.linspace(left_x, right_x + 1, 5000)
                if math.isclose(site.y, self.tree.y):
                    ax.axvline(x=site.x)
                else:
                    y = site.get_parabola_y(x, self.tree.y)
                    ax.plot(x, y, color=site_to_color(site))

            # plot the sweeping line
            ax.axhline(y=self.tree.y)
            if event:
                ax.plot([event.x], [event.y], marker='X', markersize=3,
                        color="red" if not isinstance(event, SiteEvent) else site_to_color(event.site))

        lc = mc.LineCollection(lines)
        ax.add_collection(lc)

        ax.set_aspect('equal', 'box')
        fig.set_size_inches(8, 8)
        # ax.set(xlim=(self.b1.x - 1, self.b3.x + 1), ylim=(self.b1.y - 1, self.b3.y + 1))

        fig.show()

    def finish_unbounded_edges_helper(self, unbound_edge, incident_site, co_site):

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
        payload = (unbound_edge, incident_site, co_site)

        if c > 0:
            # right
            intercept = d / c * (maxx - a) + b
            if miny <= intercept < maxy:
                border_vertex = Vertex(self.dcel, x=maxx, y=intercept, name="right")
                unbound_edge.destination = border_vertex
                border_vertex.incident_edge = unbound_edge.twin
                self.border_vertices_queue["right"].add(Comparable(border_vertex, "y", payload))
        if c < 0:
            # left
            intercept = d / c * (minx - a) + b
            if miny < intercept <= maxy:
                assert border_vertex is None
                border_vertex = Vertex(self.dcel, x=minx, y=intercept, name="left")
                unbound_edge.destination = border_vertex
                border_vertex.incident_edge = unbound_edge.twin
                self.border_vertices_queue["left"].add(Comparable(border_vertex, "y", payload))

        if d > 0:
            # top
            intercept = c / d * (maxy - b) + a
            if minx < intercept <= maxx:
                assert border_vertex is None
                border_vertex = Vertex(self.dcel, x=intercept, y=maxy, name="top")
                unbound_edge.destination = border_vertex
                border_vertex.incident_edge = unbound_edge.twin
                self.border_vertices_queue["top"].add(Comparable(border_vertex, "x", payload))

        if d < 0:
            # bottom
            intercept = c / d * (miny - b) + a
            if minx <= intercept < maxx:
                assert border_vertex is None
                border_vertex = Vertex(self.dcel, x=intercept, y=miny, name="bottom")
                unbound_edge.destination = border_vertex
                border_vertex.incident_edge = unbound_edge.twin
                self.border_vertices_queue["bottom"].add(Comparable(border_vertex, "x", payload))
        assert border_vertex is not None

    def finish_unbounded_edges_on_beach_line(self):
        if self._horizontal_co_linear:
            self.insert_horizontal_colinear()
            # this means all nodes are horizontally co-linear

        for node in self.tree:
            break_point = node.payload
            unbound_edge = break_point.half_edge
            incident_site = break_point.left_higher_site
            co_site = break_point.left_lower_site
            if unbound_edge.destination is None:
                self.finish_unbounded_edges_helper(unbound_edge, incident_site, co_site)
            if unbound_edge.origin is None:
                self.finish_unbounded_edges_helper(unbound_edge.twin, co_site, incident_site)

    def label_bounding_box(self):
        directions = ["bottom", "right", "top", "left"]
        origins = [self.b1, self.b2, self.b3, self.b4]

        num = 5

        for i, direction in enumerate(directions):
            queue = self.border_vertices_queue[direction]
            prev_vertex = origins[i]
            prev_edge = prev_vertex.incident_edge

            if i < 2:
                iter = queue
            else:
                iter = reversed(queue)

            # vertex = None
            # edge = None

            for j, cmp in enumerate(iter):
                vertex = cmp.obj
                vertex.name = "b" + str(num)
                num += 1
                edge = HalfEdge(self.dcel)
                twin_edge = HalfEdge(self.dcel)
                twin_edge.incident_face = self.uf
                edge.twin = twin_edge
                twin_edge.twin = edge

                edge.origin = vertex
                prev_edge.destination = vertex

                prev_edge.next_edge = vertex.incident_edge
                vertex.incident_edge.prev_edge = prev_edge

                vertex.incident_edge.twin.next_edge = edge
                edge.prev_edge = vertex.incident_edge.twin

                twin_edge.next_edge = prev_edge.twin
                prev_edge.twin.prev_edge = twin_edge

                prev_edge.incident_face = vertex.incident_edge.incident_face

                prev_edge = edge
                prev_vertex = vertex

            prev_edge.next_edge = origins[(i + 1) % 4].incident_edge
            origins[(i + 1) % 4].incident_edge.prev_edge=prev_edge

            prev_edge.prev_edge = prev_vertex.incident_edge.twin
            prev_vertex.incident_edge.twin.next_edge=prev_edge

            prev_edge.twin.prev_edge = origins[(i + 1) % 4].incident_edge.twin
            origins[(i + 1) % 4].incident_edge.twin.next_edge=prev_edge.twin

            prev_edge.incident_face = prev_vertex.incident_edge.twin.incident_face
            prev_edge.destination = origins[(i + 1) % 4]
            prev_edge.incident_face = prev_vertex.incident_edge.twin.incident_face
            prev_edge.twin.incident_face = prev_edge.twin.next_edge.incident_face

    def redo_bounding_box(self):
        # we do not know the size of the bounding box unless we get all the vertices of the graph
        # need to resize in the end.

        # remove all previous bounding box vertices
        args = []
        for dir, queue in self.border_vertices_queue.items():
            for cmp in queue:
                payload = cmp.payload
                args.append(payload)
                self.dcel.vertices.remove(cmp.obj)

        self.border_vertices_queue = {"top": EventQueue(),
                                      "left": EventQueue(),
                                      "right": EventQueue(),
                                      "bottom": EventQueue()}

        # get new box size
        self.diam = self.max_x - self.min_x
        if self.max_y - self.min_y > self.diam:
            self.diam = self.max_y - self.min_y
        center_x = (self.max_x + self.min_x) / 2
        center_y = (self.max_y + self.min_y) / 2
        self.box_border = 1

        self.b1.x = center_x - self.diam / 2 - self.box_border
        self.b1.y = center_y - self.diam / 2 - self.box_border
        self.b2.x = center_x + self.diam / 2 + self.box_border
        self.b2.y = center_y - self.diam / 2 - self.box_border
        self.b3.x = center_x + self.diam / 2 + self.box_border
        self.b3.y = center_y + self.diam / 2 + self.box_border
        self.b4.x = center_x - self.diam / 2 - self.box_border
        self.b4.y = center_y + self.diam / 2 + self.box_border

        # call unbound edge helper again
        for unbound_edge, incident_site, co_site in args:
            self.finish_unbounded_edges_helper(unbound_edge, incident_site, co_site)

    def consistency_test(self):
        self.tree.consistency_test()
        for edge in self.dcel.edges:
            if edge.origin is not None and edge.destination is not None:
                assert not (math.isclose(edge.origin.x, edge.destination.x) and
                            math.isclose(edge.origin.y, edge.destination.y))


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
    def __init__(self, obj, key, payload=None):
        self.obj = obj
        self.key = key
        self.payload = payload

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
        element = self.q[i]
        if isinstance(event, Comparable):
            assert element.obj is event.obj
        else:
            assert event is element
        return self.q.pop(i)

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


def cross_product(vec1, vec2):
    return vec1[0] * vec2[1] - vec1[1] * vec2[0]


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
