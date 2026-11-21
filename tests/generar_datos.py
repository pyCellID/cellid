"""Genera las imágenes sintéticas de tests/data (se ejecuta una sola vez;
las imágenes generadas se guardan en el repositorio).

Requiere: numpy, scipy, tifffile.
"""
from pathlib import Path
import numpy as np
import tifffile
import make_cells as mc

DATA = Path(__file__).parent / "data"
DATA.mkdir(exist_ok=True)

angles = np.radians(np.arange(0, 360, 15))
bf, truth = mc.make_image(["circle"], angles, size=11, n_side=5, spacing=56, seed=1)
tifffile.imwrite(DATA / "BF_Position01_time01.tif", bf)

# Fluorescencia: fondo 1000, células 3000 (sin ruido), mismas posiciones
yy, xx = np.mgrid[0:bf.shape[0], 0:bf.shape[1]].astype(float)
fl = np.full(bf.shape, 1000.0)
for t in truth:
    fl[mc.shape_mask(t["kind"], 11, np.radians(t["angle_deg"]), t["cx"], t["cy"], yy, xx)] = 3000
tifffile.imwrite(DATA / "YFP_Position01_time01.tif", fl.astype(np.uint16))
print("ok:", len(truth), "células")

# Reference statistics for tests/test_threshold.sh (double precision)
EXPECTED = DATA / "expected"
EXPECTED.mkdir(exist_ok=True)
img = bf.astype(np.float64)
(EXPECTED / "bf_stats.txt").write_text(
    "# Mean and standard deviation of tests/data/BF_Position01_time01.tif,\n"
    "# computed in double precision with NumPy (population std, ddof=0).\n"
    f"mean {img.mean():.10e}\nsd {img.std():.10e}\n")
