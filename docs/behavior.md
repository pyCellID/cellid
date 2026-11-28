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
| B07 | Lists of more than 1000 images are written past the end of fixed arrays; with 1001 images Cell-ID aborts | `cell.c`, `max_files` | xfail | `test_robustness.py::test_more_than_1000_images_do_not_crash` |
| B08 | `calculate_cut()` squares pixels in float before converting to double and stores the SD as float; one-pass formula gives NaN on large, nearly equal values | `segment.c`, `calculate_cut()` | documented | exercise `02_umbral` |
| B09 | About 20 variables "may be used uninitialized" (compiler warnings) | several files | documented | `make` with `-O2 -Wall` |
| B10 | The month of the standard TIFF DateTime is read one too high: elapsed times are wrong across the end of a month (600 s become 87 000 s at the end of November, 259 800 s at the end of February) | `date_and_time.c`, `get_date_and_time()` | xfail | `test_time_mapping.py::test_elapsed_time_across_the_end_of_a_month` |
| B11 | DateTime texts in other formats (MetaSeries writes `20191021 18:10:26.792`) are read as garbage without a warning; 600 s become 3600 s | `date_and_time.c`, `get_date_and_time()` | xfail | `test_time_mapping.py::test_non_standard_datetime_is_read_or_reported` |
| B12 | The `-t` mask file lists `a.tot - 1` interior pixels per cell: the loop stops before the last list node | `segment.c`, `output_cells_single_file()` | xfail | `test_outputs.py::test_masks_list_every_interior_pixel` |
| B13 | The help says `-l` is enabled by default; the code defaults it to off (without mask options `BF.out.tif` is 8-bit, with no cell numbers encoded) | `cell.c`, help text | documented | `test_outputs.py::test_annotated_image_is_8_bit_without_mask_options` |
| B14 | `append_output` writes the header again, leaving a header line in the middle of `out_all` | `segment.c`, `output_cells_single_file()` | xfail | `test_outputs.py::test_append_output_keeps_a_single_header` |
| B15 | Paths longer than 500 characters overflow a fixed buffer and Cell-ID aborts | `cell.c`, `max_strlen` | xfail | `test_robustness.py::test_long_paths_do_not_crash` |
| B16 | An internal error path of the vacuole search calls `exit(0)`: Cell-ID would stop reporting success | `fl_dist.c`, `find_vacuole()` | documented | code reading |
| B17 | When recombining, `vacuole_area` of the mother is added to itself instead of adding the bud's (`b1->vacuole_area += b1->vacuole_area`): it doubles | `segment.c`, `combine_cells_in_cs_array()` | xfail | `test_recombination.py::test_merged_vacuole_area_is_the_sum` |

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

### B10 and B11 — Acquisition times

Images without the MetaMorph private tag are dated from the standard TIFF DateTime tag,
parsed by fixed character positions. The code adds 1 to the month, with the comment "Does
months as 0 to 11", but the TIFF standard uses 1–12: November 30 becomes "December 30"
and December 1 "month 13". Within a month the error cancels out; across the end of a
month (except December to January) the elapsed time is wrong.

Any other text format is read at the same fixed positions. The lab's images, written by
MetaSeries, store `20191021 18:10:26.792` (no colons, milliseconds) and their processed
bright-field images have no DateTime at all, so time mapping cannot work on them: they
must be processed with `bf_fl_mapping list`, which is what rcell2 does.

### B06 — Dark and flat options

The help describes `-D <path>` as "a 'dark' image", but the code opens it as a text list
of images (default `dark.txt`). Passing an image makes `fscanf("%s")` read binary data
into a fixed buffer, and the process is killed by a segmentation fault.

## Characterized behaviour

