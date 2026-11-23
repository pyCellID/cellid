"""Regenerates the reference images of tests/data.

The images are stored in the repository; this script documents how they were
made and lets anyone check that they can be reproduced exactly.

Usage (from the repository root): python tests/generar_datos.py
"""

from pathlib import Path

import tifffile

from cellid_testing import synth

DATA = Path(__file__).parent / "data"

bf, fl, cells = synth.reference_images()
tifffile.imwrite(DATA / "BF_Position01_time01.tif", bf)
tifffile.imwrite(DATA / "YFP_Position01_time01.tif", fl)
print(f"ok: {len(cells)} cells")
