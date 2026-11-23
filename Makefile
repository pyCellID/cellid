# Makefile de cellid
#
#   make                  build ./cell
#   make test             build and run the tests (pytest)
#   make coverage         line coverage of src/ by the tests (build-cov/coverage.html)
#   make docs             build the HTML manual (docs/build/html/index.html)
#   make check-unchanged  check that src/ compiles to the same code as main
#   make format-check     check the formatting of new code (clang-format)
#   make clean            remove build outputs
#
CC      ?= gcc
CFLAGS  ?= -O2 -Wall -Wno-unused-variable -Wno-unused-but-set-variable
LDLIBS   = -ltiff -lz -lm
BASE    ?= origin/main

SRC  = $(wildcard src/*.c)
OBJ  = $(SRC:.c=.o)

cell: $(OBJ)
	$(CC) $(CFLAGS) -o $@ $(OBJ) $(LDLIBS)

src/%.o: src/%.c
	$(CC) $(CFLAGS) -c -o $@ $<

PYTHON ?= python3

test: cell
	$(PYTHON) -m pytest

# Line coverage of src/ by the test suite (needs gcovr: pip install --group coverage)
coverage:
	mkdir -p build-cov
	$(CC) -O0 -g --coverage -w -o build-cov/cell $(SRC) $(LDLIBS)
	find build-cov -name '*.gcda' -delete
	CELLID_BIN=build-cov/cell $(PYTHON) -m pytest -q
	gcovr --root . --filter src/ --object-directory build-cov \
	    --html-details build-cov/coverage.html --txt-summary --txt build-cov/coverage.txt
	@echo "Report: build-cov/coverage.html"

docs:
	mkdir -p docs/build
	doxygen Doxyfile
	@echo "Manual: docs/build/html/index.html"

check-unchanged:
	./tests/check_code_unchanged.sh $(BASE)

# New code only: src/ is the original Cell-ID code and keeps its own format
FORMAT_FILES = $(wildcard ejercicios/*/*.c ejercicios/*/*.h tests/*.c)
format-check:
	clang-format --dry-run --Werror $(FORMAT_FILES)

# C exercises (not part of the CI tests)
ejercicio1:
	$(CC) -Wall -Wextra -g -o ejercicios/01_vecinos/test_vecinos \
	    ejercicios/01_vecinos/test_vecinos.c ejercicios/01_vecinos/vecinos.c \
	    ejercicios/01_vecinos/original.c
	./ejercicios/01_vecinos/test_vecinos

ejercicio2:
	$(CC) -Wall -Wextra -g -o ejercicios/02_umbral/test_umbral \
	    ejercicios/02_umbral/test_umbral.c ejercicios/02_umbral/umbral.c \
	    ejercicios/02_umbral/original.c -lm
	./ejercicios/02_umbral/test_umbral

clean:
	rm -f cell src/*.o ejercicios/*/test_vecinos ejercicios/*/test_umbral
	rm -rf tests/salida tests/salida_golden docs/build build-cov .pytest_cache

.PHONY: test coverage docs check-unchanged format-check clean ejercicio1 ejercicio2
