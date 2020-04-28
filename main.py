import shutil

from delau import *
from fortune import *
from input_output import *


def main(overwrite=True):
    ani = Path("animation")
    if ani.exists():
        if overwrite:
            shutil.rmtree(ani)
        else:
            raise FileExistsError("The animation directory exists")
    ani.mkdir()
    output_f = Path("voronoi.txt")
    if output_f.exists():
        if overwrite:
            output_f.unlink()
        else:
            raise FileExistsError("The voronoi.txt exists")
    file = "sites.txt"
    sites = read_input(file)
    fortune = Fortune(sites, dump=True)
    fortune.run()

    dfv = DelaunayFromVoronoi(dump=True)
    dfv.convert(fortune.dcel, fortune.sites)
    dfv.plot()
    print("Output written to ./voronoi.txt")
    print("Animation is in ./animation directory")


if __name__ == '__main__':
    main(overwrite=True)
