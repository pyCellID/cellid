# Real time-course images

Crop of the sample images distributed with [pyCellID](https://github.com/pyCellID/pyCellID)
(`samples_cellid`): a yeast time course (2019-10-21, strain YPP5932), position 1.

| | |
| --- | --- |
| Time points | 1, 2, 3 |
| Channels | BF (bright field), YFP, CFP |
| Region | pixels [0:512, 0:512] of the 1040 x 1392 originals |
| Format | 16-bit TIFF, lossless zlib compression |

`expected/out_all` is the output of Cell-ID 1.5.0 (rcell2-cellid `93e7f09`) with
`tests/data/parameters.txt`. Regenerate the images with `tests/generar_datos_reales.py`
and the reference with `python -m pytest --update-golden`.
