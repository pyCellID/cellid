"""Pairing images by acquisition time (the default ``bf_fl_mapping``).

Without ``bf_fl_mapping list``, Cell-ID sorts the fluorescence images by
acquisition time, pairs each one with the closest bright-field image in time
and writes the elapsed seconds in the ``time`` column. Images from MetaMorph
carry the time in a private tag; other images are read from the standard TIFF
DateTime tag ("YYYY:MM:DD HH:MM:SS").
"""

import datetime as dt

import pytest

from cellid_testing import outputs, runner, synth

TIME_PARAMETERS = {k: v for k, v in runner.DEFAULT_PARAMETERS.items() if k != "bf_fl_mapping"}
D = dt.datetime


@pytest.fixture(scope="module")
def scene():
    cells, shape = synth.grid("circle", 2, 56, seed=41)
    return shape, synth.brightfield(shape, cells, seed=1)


def stamped(array, when):
    """An image with a standard TIFF DateTime tag."""
    return (array, {"datetime": when})


def with_datetime_text(array, text):
    """An image whose DateTime tag holds an arbitrary text."""
    return (array, {"extratags": [(306, "s", 0, text, True)]})


def run_two_time_points(run, scene, bf_times, fl_times, *, stamp=stamped, fl_order=(0, 1)):
    shape, bf = scene
    fl = synth.flat(shape, 1000)
    images = {
        "BF_t1.tif": stamp(bf, bf_times[0]),
        "BF_t2.tif": stamp(bf, bf_times[1]),
        "YFP_t1.tif": stamp(fl, fl_times[0]),
        "YFP_t2.tif": stamp((fl * 2).astype(fl.dtype), fl_times[1]),
    }
    fl_names = ["YFP_t1.tif", "YFP_t2.tif"]
    result = run(images, ["BF_t1.tif", "BF_t2.tif"], [fl_names[i] for i in fl_order],
                 parameters=TIME_PARAMETERS)
    assert result.returncode == 0, result.log
    return result, outputs.read_out_all(result.out_all)


def times(t1, t2, lag=5):
    """Bright-field times and fluorescence times taken ``lag`` seconds later."""
    return (t1, t2), (t1 + dt.timedelta(seconds=lag), t2 + dt.timedelta(seconds=lag))


def test_images_are_sorted_and_paired_by_time(run, scene):
    """Fluorescence images listed out of order are sorted by time and each one
    is paired with the closest bright-field image."""
    bf_times, fl_times = times(D(2026, 11, 27, 10, 0), D(2026, 11, 27, 10, 10))
    result, table = run_two_time_points(run, scene, bf_times, fl_times, fl_order=(1, 0))
    mapping = outputs.read_mapping(result.mapping)
    pairs = dict(zip(mapping["fluor"].str.strip(), mapping["bright"].str.strip()))
    assert pairs == {"YFP_t1.tif": "BF_t1.tif", "YFP_t2.tif": "BF_t2.tif"}
    # The second image (twice as bright) is the second time frame
    means = table.groupby("t.frame")["f.tot"].mean()
    assert means[1] == pytest.approx(2 * means[0])


@pytest.mark.parametrize(
    "t1, t2",
    [
        (D(2026, 11, 27, 10, 0), D(2026, 11, 27, 10, 10)),  # same day
        (D(2026, 11, 27, 23, 55), D(2026, 11, 28, 0, 5)),  # across midnight
        (D(2026, 11, 27, 10, 0), D(2026, 11, 27, 16, 0)),  # six hours
        (D(2026, 12, 31, 23, 55), D(2027, 1, 1, 0, 5)),  # across new year
    ],
    ids=["same-day", "midnight", "six-hours", "new-year"],
)
def test_time_column_is_the_elapsed_seconds(run, scene, t1, t2):
    bf_times, fl_times = times(t1, t2)
    _, table = run_two_time_points(run, scene, bf_times, fl_times)
    assert sorted(table["time"].unique()) == [0, (t2 - t1).total_seconds()]


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B10 (docs/behavior.md): the month of the TIFF DateTime is read one "
    "too high, so elapsed times are wrong across the end of a month",
)
@pytest.mark.parametrize(
    "t1, t2",
    [
        (D(2026, 11, 30, 23, 55), D(2026, 12, 1, 0, 5)),
        (D(2026, 2, 28, 23, 55), D(2026, 3, 1, 0, 5)),
    ],
    ids=["end-of-november", "end-of-february"],
)
def test_elapsed_time_across_the_end_of_a_month(run, scene, t1, t2):
    bf_times, fl_times = times(t1, t2)
    _, table = run_two_time_points(run, scene, bf_times, fl_times)
    assert sorted(table["time"].unique()) == [0, 600]


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B11 (docs/behavior.md): DateTime texts that are not "
    "'YYYY:MM:DD HH:MM:SS' (such as MetaSeries' '20191021 18:10:00.000') are read as "
    "garbage without any warning",
)
def test_non_standard_datetime_is_read_or_reported(run, scene):
    bf_times = ("20191021 18:10:00.000", "20191021 18:20:00.000")
    fl_times = ("20191021 18:10:05.000", "20191021 18:20:05.000")
    result, table = run_two_time_points(run, scene, bf_times, fl_times, stamp=with_datetime_text)
    assert sorted(table["time"].unique()) == [0, 600] or result.returncode != 0
