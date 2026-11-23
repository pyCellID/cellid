"""Shared fixtures for the Cell-ID test suite."""

from __future__ import annotations

import itertools
import os
import sys
from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
REPO_ROOT = TESTS_DIR.parent
sys.path.insert(0, str(TESTS_DIR))

from cellid_testing import runner, synth  # noqa: E402


def pytest_addoption(parser):
    parser.addoption(
        "--update-golden",
        action="store_true",
        help="rewrite the golden reference files instead of comparing against them",
    )


@pytest.fixture(scope="session")
def cell_binary() -> Path:
    """The ``cell`` executable: $CELLID_BIN, or ./cell at the repository root."""
    path = Path(os.environ.get("CELLID_BIN", REPO_ROOT / "cell")).resolve()
    if not path.exists():
        pytest.exit(f"Cell-ID executable not found at {path}: run `make` first", returncode=2)
    return path


@pytest.fixture(scope="session")
def data_dir() -> Path:
    return TESTS_DIR / "data"


@pytest.fixture
def run(cell_binary, tmp_path):
    """Run Cell-ID in a fresh subdirectory of ``tmp_path``.

    ``run(images, bf, fl, **kwargs)`` accepts the arguments of
    :func:`cellid_testing.runner.run_cellid` after ``binary`` and ``workdir``.
    Each call uses its own directory, so a test can run Cell-ID several times.
    """
    counter = itertools.count()

    def _run(images, bf, fl, **kwargs):
        workdir = tmp_path / f"run{next(counter)}"
        return runner.run_cellid(cell_binary, workdir, images, bf, fl, **kwargs)

    return _run


@pytest.fixture(scope="session")
def reference():
    """The stored reference images (25 circles) and their cells."""
    bf, fl, cells = synth.reference_images()
    return {"bf": bf, "fl": fl, "cells": cells}