### Inputs and configuration

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C01 | Without `bf_fl_mapping list`, fluorescence images are sorted by acquisition time and paired with the closest bright-field image; `time` is the elapsed seconds. In list mode, line *n* of each list goes together and `time` is written as 0 | `test_time_mapping.py`; lists of different length exit with code 3 (`test_inputs.py::test_lists_of_different_length_are_rejected`) |
| C02 | The channel (`flag`) of a fluorescence image is decided by the first three letters of its file name | code; B02; `test_real_data.py::test_each_channel_keeps_its_flag_in_every_time_point` |
| C03 | A flat image is used only for fluorescence images whose names start with the same three letters; otherwise it is ignored with one log line | `test_corrections.py::test_flat_needs_the_same_name_prefix` |
| C04 | A dark image is used for fluorescence images with the same exposure time; images without that metadata all report -999 and therefore match | code; `test_corrections.py::test_dark_image_is_subtracted` |
| C05 | Image paths cannot contain spaces: the lists are read word by word, so the first word cannot be opened (exit code 4) | `test_robustness.py::test_paths_with_spaces_are_split` |
| C06 | Clean failures have their own exit codes: 3 lists of different length, 4 image that cannot be opened (missing, not a TIFF), 6 images of different size, 7 output that cannot be written | `test_robustness.py`, `test_inputs.py` |
| C07 | Empty image lists are not an error: `out_all` has only the header | `test_robustness.py::test_empty_lists_give_an_empty_table` |

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

### Recombination

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C90 | With `do_recombination` and `recombination_fl_per_a_nucleus <flag> <cut>`, a cell without nucleus (`f.nucl / a.nucl - f.bg < cut`) is merged into the neighbouring cell with a nucleus: areas, sums of fluorescence, annuli and volumes are added | `test_recombination.py::test_buds_without_nucleus_are_merged_into_their_mothers` |
| C91 | The merged bud keeps its row and measurements; its `xpos` and `ypos` become `-999 - (mother's cellID)`. Analyses must drop these rows, or the bud is counted twice | `test_recombination.py::test_merged_buds_stay_in_the_table_marked_by_their_position` |
| C92 | `perim` of a merged cell is the sum of both perimeters (including their shared boundary); position and shape statistics keep the mother's values | `test_recombination.py::test_merged_perimeter_is_the_sum_of_perimeters` |
| C93 | `recombination_all_new_cells` treats every cell appearing after the first time point as a bud | `test_recombination.py::test_cells_that_appear_later_are_merged` |
| C94 | Cells under 75 pixels are always considered buds (hard-coded `recombination_min_pixels`) | code |
| C95 | The nucleus criterion uses `f.bg`, so it is affected by B03: on noise-free images (`f.bg = 0`) the same cell scores about 1000 higher | experiment |

### Outputs

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C70 | `-l` writes each contour in `BF.out.tif` with intensity `65535 - cellID - 1`: the same pixels as the contour in the `-t` mask file | `test_outputs.py::test_masks_boundary_is_the_contour_labelled_by_l` |
| C71 | `-i` writes interior and contour with `65535 - cellID - 1`; with `-w` the interior is lowered by an offset (5000 by default) so it can be told from the contour | `test_outputs.py::test_fill_option_encodes_each_whole_cell`, `test_offset_option_separates_interior_from_contour` |
| C72 | `-m` replaces the image by the masks: one value per cell plus the background | `test_outputs.py::test_mask_only_option_removes_the_image` |
| C73 | The interior pixels of the masks include most contour pixels (60 of 78 on a synthetic circle), because the polygon runs through the contour pixels' centres (see C22) | experiment |
| C74 | `paw_output` writes the same numbers as the R format, without header, split into six files | `test_outputs.py::test_paw_output_has_the_same_numbers` |
| C75 | `output_individual_cells` writes a cropped 8-bit image per cell and per image into `cells/` | `test_outputs.py::test_individual_cell_images` |
| C76 | `append_output` appends the new rows to an existing `out_all` | `test_outputs.py::test_append_output_adds_the_new_rows` |

