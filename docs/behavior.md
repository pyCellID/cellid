# Cell-ID behaviour catalogue {#behavior}

What Cell-ID 1.5.0 (`src/`) actually does, as established by reading the code and by the
test suite. It is the working base for the final documentation: every statement here is
backed by evidence, and most of them by a test.

## How to use and maintain this catalogue

- **One entry per finding**, with an identifier that never changes: `B` for bugs, `C` for
  characterized behaviour (surprising, but not decided to be wrong), `Q` for open
  questions and `M` for proposed improvements.
- **Every entry says how it is known**: a test (for example `test_geometry.py::test_touching_cells_are_split`), a code reference
  (`src/file.c`, function) or an experiment described in the entry.
- **Tests refer to the entry.** Known-bug tests (`xfail`) quote the identifier in their
  `reason`, so a failing or passing test leads straight to its entry.
- **Statuses:**
  - *kept*: reference behaviour, deliberately not changed.
  - *xfail*: a test asserts the correct behaviour and is expected to fail.
  - *characterized*: a test pins down the current behaviour.
  - *documented*: known from the code, no test yet.
  - *open*: not understood yet.
- When a bug is fixed: update the entry, remove the `xfail` mark and, if results change,
  regenerate the golden references and explain why.

Versions compared: 1.0/1.1 (Nature Methods supplementary source), 1.4.6 (SourceForge,
`cellID-linux`) and 1.5.0 (`rcell2-cellid`, commit `93e7f09`).

## Known bugs

| ID | Summary | Where | Status | Evidence |
| --- | --- | --- | --- | --- |
| B01 | Lower row of the neighbour count tests `d[u3]` three times and never `d[u3±1]` | `segment.c`, `neighboring_points()` | kept | `test_reference.py::test_golden_out_all` fails if fixed; exercise `01_vecinos` |
| B02 | A new channel listed after a repeated one gets the flag of an existing channel | `cell.c`, flag assignment | xfail | `test_inputs.py::test_each_channel_gets_its_own_flag` |
| B03 | `f.bg` is 0 when every background pixel has the same value | `segment.c`, `background_level()` | xfail | `test_fluorescence.py::test_background_of_a_uniform_image` |
| B04 | Unknown parameter names are silently ignored; defaults are used | `cell.c`, parameter parsing | xfail | `test_inputs.py::test_unknown_parameter_is_reported` |
| B05 | A missing parameters file silently uses all defaults | `cell.c`, parameter parsing | xfail | `test_inputs.py::test_missing_parameters_file_is_reported` |
| B06 | `-D` (and `-F`) expect a list of images, but the help says an image; given an image, Cell-ID reads the TIFF as text and crashes | `cell.c`, dark/flat lists and help | xfail | `test_corrections.py::test_dark_given_as_an_image_does_not_crash` |
| B07 | Lists of more than 1000 images are written past the end of fixed arrays | `cell.c`, `max_files` | documented | code reading |
| B08 | `calculate_cut()` squares pixels in float before converting to double and stores the SD as float; one-pass formula gives NaN on large, nearly equal values | `segment.c`, `calculate_cut()` | documented | exercise `02_umbral` |
| B09 | About 20 variables "may be used uninitialized" (compiler warnings) | several files | documented | `make` with `-O2 -Wall` |

### B01 — Neighbour count in `neighboring_points()`

The row below the pixel counts `d[u3]` three times instead of `d[u3]`, `d[u3+1]` and
`d[u3-1]`. Since `make_boundary_list()` moves to the neighbour with the highest count, the
traced contour changes. Present since Cell-ID 1.0.

Impact measured on `samples_cellid` (3 positions × 3 time points, 5046 cells), comparing
with a patched copy: only 17% of contours are identical; `a.tot` changes in 42% of cells
(median 0.34%, p95 1.6%), `perim` in 83% (median 0.51%, p95 6.4%), `fft.stat` in 85%
(median 2.9%, p95 18%); 0.55% of cells change side of the filter `fft.stat < 0.3`;
tracking is almost unaffected. 61% of affected cells differ only within 4 pixels of the
contour's starting point (see C04). Kept because it is the reference behaviour of every
dataset processed so far; fixing it is a joint decision with rcell2 (M01).

