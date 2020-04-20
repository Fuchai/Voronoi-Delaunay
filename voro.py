from dcel import *
from input_output import *
from avl_beach import *
import bisect


class Fortune:
    def __init__(self, sites):
        self.dcel = None
        self.tree = None
        self.queue = None
        self.sites = sites
        self.debug = True

        self.max_x = None
        self.max_y = None
        self.min_x = None
        self.min_y = None

    def run(self):
        ## init all
        # dcel
        self.dcel = DCEL()
        uf = Face(self.dcel)
        uf.name = "uf"
        self.dcel.faces.append(uf)

        # create the bounding box
        self.max_x = -float("inf")
        self.max_y = -float("inf")
        self.min_x = float("inf")
        self.min_y = float("inf")

        for site in self.sites:
            if site.x > self.max_x:
                self.max_x = site.x
            if site.x < self.min_x:
                self.min_x = site.x
            if site.y > self.max_y:
                self.max_y = site.y
            if site.y < self.min_y:
                self.min_y = site.y

        box_border = 1
        b1 = Vertex(self.dcel, self.min_x - box_border, self.min_y - box_border, None, "b1")
        b2 = Vertex(self.dcel, self.max_x + box_border, self.min_y - box_border, None, "b2")
        b3 = Vertex(self.dcel, self.max_x + box_border, self.max_y + box_border, None, "b3")
        b4 = Vertex(self.dcel, self.min_x - box_border, self.max_y + box_border, None, "b4")
        self.dcel.naive_polygon([b1, b2, b3, b4], uf, "bounding box")

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
            self.tree.l = event.y
            if event.is_site_event():
                self.handle_site_event(event)
            else:
                self.handle_circle_event(event)

    def handle_site_event(self, site_event):
        new_site = site_event.site
        left_new_node, right_new_node = self.tree.insert(new_site)

        # as a site parabola pierce through an existing arc (middle of a triplet), the previous triplets were nullified
        old_arc = right_new_node.right_nbr.payload
        # remove the circle events demarcating this arc, because the previous triplet is not longer consecutive
        # false alarm
        self.queue.remove(old_arc.circle_event)
        old_arc.circle_event = None

        # TODO check if the new site is directly under a break point

        # insert new circle event for triplets (a, b, new) and (new, b, a)
        b_node = left_new_node.left_nbr
        if b_node is not None:
            insert_circle_event_if_exists(left_new_node, self.queue)

        b_node = right_new_node.right_nbr
        if b_node is not None:
            insert_circle_event_if_exists(b_node, self.queue)

        # DCEL manipulation
        new_site.cell_face = Face(self.dcel, name="c" + new_site.name)
        old_site = old_arc.site_of_arc()

        # generate two new edges
        old_site_edge = HalfEdge(self.dcel)
        new_site_edge = HalfEdge(self.dcel)
        old_site_edge.incident_face = old_site.cell_face
        new_site_edge.incident_face = new_site.cell_face
        old_site_edge.twin = new_site_edge
        new_site_edge.twin = old_site_edge
        left_new_node.payload.half_edge = new_site_edge
        right_new_node.payload.half_edge = old_site_edge

        new_site.outer = new_site_edge

    def handle_circle_event(self, circle_event):

        # check the queue and remove all circle events involving the disappearing arc
        old_arc = circle_event.vanishing_arc_right_break_point
        self.queue.remove(circle_event)
        old_arc.circle_event = None
        aln = self.tree.delete(old_arc)
        assert circle_event.vanishing_arc_left_break_point is aln.payload
        left_arc = aln.payload
        right_arc = aln.right_nbr.payload
        if left_arc.circle_event is not None:
            self.queue.remove(left_arc.circle_event)
            left_arc.circle_event = None
        if right_arc.circle_event is not None:
            self.queue.remove(right_arc.circle_event)
            right_arc.circle_event = None

        # check if the new triplets incur new circle events
        insert_circle_event_if_exists(left_arc, self.queue)
        insert_circle_event_if_exists(right_arc, self.queue)

        # DCEL manipulation
        center, _ = circle_center_radius(circle_event.a, circle_event.b, circle_event.b)
        new_vertex = Vertex(x=center[0], y=center[1])
        e_left_from = aln.half_edge.twin
        e_left_to = aln.half_edge
        e_right_from = old_arc.half_edge.twin
        e_right_to = old_arc.half_edge

        new_vertex.incident_edge = e_left_from

        assert e_left_from.origin is None
        e_left_from.origin = new_vertex
        assert e_right_from.origin is None
        e_right_from.origin = new_vertex

        assert e_left_to.next_edge is None
        e_left_to.next_edge = e_right_from
        assert e_right_from.prev_edge is None
        e_right_from.prev_edge = e_left_to

        # convergence creates a new edge, which needs to be updated
        new_from = HalfEdge(self.dcel, origin=new_vertex)
        new_to = HalfEdge(self.dcel)
        new_from.twin = new_to
        new_to.twin = new_from

        assert new_from.prev_edge is None
        new_from.prev_edge = e_right_to
        assert e_right_to.next_edge is None
        e_right_to.next_edge = new_from
        assert new_to.next_edge is None
        new_to.next_edge = e_left_from
        assert e_left_from.prev_edge is None
        e_left_from.prev_edge = new_to

        if e_right_to.origin is None:
            # then this edge is unbounded
            k, c = bisector(old_arc.left_lower_site, old_arc.left_higher_site)
            # the unbounded edge might intersect left, top or right border
            # top
            xx = (self.max_y - c) / k
            if self.min_x < xx < self.max_x:
                self.border_vertices_queue["top"].add(Comparable(Vertex(self.dcel, x=xx, y=self.max_y), "x"))
            else:
                # left
                yy = k * self.min_x + c
                if new_vertex.y < yy:
                    self.border_vertices_queue["left"].add(Comparable(Vertex(self.dcel, x=self.min_x, y=yy), "y"))
                else:
                    # right
                    yy = k * self.max_x + c
                    if new_vertex.y < yy:
                        self.border_vertices_queue["right"].add(Comparable(Vertex(self.dcel, x=self.max_x, y=yy), "y"))
                    else:
                        raise ValueError("Why does this edge not have an origin?")


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

    radius = math.sqrt((o1[0] - a[0]) ** 2 + (o1[1] - a[1]) ** 2)
    center = o1
    return center, radius