### Nucleus and tracking

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C50 | The nucleus position is found exactly for small nuclei; `f.nucl` is the sum within 4 pixels (49 pixels, `a.nucl`) | `test_nucleus.py` |
| C51 | A nucleus larger than the search disc gives a plateau of equal sums; the first position in scan order (topmost) is kept, so `ypos.nucl` can be one pixel off | experiment |
| C52 | Cells moved a few pixels between time points keep their number | `test_tracking.py` |
| C54 | With a third image and `third_image nuclear_label`, the nucleus is placed where the third image is brightest, whatever the fluorescence image shows | `test_internal_structure.py::test_third_image_locates_the_nucleus` |
| C55 | `third_image vacuole_label` also locates the nucleus from the third image, the same way (see Q04) | `test_internal_structure.py::test_third_image_locates_the_nucleus` |
| C56 | With a nuclear label, `f.nucl.tag1` to `f.nucl.tag6` measure the third image around the nucleus (`f.nucl.tag1` within 2 pixels); `f.nucl` keeps measuring the fluorescence image | `test_internal_structure.py::test_tag_columns_measure_the_third_image` |
| C57 | `treat_brightfield_as_fluorescence_also` measures the bright field as one more channel, exactly as if given as a fluorescence image, once per time point and with its own flag | `test_internal_structure.py::test_bright_field_can_be_measured_as_a_channel`, `test_bright_field_channel_once_per_time_point` |
| C58 | The vacuole is the darkest contiguous region inside the cell. On noise-free images none is found, even with a dark region; with noise, one is always reported, also in cells without a vacuole (14–55 false pixels); a dark disc of 81 pixels is reported with 85–135 | `test_internal_structure.py` (three tests) |
| C53 | On the real time course, 87 of 97 cells keep their number through 3 time points | `test_real_data.py::test_most_cells_are_tracked_through_the_time_course` |

### Memory checks

| ID | Behaviour | Evidence |
| --- | --- | --- |
| C80 | The whole test suite runs without any AddressSanitizer or UndefinedBehaviorSanitizer report: the code paths it exercises have no detected memory errors (memory leaks are not checked) | `make sanitize` (CI job "Tests con sanitizers") |

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
| Q04 | What does `third_image vacuole_label` change, besides locating the nucleus from the third image (C55)? | The vacuole columns did not change in our experiments |

## Proposed improvements

Ordered from least to most impact on existing results. Any change that alters results needs
a new reference version, agreed with rcell2.

| ID | Proposal | Fixes | Changes results? |
| --- | --- | --- | --- |
| M01 | Correct the neighbour count | B01 | Yes, most contours slightly |
| M02 | Report unknown parameter names and a missing parameters file | B04, B05 | No |
| M03 | Give a new channel the next unused flag | B02 | Only where B02 occurs |
| M04 | Return the background value when it is uniform | B03 | Only on uniform backgrounds |
| M05 | Bounds checks or dynamic arrays for image lists and file names | B06, B07, B15 | No |
| M06 | Accept an image or a list in `-D`/`-F`, and fix the help | B06 | No |
| M07 | Turn the hard-coded constants into parameters, defaulting to the current values | C12 | No |
| M08 | Square in double, or use a more robust variance algorithm, in `calculate_cut()` | B08 | Possibly, slightly |
| M09 | Initialise the variables flagged by the compiler | B09 | Should not |
| M10 | Choose channels and flat images from explicit lists instead of file-name prefixes | C02, C03 | No |
| M11 | Read the TIFF DateTime month as 1–12 | B10 | Only time-mapped runs across a month end |
| M12 | Parse other DateTime formats (at least MetaSeries), or stop with a clear message | B11 | Only time-mapped runs with those images |
| M13 | Write the last interior pixel in the `-t` mask file | B12 | Only the mask file |
| M14 | Fix the help of `-l` (and `-D`/`-F`, B06) | B13 | No |
| M15 | Do not repeat the header when appending | B14 | Only appended files |
| M16 | Remove the code no function calls (about 400 lines: `gauss_fit`, `gauss_gradients`, `neighbor_interpolation`, `calculate_volume_cone_old`, `search_data_for_number`, `get_median_deviations`, `circularize_points`, and the never-called contour clean-ups of C23) | — | No |
| M17 | Report a vacuole only when it is significantly darker than the rest of the cell (and handle noise-free images) | C58 | Yes, vacuole columns |
| M18 | Use non-zero exit codes on every error path | B16 | No |
| M19 | Add the bud's vacuole area when recombining | B17 | Only recombined cells |
| M20 | Recompute the contour, perimeter, position and shape of merged cells, and drop (or flag explicitly) the merged buds | C91, C92 | Yes, recombined cells |
