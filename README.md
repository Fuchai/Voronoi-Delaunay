### Dependencies
python 3.6 and above for Path library
Python ```numpy```, ```pylab```, ```matplotlib```


### Entry Point

Your entry point is ```main.py```. 
Put the file in the directory. Animation plot is in ```./animation/``` directory.
DCEL output is in ```./voronoi.txt```.

### Project Structure

```dcel.py``` implements doubly connected edge list

```avl_beac.py``` implements the beach line tree with AVL tree.
Deletion and self-balancing is implemented.

```fortune.py``` constructs the Voronoi diagram.

```delau.py``` constructs the Delaunay diagram from the Voronoi class 
that finishes the construction of Voronoi diagram.