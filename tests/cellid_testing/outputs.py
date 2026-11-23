"""Read Cell-ID output files."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd


def read_out_all(path: Path) -> pd.DataFrame:
    """Read ``out_all`` (tab-separated), with column names stripped of padding."""
    df = pd.read_csv(path, sep="\t")
    df.columns = df.columns.str.strip()
    return df


def read_mapping(path: Path) -> pd.DataFrame:
    """Read ``out_bf_fl_mapping``: which image got which channel number (flag)."""
    df = pd.read_csv(path, sep="\t")
    df.columns = df.columns.str.strip()
    return df


def read_masks(path: Path) -> pd.DataFrame:
    """Read the boundary and interior pixels written with the ``-t`` option."""
    df = pd.read_csv(path, sep="\t")
    df.columns = df.columns.str.strip()
    df["pixtype"] = df["pixtype"].str.strip()
    return df


def threshold_stats(log: str) -> tuple[float, float]:
    """Mean and standard deviation that ``calculate_cut()`` printed in the log."""
    match = re.search(r"In Pixel units: mu=([-+0-9.eE]+), sig=([-+0-9.eE]+?)\.?\s", log)
    if match is None:
        raise ValueError("threshold statistics not found in the Cell-ID log")
    return float(match.group(1)), float(match.group(2))


def logged_parameter(log: str, name: str) -> float:
    """Value of a parameter as Cell-ID reports it under ``Using parameters:``."""
    match = re.search(rf"\b{re.escape(name)}=([-+0-9.eE]+)", log)
    if match is None:
        raise ValueError(f"parameter {name!r} not found in the Cell-ID log")
    return float(match.group(1))
