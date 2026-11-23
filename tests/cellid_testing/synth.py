"""Synthetic bright-field and fluorescence images with known ground truth.

A synthetic cell is an "inner" region (the ground truth) surrounded by a dark
ring, as in a slightly defocused bright-field image. Images are 16-bit, like
the camera images Cell-ID processes.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi

#: Default intensities of a synthetic bright-field image.
BACKGROUND = 36000
INSIDE = 38000
RING = 22000
NOISE_SD = 600
RING_WIDTH = 2

KINDS = ("circle", "ellipse", "budding", "shmoo")


@dataclass(frozen=True)
class Cell:
    """A synthetic cell: its shape, size, orientation and centre (pixels)."""

    kind: str
    cx: float
    cy: float
    size: float = 11.0
    angle_deg: float = 0.0

    def mask(self, shape: tuple[int, int]) -> np.ndarray:
        """Boolean mask of the cell's inner region in an image of ``shape``."""
        yy, xx = np.mgrid[0 : shape[0], 0 : shape[1]].astype(float)
        return shape_mask(self.kind, self.size, np.radians(self.angle_deg), self.cx, self.cy, yy, xx)


def shape_mask(kind, size, angle, cx, cy, yy, xx):
    """Boolean mask of a cell of the given kind, in coordinates ``(yy, xx)``."""
    ca, sa = np.cos(angle), np.sin(angle)
    u = (xx - cx) * ca + (yy - cy) * sa  # major axis
    v = -(xx - cx) * sa + (yy - cy) * ca  # minor axis
    if kind == "circle":
        return u**2 + v**2 <= size**2
    if kind == "ellipse":
        return (u / (1.6 * size)) ** 2 + (v / (0.75 * size)) ** 2 <= 1
    if kind == "budding":  # mother + bud
        mother = u**2 + v**2 <= size**2
        bud = (u - 1.45 * size) ** 2 + v**2 <= (0.65 * size) ** 2
        return mother | bud
    if kind == "shmoo":  # cell with a mating projection
        body = u**2 + v**2 <= size**2
        width = 0.35 * size * (1.2 - u / (2.4 * size))
        tip = (u > 0) & (u < 2.0 * size) & (np.abs(v) <= width)
        return body | tip
    raise ValueError(f"unknown cell kind: {kind!r}")


def brightfield(shape, cells, *, noise_sd=NOISE_SD, seed=0, rng=None):
    """Bright-field image with the given cells.

    Each cell's inner region is brighter than the background and surrounded
    by a dark ring of ``RING_WIDTH`` pixels. Gaussian noise is added at the end.
    """
    rng = np.random.default_rng(seed) if rng is None else rng
    img = np.full(shape, float(BACKGROUND))
    for cell in cells:
        inner = cell.mask(shape)
        ring = ndi.binary_dilation(inner, iterations=RING_WIDTH) & ~inner
        img[ring] = RING
        img[inner] = INSIDE
    if noise_sd:
        img += rng.normal(0, noise_sd, img.shape)
    return np.clip(img, 0, 65535).astype(np.uint16)


def fluorescence(shape, cells, *, background=1000, inside=3000):
    """Noise-free fluorescence image: ``inside`` within cells, ``background`` elsewhere."""
    img = np.full(shape, float(background))
    for cell in cells:
        img[cell.mask(shape)] = inside
    return img.astype(np.uint16)


def flat(shape, value):
    """Image with the same value in every pixel."""
    return np.full(shape, value, dtype=np.uint16)


def grid(kind, n_side, spacing, *, size=11.0, angles_deg=(0.0,), jitter=0.5, rng=None, seed=0):
    """Cells of one kind on an ``n_side`` x ``n_side`` grid.

    Each cell is centred in its grid square, shifted by up to ``jitter`` pixels
    so that cells are not aligned with the pixel grid. Orientations cycle
    through ``angles_deg``. Returns the cells and the image shape.
    """
    rng = np.random.default_rng(seed) if rng is None else rng
    cells = []
    k = 0
    for r in range(n_side):
        for c in range(n_side):
            cx = c * spacing + spacing / 2 + rng.uniform(-jitter, jitter)
            cy = r * spacing + spacing / 2 + rng.uniform(-jitter, jitter)
            angle = angles_deg[k % len(angles_deg)]
            cells.append(Cell(kind, cx, cy, size, angle))
            k += 1
    side = n_side * spacing
    return cells, (side, side)


def reference_images():
    """The images stored in ``tests/data`` (25 circles), and their cells.

    Uses one random generator for positions and noise, in that order, so the
    stored images are reproduced exactly.
    """
    rng = np.random.default_rng(1)
    angles = tuple(float(a) for a in np.arange(0, 360, 15))
    cells, shape = grid("circle", 5, 56, angles_deg=angles, rng=rng)
    bf = brightfield(shape, cells, rng=rng)
    fl = fluorescence(shape, cells)
    return bf, fl, cells
