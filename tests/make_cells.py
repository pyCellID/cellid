"""Genera imágenes de campo claro sintéticas con células de forma conocida.

Cada célula es una región "interior" (verdad conocida) rodeada por un anillo
oscuro, como en una imagen de campo claro levemente desenfocada. Se guardan
imágenes TIFF de 16 bits y una tabla con la verdad de cada célula.
"""
import json
import sys
from pathlib import Path

import numpy as np
import tifffile
from scipy import ndimage as ndi

BG = 36000      # fondo
INSIDE = 38000  # interior de la célula
RING = 22000    # anillo oscuro (borde)
NOISE = 600     # desvío del ruido gaussiano
RING_W = 2      # ancho del anillo en píxeles


def shape_mask(kind, size, angle, cx, cy, yy, xx):
    """Máscara booleana de la célula en coordenadas (yy, xx)."""
    ca, sa = np.cos(angle), np.sin(angle)
    u = (xx - cx) * ca + (yy - cy) * sa     # eje mayor
    v = -(xx - cx) * sa + (yy - cy) * ca    # eje menor
    if kind == "circle":
        return u**2 + v**2 <= size**2
    if kind == "ellipse":
        return (u / (1.6 * size))**2 + (v / (0.75 * size))**2 <= 1
    if kind == "budding":  # madre + brote
        mother = u**2 + v**2 <= size**2
        bud = (u - 1.45 * size)**2 + v**2 <= (0.65 * size)**2
        return mother | bud
    if kind == "shmoo":  # célula con proyección de apareamiento
        body = u**2 + v**2 <= size**2
        tip = (u > 0) & (u < 2.0 * size) & (np.abs(v) <= 0.35 * size * (1.2 - u / (2.4 * size)))
        return body | tip
    raise ValueError(kind)


def make_image(kinds, angles, size, n_side, spacing, seed, noise=NOISE):
    rng = np.random.default_rng(seed)
    side = n_side * spacing
    yy, xx = np.mgrid[0:side, 0:side].astype(float)
    img = np.full((side, side), float(BG))
    truth = []
    k = 0
    for r in range(n_side):
        for c in range(n_side):
            kind = kinds[k % len(kinds)]
            ang = angles[k % len(angles)]
            # pequeño corrimiento subpíxel para no alinear todo con la grilla
            cx = c * spacing + spacing / 2 + rng.uniform(-0.5, 0.5)
            cy = r * spacing + spacing / 2 + rng.uniform(-0.5, 0.5)
            inner = shape_mask(kind, size, ang, cx, cy, yy, xx)
            ring = ndi.binary_dilation(inner, iterations=RING_W) & ~inner
            img[ring] = RING
            img[inner] = INSIDE
            perim_pix = ndi.binary_dilation(inner) & ~inner  # anillo de 1 px exterior
            truth.append(dict(kind=kind, angle_deg=round(float(np.degrees(ang)), 2),
                              cx=float(cx), cy=float(cy),
                              area_inner=int(inner.sum()),
                              area_inner_plus_ring1=int((inner | perim_pix).sum())))
            k += 1
    img += rng.normal(0, noise, img.shape)
    img = np.clip(img, 0, 65535).astype(np.uint16)
    return img, truth


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    all_truth = {}
    # Experimento 1: mismas formas rotadas en 24 ángulos (0 a 345 grados)
    angles = np.radians(np.arange(0, 360, 15))
    for i, kind in enumerate(["circle", "ellipse", "budding", "shmoo"]):
        img, truth = make_image([kind], angles, size=11, n_side=5, spacing=56, seed=10 + i)
        name = f"BF_Position0{i+1}_time01.tif"
        tifffile.imwrite(out / name, img)
        all_truth[name] = truth
    (out / "truth.json").write_text(json.dumps(all_truth, indent=1))
    print("ok", list(all_truth))