### B02 — Channel flags

`flag[i] = flag[i-1] + 1` is used as the default for a new channel, instead of the next
unused number. Listing `YFP_t1, CFP_t1, YFP_t2, RFP_t2` gives flags 0, 1, 0, 1: RFP and
CFP share flag 1 and cannot be told apart in `out_all`. With the usual order (all
channels in every time point, always in the same order) it does not happen.

### B06 — Dark and flat options

The help describes `-D <path>` as "a 'dark' image", but the code opens it as a text list
of images (default `dark.txt`). Passing an image makes `fscanf("%s")` read binary data
into a fixed buffer, and the process is killed by a segmentation fault.

## Characterized behaviour

### Inputs and configuration

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C01 | Without `bf_fl_mapping list`, images are paired by MetaMorph acquisition time; in list mode, line *n* of each list goes together and `time` is written as 0 | code; lists of different length exit with code 3 (`test_inputs.py::test_lists_of_different_length_are_rejected`) |
| C02 | The channel (`flag`) of a fluorescence image is decided by the first three letters of its file name | code; B02; `test_real_data.py::test_each_channel_keeps_its_flag_in_every_time_point` |
| C03 | A flat image is used only for fluorescence images whose names start with the same three letters; otherwise it is ignored with one log line | `test_corrections.py::test_flat_needs_the_same_name_prefix` |
| C04 | A dark image is used for fluorescence images with the same exposure time; images without that metadata all report -999 and therefore match | code; `test_corrections.py::test_dark_image_is_subtracted` |
| C05 | Image paths cannot contain spaces (`fscanf("%s")` splits them) | code |

### Segmentation (`find_cells()`)

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C10 | Two thresholds, `mean ± background_reject_factor × SD`: pixels above the upper one are cell interior, below the lower one cell border, the rest background. The interior must be brighter than the background | code |
| C11 | `calculate_cut()` ignores pixels with value ≤ 0.1 | code; exercise `02_umbral` |
| C12 | Hard-coded constants: background regions over 1000 pixels are background, border regions under 50 pixels become interior, interior regions under 75 pixels are dropped, overlaps over 30% remove a cell, splits ignore paths under 5 pixels. `min_pixels_per_cell` below 75 has no effect | code; `test_geometry.py::test_regions_under_75_pixels_are_never_found` |
| C13 | Cells touching the image edge are discarded | `test_geometry.py::test_cells_touching_the_image_edge_are_discarded` |
| C14 | Touching cells are split where the contour is pinched (`max_dist_over_waist`), unless the cut is long compared with the minor axis (`max_split_over_minor`) | `test_geometry.py::test_touching_cells_are_split` |
| C15 | Cells whose circularity cannot be computed are removed, so `fft.stat = -1` never reaches `out_all` | code |
| C16 | Cells removed from the arrays are replaced by the last one, so `cellID` order depends on internal details: compare cells by position, not by number | code |

### Contours

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C20 | The contour is traced on the background pixels that touch the cell (an outer ring), starting from the cell's leftmost pixel | code; Python emulation matches the C contours exactly |
| C21 | The walk stops when it returns to the first point, or at a dead end within one pixel of it; the first point is not repeated, and every consumer closes the polygon | code |
| C22 | `a.tot` is the filled polygon: the true area plus about half of the dark ring, 12–18% larger than the inner region on synthetic cells | `test_geometry.py::test_area_is_close_to_the_true_area` |
| C23 | `fix_spirals()`, `clean_up_tails()` and `circularize_points()` exist but are never called | code |

### Measurements

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C30 | `perim`, `maj.axis` and `min.axis` are measured on 128 rays from the contour's centroid, not on the pixel chain; on concave cells a ray can miss or cut the contour twice | code |
| C31 | `fft.stat` is the square root of the sum of `|F(ω)|²` for ω > 0 divided by `|F(0)|` (the 2012 protocol is right; the 2007 supplement omits the root) | code |
| C32 | On a flat fluorescence image, every sum is the value times its area, and the annuli are nested | `test_fluorescence.py` |
| C33 | Measurements depend on image orientation: flipping vertically or rotating changes the area of ~83% of real cells (median 0.5%, p95 2%); flipping left-right keeps 81% identical. Fixing B01 does not remove it | experiment on `samples_cellid` (see Q02) |

