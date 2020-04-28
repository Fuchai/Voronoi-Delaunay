from pathlib import Path
from avl_beach import *

def read_input(file="sites.txt"):
    f_path = Path(file)
    points=[]
    with f_path.open("r") as f:
        for line in f:
            if line[-1]=='\n':
                line=line[:-1]
            splitted=line.split()
            for i in range(0, len(splitted),2):
                xx=splitted[i]
                yy=splitted[i+1]

                assert xx[0]=="("
                assert xx[-1]==","
                assert yy[-1]==")"
                x=xx[1:]
                x=x[:-1]
                y=yy[:-1]
                x=float(x)
                y=float(y)
                points.append((x,y))
    sites = []
    for i, point in enumerate(points):
        sites.append(Site(x=point[0], y=point[1], name="p" + str(i + 1)))
    return sites