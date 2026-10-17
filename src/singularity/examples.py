"""Explicit seven-vertex examples, with original labels retained."""

from .graph import Graph

GRAPHS = {
    "spectral_g": Graph(7, ((0, 1), (0, 2), (0, 3), (0, 4), (1, 2), (3, 5), (3, 6))),
    "spectral_h": Graph(7, ((0, 1), (0, 2), (0, 3), (0, 4), (1, 5), (1, 6), (5, 6))),
    "binary_g": Graph(7, ((0, 3), (0, 4), (0, 6), (1, 2), (1, 3), (2, 3), (2, 4), (3, 5))),
    "binary_h": Graph(7, ((0, 1), (0, 4), (0, 6), (1, 5), (1, 6), (2, 6), (3, 6), (4, 5))),
}
