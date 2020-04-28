import shutil
from pathlib import Path

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
    file = "sites.txt"
    sites = read_input(file)
    fortune = Fortune(sites)
    fortune.run()

    dfv = DelaunayFromVoronoi()
    dfv.convert(fortune.dcel, fortune.sites)
    dfv.plot()


if __name__ == '__main__':
    main(overwrite=True)
