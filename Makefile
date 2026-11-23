# Makefile de cellid
#
#   make                  build ./cell
#   make test             build and run the tests
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

test: cell
	./tests/test_smoke.sh
	./tests/test_golden.sh
	./tests/test_threshold.sh

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
	rm -rf tests/salida tests/salida_golden docs/build

.PHONY: test docs check-unchanged format-check clean ejercicio1 ejercicio2
