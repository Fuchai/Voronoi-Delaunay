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

    def run(self):
        ## init all
        # dcel
        self.dcel = DCEL()
        uf = Face()
        uf.name = "uf"
        self.dcel.faces.append(uf)
        # tree
        self.tree = BeachLineTree(debug=self.debug)
        # queue
        self.queue = EventQueue()
        for site in self.sites:
            self.queue.insert(SiteEvent(site))

        ## work
        while len(self.queue) != 0:
            event = self.queue.pop()
            self.tree.l = event.y
            if event.is_site_event():
                self.handle_site_event(event)
            else:
                self.handle_circle_event(event)

    def handle_site_event(self, site_event):
        self.tree.insert(site_event.site)

        # TODO check if the new site is directly under a break point

        # insert new circle event for triplets (a, b, new) and (new, a, b)


    def handle_circle_event(self, circle_event):

        # check the queue and remove all circle events involving the disappearing arc
        pass

        # check if the new triplets incur new circle events


class EventQueue:
    def __init__(self):
        # maintain ascending
        self.q = []

    def in_place_sort(self):
        sorted(self.q, key=lambda event: event.y)

    def insert(self, event):
        bisect.insort(self.q, event)

    def pop(self):
        return self.q.pop()

    def __len__(self):
        return len(self.q)


class Event:
    def __init__(self, y):
        self.y = y

    def __lt__(self, other):
        return self.y < other.y

    def is_site_event(self):
        return isinstance(self, SiteEvent)


class CircleEvent(Event):
    def __init__(self, y):
        super(CircleEvent, self).__init__(y)


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
