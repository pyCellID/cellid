"""Tracking of cells between time points."""

from cellid_testing import outputs, synth


def test_shifted_cells_keep_their_ids(run):
    cells, shape = synth.grid("circle", 3, 56, seed=7)
    moved = [synth.Cell(c.kind, c.cx + 3, c.cy + 2, c.size) for c in cells]
    fl = synth.flat(shape, 1000)
    images = {
        "BF_t1.tif": synth.brightfield(shape, cells, seed=1),
        "BF_t2.tif": synth.brightfield(shape, moved, seed=2),
        "FL_t1.tif": fl,
        "FL_t2.tif": fl,
    }
    result = run(images, ["BF_t1.tif", "BF_t2.tif"], ["FL_t1.tif", "FL_t2.tif"])
    assert result.returncode == 0, result.log
    table = outputs.read_out_all(result.out_all)
    first = table[table["t.frame"] == 0].set_index("cellID")
    second = table[table["t.frame"] == 1].set_index("cellID")
    assert sorted(first.index) == sorted(second.index)
    assert ((second["xpos"] - first["xpos"]) == 3).all()
    assert ((second["ypos"] - first["ypos"]) == 2).all()
