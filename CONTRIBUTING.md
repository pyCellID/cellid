# Contributing to cellid

## Principles

- **`src/` is the reference.** It is Cell-ID 1.5.0 as used by rcell2. Any change that alters
  results is a scientific decision: discuss it first, document it, and update the golden
  reference in the same pull request.
- **Documentation first, changes later.** Documenting `src/` must not change the compiled
  code. Check it with `make check-unchanged`.
- **Every change goes through a branch and a pull request**, with the CI green before merging.
- **Every finding goes to `docs/behavior.md`**: bugs (`B`), characterized behaviour (`C`), open
  questions (`Q`) and proposed improvements (`M`), each with the evidence that supports it.
  Known-bug tests quote the identifier in their `xfail` reason.

## Language

Code, comments and documentation in `src/` and `tests/` are in English. The exercises
(`ejercicios/`) are learning material and are written in Spanish.

## Documentation (Doxygen)

Document functions with Doxygen comments (`/** ... */`). Public functions are documented in
their header (`.h`); `static` helpers in the `.c` file.

```c
/**
 * @brief One-line summary.
 *
 * Longer description, if needed.
 *
 * @param name  Meaning of the parameter.
 * @return      Meaning of the return value.
 * @bug         Known problem (it appears in the "Bug List" page of the manual).
 */
```

Build the manual with `make docs` and open `docs/build/html/index.html`.

## Code style (new code)

- C11 (`-std=c11`), compiled with `-Wall -Wextra` and no warnings.
- Formatting with `clang-format` (`.clang-format` at the root); check with `make format-check`.
  `src/` is excluded: the original code keeps its format so that its history stays readable.
- Initialise every variable when it is declared.
- Use `const` for anything a function does not modify, and `static` for internal helpers.
- No global variables in new code: everything a function needs comes in as a parameter.
- Always use braces, even for one-line `if`, `for` and `while` bodies.
- No magic numbers: give constants a name (`#define` or `static const`).
- Check everything that can fail: return values of `malloc` and `fopen`, array bounds.
- Return statements: under discussion. Single exit is preferred in functions that acquire
  resources (memory, files); see the discussion in the project notes.

## Tests

The test suite runs the `cell` executable from the outside, with pytest. Install its
dependencies once (`pip install --group test`, pip >= 25.1), then run `make test`.

### Layout

| Path | Contents |
| --- | --- |
| `tests/cellid_testing/synth.py` | Synthetic images with known ground truth (cells, bright field, fluorescence) |
| `tests/cellid_testing/runner.py` | Writes images, lists and parameters, runs `cell`, returns a `Run` |
| `tests/cellid_testing/outputs.py` | Readers for `out_all`, `out_bf_fl_mapping`, masks and the log |
| `tests/cellid_testing/compare.py` | Table comparison with a numeric tolerance |
| `tests/cellid_testing/matching.py` | Pairs found cells with synthetic cells |
| `tests/conftest.py` | Fixtures: the `cell` binary (`$CELLID_BIN` or `./cell`) and `run` |
| `tests/test_*.py` | The tests, one file per topic |
| `tests/data/` | Stored reference images and the golden `out_all` |

Every run happens in a temporary directory: tests never write into `tests/data`.

### Kinds of tests

- **Ground truth**: synthetic images where the right answer is known (number of cells,
  areas, exact fluorescence on flat images, tracking of shifted cells).
- **Characterization**: document current behaviour that is surprising but not decided to
  be wrong (for example, regions under 75 pixels are never found). Their docstring says why.
- **Known bugs**: `@pytest.mark.xfail(strict=True, reason="Known bug: ...")`. They assert
  the *correct* behaviour, so they fail today. `strict=True` makes them fail loudly if
  they start passing: when a bug is fixed, remove the mark.
- **Regression (golden)**: `out_all` on the stored images must match
  `tests/data/expected/out_all`, numbers within a relative tolerance of 1e-5 (the same
  binary can print a different last digit on different CPUs). If a change to `src/` is
  meant to change results, run `python -m pytest --update-golden` and explain why in the
  commit message.

### Coverage

`make coverage` builds an instrumented `cell` in `build-cov/`, runs the suite and writes
`build-cov/coverage.html` (needs `pip install --group coverage`). The CI publishes the
report as an artifact.

### Memory checks

`make sanitize` builds `cell` with AddressSanitizer and UndefinedBehaviorSanitizer in
`build-asan/` and runs the suite with it: a memory error or undefined behaviour stops
Cell-ID, and the test that ran it fails. Tests that expect a crash today check
`result.crashed`, which also recognises sanitizer reports. The CI runs it in its own job.

### Writing a new test

1. Build the input with `synth` (or load an image from `tests/data`).
2. Run it with the `run` fixture: `result = run(images, bf_list, fl_list)`.
3. Read the outputs with `outputs` and assert one property per test.
4. Name the test after the behaviour it checks: `test_cells_touching_the_image_edge_are_discarded`.
