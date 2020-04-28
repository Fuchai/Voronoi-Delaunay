from pathlib import Path

import matplotlib.pyplot as plt
import pylab as pl
from matplotlib import collections  as mc

from dcel import *


class DelaunayFromVoronoi:
    def __init__(self):
        self.dcel = DCEL()
        self.uf = Face(self.dcel)
        self.uf.name = "uf"
        self.triangles = 1
        self.t_centers = []

    def convert(self, voro_dcel, sites):
        delau_vertices = {}
        # every voronoi site is a delaunay vertex
        for site in sites:
            delau_vertices[site.name] = Vertex(self.dcel, site.x, site.y, name=site.name)

        delau_edges = {}
        unbounded_count = 0
        for voro_vertex in voro_dcel.vertices:
            if voro_vertex.name[0] == "v":
                # v_num=int(voro_vertex.name[1:])
                delau_cell = Face(self.dcel, name="t" + str(self.triangles))
                self.triangles += 1
                voro_cells_around = voro_vertex.counter_clockwise_around()
                assert (len(voro_cells_around) == 3), "Is it not a triangulation? Why are there more than three edges?"
                x_avg = 0
                y_avg = 0
                # create the edges and twin edges of this triangle
                for i in range(len(voro_cells_around)):
                    from_v_name = "p" + voro_cells_around[i - 1].name[1:]
                    to_v_name = "p" + voro_cells_around[i].name[1:]
                    edge_name = from_v_name + "," + to_v_name
                    from_v = delau_vertices[from_v_name]
                    to_v = delau_vertices[to_v_name]
                    x_avg += to_v.x
                    y_avg += to_v.y
                    if edge_name not in delau_edges:
                        edge = HalfEdge(self.dcel, from_v, incident_face=delau_cell)
                        if from_v.incident_edge is None:
                            from_v.incident_edge = edge
                        delau_edges[edge_name] = edge
                        if delau_cell.outer is None:
                            delau_cell.outer = edge
                    else:
                        edge = delau_edges[edge_name]
                        assert edge.incident_face is None
                        edge.incident_face = delau_cell

                    twin_name = to_v_name + "," + from_v_name
                    if twin_name not in delau_edges:
                        twin = HalfEdge(self.dcel, to_v)
                        delau_edges[twin_name] = twin
                    else:
                        twin = delau_edges[twin_name]

                    edge.twin = twin
                    twin.twin = edge

                x_avg /= len(voro_cells_around)
                y_avg /= len(voro_cells_around)
                self.t_centers.append(("t" + str(self.triangles - 1), x_avg, y_avg))

                # wire prev and next
                for i in range(len(voro_cells_around)):
                    from_v_name = "p" + voro_cells_around[i - 2].name[1:]
                    to_v_name = "p" + voro_cells_around[i - 1].name[1:]
                    edge_name = from_v_name + "," + to_v_name
                    edge = delau_edges[edge_name]

                    from_v_name = "p" + voro_cells_around[i - 3].name[1:]
                    to_v_name = "p" + voro_cells_around[i - 2].name[1:]
                    edge_name = from_v_name + "," + to_v_name
                    prev_edge = delau_edges[edge_name]

                    from_v_name = "p" + voro_cells_around[i - 1].name[1:]
                    to_v_name = "p" + voro_cells_around[i].name[1:]
                    edge_name = from_v_name + "," + to_v_name
                    next_edge = delau_edges[edge_name]

                    edge.prev_edge = prev_edge
                    edge.next_edge = next_edge
            else:
                assert voro_vertex.name[0] == "b"
                border_num = int(voro_vertex.name[1:])
                if border_num > 4:
                    unbounded_count += 1

        unbounded = [None] * unbounded_count
        for voro_vertex in voro_dcel.vertices:
            if voro_vertex.name[0] == "b":
                border_num = int(voro_vertex.name[1:])
                if border_num > 4:
                    from_v_f = voro_vertex.incident_edge.twin.incident_face
                    to_v_f = voro_vertex.incident_edge.incident_face
                    from_v_name = "p" + from_v_f.name[1:]
                    to_v_name = "p" + to_v_f.name[1:]
                    edge_name = from_v_name + "," + to_v_name
                    try:
                        unbounded[border_num - 5] = delau_edges[edge_name]
                    except KeyError:
                        print("All sites are colinear")
                        return

        # remember it is sorted counter-clockwise
        for i in range(len(unbounded)):
            from_edge = unbounded[i]
            if self.uf.inner is None:
                self.uf.inner = [from_edge]
            to_edge = unbounded[i - 1]
            to_edge.prev_edge = from_edge
            from_edge.next_edge = to_edge
            from_edge.incident_face = self.uf

        print("****** Delaunay triangulation ******")
        print(repr(self.dcel))

    def plot(self):
        def vertex_to_color(vertex):
            cm = plt.cm.get_cmap("tab10")
            site_num = int(vertex.name[1:])
            color = cm(1. * site_num / len(self.dcel.vertices))
            return color

        # plot dcel
        dcel = self.dcel
        fig, ax = pl.subplots()

        for vertex in self.dcel.vertices:
            ax.plot([vertex.x], [vertex.y], marker='o', markersize=3, color=vertex_to_color(vertex))
            ax.annotate(s=str(vertex), xy=(vertex.x, vertex.y), xytext=(2, 4), textcoords='offset points')

        for name, x, y in self.t_centers:
            ax.annotate(s=name, xy=(x, y))

        lines = []
        for edge in dcel.edges:
            try:
                lines.append([(edge.origin.x, edge.origin.y), (edge.destination.x, edge.destination.y)])
            except AttributeError:
                raise

        lc = mc.LineCollection(lines)
        ax.add_collection(lc)

        ax.set_aspect('equal', 'box')
        fig.set_size_inches(8, 8)
        # ax.set(xlim=(self.b1.x - 1, self.b3.x + 1), ylim=(self.b1.y - 1, self.b3.y + 1))

        fig.savefig(Path("animation") / "delau.png")
