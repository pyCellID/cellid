# Makefile de cellid
#
#   make                  build ./cell
#   make test             build and run the tests (pytest)
#   make coverage         line coverage of src/ by the tests (build-cov/coverage.html)
#   make sanitize         the tests with AddressSanitizer and UBSan
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
	    --html-details build-cov/coverage.html --markdown build-cov/coverage.md \
	    --txt-summary --txt build-cov/coverage.txt
	@echo "Report: build-cov/coverage.html"

# The test suite with AddressSanitizer and UndefinedBehaviorSanitizer: a memory
# error or undefined behaviour stops Cell-ID and fails the test that ran it.
sanitize:
	mkdir -p build-asan
	$(CC) -O1 -g -fsanitize=address,undefined -fno-omit-frame-pointer -w \
	    -o build-asan/cell $(SRC) $(LDLIBS)
	CELLID_BIN=build-asan/cell ASAN_OPTIONS=detect_leaks=0 \
	    UBSAN_OPTIONS=halt_on_error=1:print_stacktrace=1 $(PYTHON) -m pytest -q

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
	rm -rf tests/salida tests/salida_golden docs/build build-cov build-asan .pytest_cache

.PHONY: test coverage sanitize docs check-unchanged format-check clean ejercicio1 ejercicio2
