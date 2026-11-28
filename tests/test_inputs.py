"""How Cell-ID handles its inputs: image lists, parameters and channels."""

import pytest

from cellid_testing import outputs, runner, synth


def one_image():
    cells, shape = synth.grid("circle", 2, 56, seed=8)
    return synth.brightfield(shape, cells, seed=8), synth.flat(shape, 1000)


def misspelt_parameters():
    parameters = dict(runner.DEFAULT_PARAMETERS)
    parameters["background_reject_facor"] = parameters.pop("background_reject_factor")
    return parameters


def test_lists_of_different_length_are_rejected(run):
    bf, fl = one_image()
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif", "BF.tif"], ["FL.tif"])
    assert result.returncode == 3
    assert not result.out_all.exists()


def test_unknown_parameter_falls_back_to_the_default(run):
    """Current behaviour: a misspelt name is ignored and the default is used
    (background_reject_factor defaults to 3.0)."""
    bf, fl = one_image()
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"],
                 parameters=misspelt_parameters(), check_parameters=False)
    assert outputs.logged_parameter(result.log, "background_reject_factor") == 3.0


@pytest.mark.xfail(strict=True, reason="Known bug B04 (docs/behavior.md): unknown parameter names are silently ignored")
def test_unknown_parameter_is_reported(run):
    bf, fl = one_image()
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"],
                 parameters=misspelt_parameters(), check_parameters=False)
    assert result.returncode != 0


@pytest.mark.xfail(strict=True, reason="Known bug B05 (docs/behavior.md): a missing parameters file silently uses defaults")
def test_missing_parameters_file_is_reported(run):
    bf, fl = one_image()
    result = run({"BF.tif": bf, "FL.tif": fl}, ["BF.tif"], ["FL.tif"], write_parameters_file=False)
    assert result.returncode != 0


@pytest.mark.xfail(
    strict=True,
    reason="Known bug B02 (docs/behavior.md): a new channel listed after a repeated one "
    "gets the flag of another channel",
)
def test_each_channel_gets_its_own_flag(run):
    bf, fl = one_image()
    images = {"BF_t1.tif": bf, "BF_t2.tif": bf, "YFP_t1.tif": fl, "CFP_t1.tif": fl,
              "YFP_t2.tif": fl, "RFP_t2.tif": fl}
    result = run(images, ["BF_t1.tif", "BF_t1.tif", "BF_t2.tif", "BF_t2.tif"],
                 ["YFP_t1.tif", "CFP_t1.tif", "YFP_t2.tif", "RFP_t2.tif"])
    mapping = outputs.read_mapping(result.mapping)
    channel = mapping["fluor"].str[:3]
    flags_per_channel = mapping.groupby(channel)["flag"].unique()
    # Each channel has one flag, and no two channels share a flag
    assert all(len(flags) == 1 for flags in flags_per_channel)
    assert mapping.groupby("flag")["fluor"].apply(lambda f: f.str[:3].nunique()).max() == 1