### Fluorescence corrections and alignment

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C40 | The dark image is subtracted exactly | `test_corrections.py::test_dark_image_is_subtracted` |
| C41 | The flat correction brings a ±20% linear illumination gradient within 1% | `test_corrections.py::test_flat_field_evens_out_the_illumination` |
| C42 | Image alignment finds integer offsets exactly up to about 10 pixels | `test_alignment.py::test_fluorescence_is_realigned_to_the_bright_field` |
| C43 | Alignment is a local search from (0, 0): large shifts (20 pixels with cells 56 pixels apart) end at a wrong offset | `test_alignment.py::test_large_shifts_are_not_recovered` |
| C44 | `align_individual_cells` recovers cells moved up to 2 pixels each | `test_alignment.py::test_each_cell_is_realigned_individually` |
| C45 | No alignment mode changes contours or shapes | `test_alignment.py::test_alignment_never_changes_the_geometry` |
| C46 | `align_individual_cells_boundary` measures ~12% less fluorescence on uniformly fluorescent cells (probably meant for membrane signals) | experiment (see Q03) |

### Nucleus and tracking

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C50 | The nucleus position is found exactly for small nuclei; `f.nucl` is the sum within 4 pixels (49 pixels, `a.nucl`) | `test_nucleus.py` |
| C51 | A nucleus larger than the search disc gives a plateau of equal sums; the first position in scan order (topmost) is kept, so `ypos.nucl` can be one pixel off | experiment |
| C52 | Cells moved a few pixels between time points keep their number | `test_tracking.py` |
| C53 | On the real time course, 87 of 97 cells keep their number through 3 time points | `test_real_data.py::test_most_cells_are_tracked_through_the_time_course` |

### Differences between versions

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C60 | Segmentation and measurements are identical from 1.0 to 1.4.6 (same `out_all` except `time`) | experiment |
| C61 | 1.5.0 accumulates the threshold in double instead of float; contours of ~6% of cells differ by 1–2 pixels from 1.4.6. Applying only that change to 1.4.6 reproduces 1.5.0 exactly | experiment; `test_reference.py::test_threshold_in_double_precision` |
| C62 | 1.4.6 writes `con.vol` twice (57 columns); 1.5.0 writes it once (56) | code |

## Open questions

| ID | Question | What is known |
| --- | --- | --- |
| Q01 | On real images, which step modifies the bright-field image before `calculate_cut()`? | The loader returns the image intact (1222 zero pixels), but the threshold excludes only 540 and the mean matches no simple variant |
| Q02 | Where does the orientation dependence (C33) come from? | Not from B01; the scan-line polygon fill (`y + 0.1`) is a candidate |
| Q03 | What is `align_individual_cells_boundary` meant for? | Lowers the signal of uniformly filled cells (C46) |

## Proposed improvements

Ordered from least to most impact on existing results. Any change that alters results needs
a new reference version, agreed with rcell2.

| ID | Proposal | Fixes | Changes results? |
| --- | --- | --- | --- |
| M01 | Correct the neighbour count | B01 | Yes, most contours slightly |
| M02 | Report unknown parameter names and a missing parameters file | B04, B05 | No |
| M03 | Give a new channel the next unused flag | B02 | Only where B02 occurs |
| M04 | Return the background value when it is uniform | B03 | Only on uniform backgrounds |
| M05 | Bounds checks or dynamic arrays for image lists and file names | B06, B07 | No |
| M06 | Accept an image or a list in `-D`/`-F`, and fix the help | B06 | No |
| M07 | Turn the hard-coded constants into parameters, defaulting to the current values | C12 | No |
| M08 | Square in double, or use a more robust variance algorithm, in `calculate_cut()` | B08 | Possibly, slightly |
| M09 | Initialise the variables flagged by the compiler | B09 | Should not |
| M10 | Choose channels and flat images from explicit lists instead of file-name prefixes | C02, C03 | No |