def bisector(a, b):
    """

    :param a:
    :param b:
    :return: the slope and the intercept
    """

    try:
        # point
        ax, ay = a
        bx, by = b
    except TypeError:
        ax, ay = a.x, a.y
        bx, by = b.x, b.y
    if math.isclose(ax, bx):
        return 0, (by + ay) / 2
    ab_delta = (ay - by) / (ax - bx)
    k = -1 / ab_delta
    c = (ay + by) / 2 - k * (ax + bx) / 2

    return k, c


def intersect(kcline1, kcline2):
    k1, c1 = kcline1
    k2, c2 = kcline2
    return (c2 - c1) / (k1 - k2)


class Comparable:
    def __init__(self, obj, key):
        self.obj = obj
        self.key = key

    def __lt__(self, other):
        return getattr(self.obj, self.key) < getattr(other, self.key)


class EventQueue:
    def __init__(self):
        # maintain ascending
        self.q = []

    def in_place_sort(self):
        sorted(self.q, key=lambda event: getattr(event, self.key))

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


class Event:
    def __init__(self, y):
        self.y = y

    def __lt__(self, other):
        return self.y < other.y

    def is_site_event(self):
        return isinstance(self, SiteEvent)


def insert_circle_event_if_exists(vanishing_arc_right_node, queue):
    vanishing_arc_left_break_point = vanishing_arc_right_node.left_nbr.payload
    vanishing_arc_right_break_point = vanishing_arc_right_node.payload

    b = vanishing_arc_left_break_point.left_higher_site
    assert b is vanishing_arc_right_break_point.left_lower_site

    a = vanishing_arc_left_break_point.left_lower_site
    c = vanishing_arc_right_break_point.left_higher_site

    clp_x, clp_y = circle_lowest_point(a, b, c)

    if points_are_close((clp_x, clp_y), (b.x, b.y)):
        raise NotImplementedError("The site is directly below a breakpoint")
    else:
        if clp_y < b.y:
            ce = CircleEvent(vanishing_arc_left_break_point, vanishing_arc_right_break_point, a, b, c, clp_y)
            assert vanishing_arc_right_break_point.circle_event is None
            vanishing_arc_right_break_point.circle_event = ce
            queue.add(ce)
            return ce
        elif math.isclose(clp_y, b.y):
            raise NotImplementedError("Tangent new site")
        else:
            return None


class CircleEvent(Event):
    def __init__(self, vanishing_arc_left_break_point, vanishing_arc_right_break_point, a, b, c, clp_y):
        self.vanishing_arc_left_break_point = vanishing_arc_left_break_point
        self.vanishing_arc_right_break_point = vanishing_arc_right_break_point

        self.a = a
        self.b = b
        self.c = c

        assert self.vanishing_arc_right_break_point.circle_event is None
        super(CircleEvent, self).__init__(clp_y)


class SiteEvent(Event):
    def __init__(self, site):
        super(SiteEvent, self).__init__(site.y)
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
