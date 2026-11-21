# Contributing to cellid

## Principles

- **`src/` is the reference.** It is Cell-ID 1.5.0 as used by rcell2. Any change that alters
  results is a scientific decision: discuss it first, document it, and update the golden
  reference in the same pull request.
- **Documentation first, changes later.** Documenting `src/` must not change the compiled
  code. Check it with `make check-unchanged`.
- **Every change goes through a branch and a pull request**, with the CI green before merging.

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

`make test` runs:

| Test | What it checks |
| --- | --- |
| `tests/test_smoke.sh` | Cell-ID finds the 25 cells of the synthetic image |
| `tests/test_golden.sh` | `out_all` is byte-for-byte identical to `tests/data/expected/out_all` |
| `tests/test_threshold.sh` | The segmentation thresholds are computed in double precision |

If a change to `src/` is meant to change results, regenerate the reference with
`./tests/test_golden.sh --update` and explain why in the commit message.

The golden reference was generated with gcc 13 on x86-64 (Ubuntu 24.04), the same environment
as the CI. Other compilers or platforms may produce tiny floating-point differences.
