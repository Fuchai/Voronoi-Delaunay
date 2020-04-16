class DCEL:
    def __init__(self):
        self.vertices=[]
        self.faces=[]
        self.edges=[]

        face=Face()
        self.add_face(face)

    def add_face(self,face):
        face.name="f"+repr(len(self.faces)+1)
        self.faces.append(face)

    def naive_polygon(self, vertices, out_face):
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

        in_face=Face()
        self.add_face(in_face)
        # make edges

        edge_num=len(self.edges)+1

        in_edges=[]
        out_edges=[]

        for i in range(len(vertices)):
            from_vertex=vertices[i]
            if i+1<len(vertices):
                to_vertex=vertices[i+1]
            else:
                to_vertex=vertices[0]

            in_edge = Edge(from_vertex)
            out_edge = Edge(to_vertex)
            in_edge.name="e"+str(edge_num)+",1"
            out_edge.name="e"+str(edge_num)+",2"
            edge_num+=1

            in_edge.twin = out_edge
            out_edge.twin = in_edge

            in_edge.incident_face = in_face
            out_edge.incident_face = out_face

            in_edges.append(in_edge)
            out_edges.append(out_edge)

            from_vertex.incident_edge=in_edge


        for i in range(len(vertices)):
            in_edges[i-1].next_edge=in_edges[i]
            out_edges[i-1].prev_edge=out_edges[i]

            in_edges[i].prev_edge=in_edges[i-1]
            out_edges[i].next_edge=out_edges[i-1]


        if out_face.inner is not None:
            out_face.inner.append(out_edges[0])
        else:
            out_face.inner=[out_edges[0]]

        # connect all
        in_face.outer=in_edges[0]

        self.vertices+=vertices
        self.edges+=in_edges+out_edges


    def __repr__(self):
        string=""
        for v in self.vertices:
            string+=repr(v)+"\n"
        string+="\n"
        for f in self.faces:
            string+=repr(f)+"\n"
        string+="\n"
        for e in self.edges:
            string+=repr(e)+"\n"
        return string

class Vertex:
    def __init__(self, x=None, y=None, incident_edge=None, name=None):
        self.x = x
        self.y = y
        self.incident_edge = incident_edge
        self.name=name

    def assert_complete(self):
        assert (None not in [self.x, self.y, self.incident_edge])

    def __repr__(self):
        return f"{self.name}  ({self.x},  {self.y})  {self.incident_edge.name}"

    def __str__(self):
        return self.name

class Face:
    def __init__(self, outer=None, inner=None, name=None):
        self.outer = outer
        self.inner = inner
        self.name= name

    def assert_complete(self):
        assert self.outer is not None
        assert self.inner is not None

    def __repr__(self):
        n="nil"
        s=f"{self.name}  {self.outer.name if self.outer is not None else n}"
        if self.inner is not None:
            for i in self.inner:
                s+="  "+ i.name
        else:
            s+="  nil"
        return s

    def __str__(self):
        return self.name

class Edge:
    def __init__(self, origin=None, twin=None, incident_face=None, next_edge=None, prev_edge=None, name=None):
        self.origin = origin
        self.twin = twin
        self.incident_face = incident_face
        self.next_edge = next_edge
        self.prev_edge = prev_edge
        self.name=name

    def assert_complete(self):
        for i in (self.origin, self.twin, self.incident_face, self.next_edge, self.prev_edge):
            assert i is not None

    def __repr__(self):
        return f"{self.name}  {self.origin.name}  {self.twin.name}  {self.incident_face.name}  {self.next_edge.name}  {self.prev_edge.name}"

    def __str__(self):
        return self.name


def run_naive_polygon():
    v1=Vertex(0,0,None,"v1")
    v2=Vertex(1,0,None,"v2")
    v3=Vertex(0,1,None,"v3")

    dcel=DCEL()
    dcel.naive_polygon([v1,v2,v3],dcel.faces[0])

    print(repr(dcel))

if __name__ == '__main__':
    run_naive_polygon()