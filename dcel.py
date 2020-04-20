from adapters import *


class DCEL:
    def __init__(self, demo=False):
        self.vertices = []
        self.faces = []
        self.edges = []

        self.demo = demo
        if self.demo:
            face = Face(self)
            face.name = "f" + repr(len(self.faces) + 1)

    def naive_polygon(self, vertices, out_face, name=None):
        """
        Insert a polygon by a list of vertices
        This function is for testing only.
        :param out_face: The out-face of the polygon
        :param vertices:
        :return:
        """

        assert (isinstance(vertices, list))
        for vertex in vertices:
            assert (isinstance(vertex, Vertex))

        in_face = Face(self)
        if name is None:
            in_face.name = "f" + repr(len(self.faces) + 1)
        else:
            in_face.name=name
        # make edges

        edge_num = len(self.edges) + 1

        in_edges = []
        out_edges = []

        for i in range(len(vertices)):
            from_vertex = vertices[i]
            if i + 1 < len(vertices):
                to_vertex = vertices[i + 1]
            else:
                to_vertex = vertices[0]

            in_edge = HalfEdge(self, from_vertex)
            out_edge = HalfEdge(self, to_vertex)
            in_edge.name = "e" + str(edge_num) + ",1"
            out_edge.name = "e" + str(edge_num) + ",2"
            edge_num += 1

            in_edge.twin = out_edge
            out_edge.twin = in_edge

            in_edge.incident_face = in_face
            out_edge.incident_face = out_face

            in_edges.append(in_edge)
            out_edges.append(out_edge)

            from_vertex.incident_edge = in_edge

        for i in range(len(vertices)):
            in_edges[i - 1].next_edge = in_edges[i]
            out_edges[i - 1].prev_edge = out_edges[i]

            in_edges[i].prev_edge = in_edges[i - 1]
            out_edges[i].next_edge = out_edges[i - 1]

        if out_face.inner is not None:
            out_face.inner.append(out_edges[0])
        else:
            out_face.inner = [out_edges[0]]

        # connect all
        in_face.outer = in_edges[0]

        # self.vertices += vertices
        # self.edges += in_edges + out_edges

    def __repr__(self):
        string = ""
        for v in self.vertices:
            string += repr(v) + "\n"
        string += "\n"
        for f in self.faces:
            string += repr(f) + "\n"
        string += "\n"
        for e in self.edges:
            string += repr(e) + "\n"
        return string


class Vertex:
    def __init__(self, dcel, x=None, y=None, incident_edge=None, name=None):
        self.x = x
        self.y = y
        self.incident_edge = incident_edge
        self.name = name
        self.dcel = dcel
        self.dcel.vertices.append(self)

    def assert_complete(self):
        assert (None not in [self.x, self.y, self.incident_edge])

    def __repr__(self):
        try:
            return f"{self.name}  ({self.x},  {self.y})  {self.incident_edge.name}"
        except AttributeError:
            return str(self)

    def __str__(self):
        return self.name


class Face:
    def __init__(self, dcel, outer=None, inners=None, name=None):
        self.outer = outer
        self.inner = inners
        self.name = name
        self.dcel = dcel
        self.dcel.faces.append(self)

    def assert_complete(self):
        assert self.outer is not None
        assert self.inner is not None

    def __repr__(self):
        try:
            n = "nil"
            s = f"{self.name}  {self.outer.name if self.outer is not None else n}"
            if self.inner is not None:
                for i in self.inner:
                    s += "  " + i.name
            else:
                s += "  nil"
            return s
        except AttributeError:
            return str(self)

    def __str__(self):
        return self.name


class HalfEdge:
    def __init__(self, dcel, origin=None, twin=None, incident_face=None, next_edge=None, prev_edge=None, name=None):
        self.origin = origin
        self.twin = twin
        self.incident_face = incident_face
        self.next_edge = next_edge
        self.prev_edge = prev_edge
        self.name = name
        self.dcel = dcel
        self.dcel.edges.append(self)

    def assert_complete(self):
        for i in (self.origin, self.twin, self.incident_face, self.next_edge, self.prev_edge):
            assert i is not None

    def __repr__(self):
        try:
            return f"{self.name}  {self.origin.name}  {self.twin.name}  {self.incident_face.name}  {self.next_edge.name}  {self.prev_edge.name}"
        except AttributeError:
            return str(self)

    def __str__(self):
        return self.name
