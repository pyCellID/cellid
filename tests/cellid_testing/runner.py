"""Run the Cell-ID executable on a set of images.

:func:`run_cellid` writes the images, the image lists and ``parameters.txt``
into a working directory, runs ``cell`` there and returns a :class:`Run` with
everything needed to inspect the result.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

import tifffile

#: Parameter names that Cell-ID recognises (from src/cell.c). Cell-ID silently
#: ignores unknown names, so the test helpers refuse them.
KNOWN_PARAMETERS = frozenset(
    {
        "align_fl_to_bf", "align_fl_to_first", "align_individual_cells",
        "align_individual_cells_boundary", "append_output", "background_reject_factor",
        "bf_fl_mapping", "do_recombination", "force_nucleus_in_center", "fret",
        "image_type", "max_dist_over_waist", "max_pixels_per_cell", "max_split_over_minor",
        "min_pixels_per_cell", "nucleus_radius_1", "nucleus_radius_2", "nucleus_radius_3",
        "nucleus_radius_4", "nucleus_radius_5", "nucleus_radius_6", "output_individual_cells",
        "paw_output", "recombination_all_new_cells", "recombination_fl_per_a_nucleus",
        "recombination_is_a_cell_fl_per_a", "third_image", "tracking_comparison",
        "treat_brightfield_as_fluorescence_also",
    }
)

#: Parameters used by default in the tests (those of tests/data/parameters.txt).
DEFAULT_PARAMETERS = {
    "max_split_over_minor": 0.5,
    "max_dist_over_waist": 8,
    "max_pixels_per_cell": 2000,
    "min_pixels_per_cell": 75,
    "background_reject_factor": 0.75,
    "tracking_comparison": 0.2,
    "image_type": "brightfield",
    "bf_fl_mapping": "list",
}


@dataclass
class Run:
    """Result of one Cell-ID run."""

    returncode: int
    workdir: Path
    log: str
    binary: Path

    @property
    def out_all(self) -> Path:
        return self.workdir / "out_all"

    @property
    def mapping(self) -> Path:
        return self.workdir / "out_bf_fl_mapping"

    @property
    def masks(self) -> Path:
        return self.workdir / "out_all_masks.tsv.gz"


def write_parameters(path: Path, parameters: dict, *, check: bool = True) -> None:
    """Write a Cell-ID parameters file, one ``name value`` per line.

    A value of ``True`` writes the name alone (a flag such as ``align_fl_to_bf``).
    With ``check=True`` unknown names raise ``ValueError``; tests that study what
    Cell-ID does with unknown names pass ``check=False``.
    """
    if check:
        unknown = sorted(set(parameters) - KNOWN_PARAMETERS)
        if unknown:
            raise ValueError(f"unknown Cell-ID parameters: {unknown}")
    lines = [name if value is True else f"{name} {value}" for name, value in parameters.items()]
    path.write_text("\n".join(lines) + "\n")


def run_cellid(
    binary: Path,
    workdir: Path,
    images: dict[str, "object"],
    bf: list[str],
    fl: list[str],
    *,
    parameters: dict | None = None,
    check_parameters: bool = True,
    write_parameters_file: bool = True,
    text_files: dict[str, str] | None = None,
    extra_args: tuple[str, ...] = (),
) -> Run:
    """Run Cell-ID in ``workdir``.

    Args:
        binary: path to the ``cell`` executable.
        workdir: directory for inputs and outputs (normally a pytest ``tmp_path``).
        images: file name -> 2-D array to write as a 16-bit TIFF, or a tuple
            ``(array, options)`` with keyword arguments for ``tifffile.imwrite``
            (for example ``{"datetime": ...}`` for the acquisition time).
        bf: bright-field file names, one per line of the list (repeat a name to
            use it for several fluorescence images).
        fl: fluorescence file names, same length as ``bf`` for list mapping.
        parameters: Cell-ID parameters; ``None`` uses :data:`DEFAULT_PARAMETERS`.
        check_parameters: refuse unknown parameter names.
        write_parameters_file: write ``parameters.txt``; ``False`` runs Cell-ID
            with a parameters file that does not exist.
        text_files: file name -> text, for extra inputs such as the dark and
            flat image lists (``-D``, ``-F``).
        extra_args: additional command-line options, e.g. ``("-t",)``.
    """
    workdir.mkdir(parents=True, exist_ok=True)
    for name, image in images.items():
        # An image is an array, or (array, tifffile.imwrite keyword arguments)
        # to write metadata such as the acquisition time.
        array, options = image if isinstance(image, tuple) else (image, {})
        tifffile.imwrite(workdir / name, array, **options)
    for name, text in (text_files or {}).items():
        (workdir / name).write_text(text)
    (workdir / "bf.txt").write_text("\n".join(bf) + "\n")
    (workdir / "fl.txt").write_text("\n".join(fl) + "\n")
    if write_parameters_file:
        params = DEFAULT_PARAMETERS if parameters is None else parameters
        write_parameters(workdir / "parameters.txt", params, check=check_parameters)

    cmd = [str(binary), "-p", "parameters.txt", "-b", "bf.txt", "-f", "fl.txt", "-o", "out",
           *extra_args]
    proc = subprocess.run(cmd, cwd=workdir, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=300)
    return Run(proc.returncode, workdir, proc.stdout + proc.stderr, Path(binary))
