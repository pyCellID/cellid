"""Regenerates the real time-course images of tests/data/real.

They are a crop of the sample images of pyCellID (``samples_cellid``):
position 1, time points 1 to 3, bright field (BF) and two fluorescence
channels (YFP, CFP), pixels [0:512, 0:512], saved with lossless zlib
compression. Cell-ID gives byte-for-byte the same out_all with the compressed
and the uncompressed crops.

Usage: python tests/generar_datos_reales.py /path/to/pyCellID/samples_cellid
"""

import sys
from pathlib import Path

import tifffile

SOURCE = Path(sys.argv[1])
DEST = Path(__file__).parent / "data" / "real"
DEST.mkdir(parents=True, exist_ok=True)

for time in ("01", "02", "03"):
    for channel in ("BF", "YFP", "CFP"):
        name = f"{channel}_Position01_time{time}.tif"
        crop = tifffile.imread(SOURCE / name)[0:512, 0:512]
        tifffile.imwrite(DEST / name, crop, compression="zlib")
print(f"ok: images written to {DEST}")
